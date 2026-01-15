"""Main downloader module for Archive.org books."""

import json
import time
from concurrent import futures
from pathlib import Path

import requests
from tqdm import tqdm

from bookfetch.config.constants import DEFAULT_HEADERS, MAX_RETRIES, RETRY_DELAY_SECONDS
from bookfetch.core.loan_manager import LoanManager
from bookfetch.core.models import Book, DownloadConfig, OutputFormat
from bookfetch.utils.exceptions import DownloadError
from bookfetch.utils.image_utils import generate_image_filename, get_image_files
from bookfetch.utils.logger import get_logger
from bookfetch.utils.pdf_utils import (
    cleanup_temp_directory,
    create_pdf_from_images,
    get_unique_output_path,
)
from bookfetch.utils.validators import sanitize_filename

logger = get_logger(__name__)


class ArchiveDownloader:
    """Handles downloading books from Archive.org."""

    def __init__(self, session: requests.Session, config: DownloadConfig) -> None:
        """Initialize downloader.

        Args:
            session: Authenticated requests session
            config: Download configuration
        """
        self.session = session
        self.config = config
        self.loan_manager = LoanManager(session)

    def get_book_info(self, url: str) -> Book:
        """Extract book information from Archive.org URL.

        Args:
            url: Archive.org book URL

        Returns:
            Book object with metadata and image links

        Raises:
            DownloadError: If book info cannot be retrieved
        """
        logger.info(f"Fetching book information from: {url}")

        try:
            # Get page content
            response = self.session.get(url)
            response.raise_for_status()
            page_content = response.text

            # Extract info URL from page
            info_url = "https:" + page_content.split('"url":"')[1].split('"')[0].replace("\\u0026", "&")

            # Get book data
            response = self.session.get(info_url)
            response.raise_for_status()
            data = response.json()["data"]

            # Extract metadata
            metadata = data.get("metadata", {})
            br_options = data.get("brOptions", {})

            # Get title and sanitize
            title = br_options.get("bookTitle", "unknown").strip()
            title = sanitize_filename(title)

            # Extract image links
            links = []
            for item in br_options.get("data", []):
                for page in item:
                    if "uri" in page:
                        links.append(page["uri"])

            if not links:
                raise DownloadError("No image links found in book data")

            # Extract book ID from URL
            book_id = list(filter(None, url.split("/")))[3]

            logger.info(f"Found {len(links)} pages for book: {title}")

            return Book(
                url=url,
                book_id=book_id,
                title=title,
                pages=len(links),
                image_links=links,
                metadata=metadata,
            )

        except (IndexError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse book info: {e}")
            raise DownloadError(f"Failed to extract book information: {e}")
        except requests.RequestException as e:
            logger.error(f"Network error while fetching book info: {e}")
            raise DownloadError(f"Failed to fetch book information: {e}")

    def download_book(self, book: Book) -> Path:
        """Download a complete book.

        Args:
            book: Book object to download

        Returns:
            Path to downloaded file (PDF or directory of images)

        Raises:
            DownloadError: If download fails
        """
        logger.info(f"Starting download of: {book.title}")

        # Ensure book is borrowed
        self.loan_manager.borrow_book(book.book_id, verbose=self.config.verbose)

        # Create temporary directory for images
        temp_dir = self.config.output_dir / book.safe_title
        temp_dir = Path(get_unique_output_path(temp_dir))
        temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading images to: {temp_dir}")

        try:
            # Download all images
            images = self._download_images(book, temp_dir)

            # Save metadata if requested
            if self.config.save_metadata:
                self._save_metadata(book, temp_dir)

            # Create PDF or leave as JPG
            if self.config.output_format == OutputFormat.PDF:
                logger.info("Converting images to PDF...")

                pdf_filename = f"{book.safe_title}.pdf"
                pdf_path = get_unique_output_path(
                    Path(pdf_filename), directory=self.config.output_dir
                )

                create_pdf_from_images(
                    image_paths=images,
                    output_path=pdf_path,
                    metadata=book.metadata,
                    book_id=book.book_id,
                )

                # Cleanup temporary images
                cleanup_temp_directory(temp_dir)

                logger.info(f"Download complete: {pdf_path}")
                return pdf_path
            else:
                logger.info(f"Download complete: {temp_dir}")
                return temp_dir

        except Exception as e:
            logger.error(f"Download failed: {e}")
            # Cleanup on failure
            cleanup_temp_directory(temp_dir)
            raise DownloadError(f"Failed to download book: {e}")
        finally:
            # Return the book
            try:
                self.loan_manager.return_book(book.book_id)
            except Exception as e:
                logger.warning(f"Failed to return book: {e}")

    def _download_images(self, book: Book, directory: Path) -> list[Path]:
        """Download all images for a book using multi-threading.

        Args:
            book: Book object
            directory: Directory to save images

        Returns:
            List of downloaded image paths
        """
        logger.info(f"Downloading {book.pages} pages with {self.config.threads} threads...")

        # Prepare image URLs with scale parameter
        image_urls = [
            f"{link}&rotate=0&scale={self.config.resolution}" for link in book.image_links
        ]

        # Download images in parallel
        tasks = []
        with futures.ThreadPoolExecutor(max_workers=self.config.threads) as executor:
            for idx, url in enumerate(image_urls):
                task = executor.submit(
                    self._download_single_image,
                    url=url,
                    page_num=idx,
                    total_pages=book.pages,
                    directory=directory,
                    book_id=book.book_id,
                )
                tasks.append(task)

            # Wait for all downloads with progress bar
            for task in tqdm(futures.as_completed(tasks), total=len(tasks), desc="Downloading"):
                pass

        # Get list of downloaded images
        images = get_image_files(directory, book.pages)

        logger.info(f"Successfully downloaded {len(images)} images")
        return images

    def _download_single_image(
        self, url: str, page_num: int, total_pages: int, directory: Path, book_id: str
    ) -> Path:
        """Download a single image with retry logic.

        Args:
            url: Image URL
            page_num: Page number (0-indexed)
            total_pages: Total number of pages
            directory: Output directory
            book_id: Book identifier for re-borrowing if needed

        Returns:
            Path to downloaded image

        Raises:
            DownloadError: If download fails after retries
        """
        image_path = generate_image_filename(page_num, total_pages, directory)

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, headers=DEFAULT_HEADERS)

                if response.status_code == 403:
                    # Token expired, re-borrow the book
                    logger.debug(f"Token expired, re-borrowing book: {book_id}")
                    self.loan_manager.borrow_book(book_id, verbose=False)
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue
                elif response.status_code == 200:
                    # Success, save image
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    return image_path
                else:
                    logger.warning(f"Unexpected status code {response.status_code} for page {page_num}")
                    time.sleep(RETRY_DELAY_SECONDS)

            except requests.RequestException as e:
                logger.warning(f"Download attempt {attempt + 1} failed for page {page_num}: {e}")
                time.sleep(RETRY_DELAY_SECONDS)

        raise DownloadError(f"Failed to download page {page_num} after {MAX_RETRIES} attempts")

    def _save_metadata(self, book: Book, directory: Path) -> None:
        """Save book metadata to JSON file.

        Args:
            book: Book object
            directory: Output directory
        """
        metadata_path = directory / "metadata.json"

        try:
            with open(metadata_path, "w") as f:
                json.dump(book.metadata, f, indent=2)
            logger.info(f"Metadata saved to: {metadata_path}")
        except Exception as e:
            logger.warning(f"Failed to save metadata: {e}")
