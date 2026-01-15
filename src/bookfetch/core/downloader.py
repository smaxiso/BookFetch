"""Main downloader module for Archive.org books."""

import json
import time
from concurrent import futures
from pathlib import Path
from typing import Optional

import requests
from internetarchive import get_item
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
            url: Archive.org book URL or book ID

        Returns:
            Book object with metadata and image links

        Raises:
            DownloadError: If book info cannot be retrieved
        """
        # Convert book ID to full URL if needed
        if not url.startswith("http"):
            url = f"https://archive.org/details/{url}"

        logger.info(f"Fetching book information from: {url}")

        try:
            # Get page content
            response = self.session.get(url)
            response.raise_for_status()
            page_content = response.text

            # Extract info URL from page
            # This is brittle and might fail for non-standard books
            try:
                info_url = "https:" + page_content.split('"url":"')[1].split('"')[0].replace(
                    "\\u0026", "&"
                )

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
                    logger.warning("No image links found in BookReader data, checking fallback.")
                else:
                    # Extract book ID from URL
                    book_id = list(filter(None, url.split("/")))[3]

                    logger.info(f"Found {len(links)} pages for book: {title}")

                    # Check for restricted status
                    is_restricted = False
                    restricted_flag = metadata.get("access-restricted-item")
                    if restricted_flag and str(restricted_flag).lower() == "true":
                        is_restricted = True

                    # Check collections
                    if not is_restricted:
                        collections = metadata.get("collection", [])
                        if isinstance(collections, str):
                            collections = [collections]
                        if any(
                            c in ["inlibrary", "lendinglibrary", "printdisabled"]
                            for c in collections
                        ):
                            is_restricted = True

                    return Book(
                        url=url,
                        book_id=book_id,
                        title=title,
                        pages=len(links),
                        image_links=links,
                        metadata=metadata,
                        is_restricted=is_restricted,
                    )
            except (IndexError, KeyError, ValueError, requests.RequestException) as scrape_err:
                logger.warning(
                    f"BookReader scraping failed: {scrape_err}. Trying metadata fallback."
                )

            # --- FALLBACK: Use internetarchive library ---
            # Extract ID from URL
            parts = list(filter(None, url.split("/")))
            # url usually https://archive.org/details/ID
            if "details" in parts:
                idx = parts.index("details")
                if idx + 1 < len(parts):
                    book_id = parts[idx + 1]
                else:
                    raise DownloadError(f"Could not parse Book ID from {url}")
            else:
                # Assume last part is ID
                book_id = parts[-1]

            item = get_item(book_id)
            title = sanitize_filename(item.metadata.get("title", book_id))
            is_restricted = False  # Default check

            # Check for direct PDF
            pdf_file = None
            largest_pdf_size = 0

            for file in item.files:
                # internetarchive files are dicts
                fmt = file.get("format", "")
                name = file.get("name", "")

                if fmt == "Text PDF" or name.lower().endswith(".pdf"):
                    # Find the largest PDF (likely the book)
                    if "size" in file:
                        f_size = int(file["size"])
                        if f_size > largest_pdf_size:
                            pdf_file = file
                            largest_pdf_size = f_size
                    elif not pdf_file:
                        pdf_file = file

            if pdf_file:
                fname = pdf_file.get("name")
                logger.info(f"Found direct PDF download: {fname}")
                direct_url = f"https://archive.org/download/{book_id}/{fname}"

                return Book(
                    url=url,
                    book_id=book_id,
                    title=title,
                    pages=0,  # Unknown
                    image_links=[],
                    metadata=item.metadata,
                    is_restricted=False,  # If there is a PDF, it's usually free
                    direct_url=direct_url,
                )
            else:
                # If no PDF and scraping failed, assume it relies on Loan (maybe?)
                # or is just incompatible.
                raise DownloadError("Could not find readable book content (No BookReader or PDF).")

        except Exception as e:
            # Clean up error message
            msg = str(e)
            if "list index out of range" in msg:
                msg = "Book not supported (Not a standard book format)"
            logger.error(f"Download init failed: {e}")
            raise DownloadError(f"Failed to fetch book info: {msg}") from e

    def download_book(self, book: Book, on_progress=None) -> Path:
        """Download a complete book.

        Args:
            book: Book object to download
            on_progress: Optional callback function(progress_0_to_1, status_text)

        Returns:
            Path to downloaded file (PDF or directory of images)

        Raises:
            DownloadError: If download fails
        """
        if book.direct_url:
            logger.info(f"Performing Direct PDF Download from: {book.direct_url}")
            try:
                # Direct file download
                pdf_filename = f"{book.safe_title}.pdf"
                pdf_path = get_unique_output_path(
                    Path(pdf_filename), directory=self.config.output_dir
                )

                response = self.session.get(book.direct_url, stream=True)
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))

                with (
                    open(pdf_path, "wb") as f,
                    tqdm(
                        desc="Downloading PDF",
                        total=total_size,
                        unit="iB",
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as bar,
                ):
                    downloaded = 0
                    for data in response.iter_content(chunk_size=1024):
                        size = f.write(data)
                        bar.update(size)
                        downloaded += size
                        if on_progress and total_size > 0:
                            # Update UI callback
                            try:
                                on_progress(
                                    downloaded / total_size,
                                    f"Downloading PDF: {int(downloaded / 1024 / 1024)}MB / {int(total_size / 1024 / 1024)}MB",
                                )
                            except Exception:
                                pass

                logger.info(f"Direct download complete: {pdf_path}")
                return pdf_path
            except Exception as e:
                logger.error(f"Direct download failed: {e}")
                raise DownloadError(f"Failed to download PDF directly: {e}") from e

        logger.info(f"Starting download of: {book.title}")

        # Ensure book is borrowed and get token
        _, token = self.loan_manager.borrow_book(book.book_id, verbose=self.config.verbose)

        # Create temporary directory for images
        temp_dir = self.config.output_dir / book.safe_title
        temp_dir = Path(get_unique_output_path(temp_dir))
        temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading images to: {temp_dir}")

        try:
            # Download all images
            images = self._download_images(book, temp_dir, token, on_progress)

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
            raise DownloadError(f"Failed to download book: {e}") from e
        finally:
            # Return the book
            try:
                self.loan_manager.return_book(book.book_id)
            except Exception as e:
                logger.warning(f"Failed to return book: {e}")

    def _download_images(
        self, book: Book, directory: Path, token: Optional[str] = None, on_progress=None
    ) -> list[Path]:
        """Download all images for a book using multi-threading.

        Args:
            book: Book object
            directory: Directory to save images
            token: Optional loan token for restricted books
            on_progress: Optional callback

        Returns:
            List of downloaded image paths
        """
        logger.info(f"Downloading {book.pages} pages with {self.config.threads} threads...")

        # Prepare image URLs with scale parameter
        image_urls = []
        for link in book.image_links:
            url = f"{link}&rotate=0&scale={self.config.resolution}"
            if token:
                url += f"&token={token}"
            image_urls.append(url)

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
            completed = 0
            total = len(tasks)

            for _task in tqdm(futures.as_completed(tasks), total=total, desc="Downloading"):
                completed += 1
                if on_progress:
                    try:
                        progress = completed / total
                        on_progress(progress, f"Downloading page {completed}/{total}")
                    except Exception:
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
                    # We discard the new token here as we can't easily update the current URL
                    # In a perfect world we would recursively call _download_single_image with new token
                    self.loan_manager.borrow_book(book_id, verbose=False)
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue
                elif response.status_code == 200:
                    # Success, save image
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    return image_path
                else:
                    logger.warning(
                        f"Unexpected status code {response.status_code} for page {page_num}"
                    )
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
