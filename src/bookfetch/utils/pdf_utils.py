"""PDF manipulation utilities."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import img2pdf

from bookfetch.utils.exceptions import ConversionError
from bookfetch.utils.logger import get_logger

logger = get_logger(__name__)


def create_pdf_from_images(
    image_paths: list[Path],
    output_path: Path,
    metadata: Optional[dict] = None,
    book_id: Optional[str] = None,
) -> Path:
    """Create PDF from list of image files with metadata.

    Args:
        image_paths: List of image file paths
        output_path: Output PDF path
        metadata: Optional metadata dictionary from Archive.org
        book_id: Optional book ID for adding to keywords

    Returns:
        Path to created PDF file

    Raises:
        ConversionError: If PDF creation fails
    """
    try:
        # Prepare PDF metadata
        pdfmeta = {}

        if metadata:
            # Ensure metadata values are strings
            for key in ["title", "creator", "associated-names"]:
                if key in metadata:
                    if isinstance(metadata[key], str):
                        pass
                    elif isinstance(metadata[key], list):
                        metadata[key] = "; ".join(metadata[key])
                    else:
                        logger.warning(f"Unsupported metadata type for {key}: {type(metadata[key])}")

            # Title
            if "title" in metadata:
                pdfmeta["title"] = metadata["title"]

            # Author
            if "creator" in metadata and "associated-names" in metadata:
                pdfmeta["author"] = metadata["creator"] + "; " + metadata["associated-names"]
            elif "creator" in metadata:
                pdfmeta["author"] = metadata["creator"]
            elif "associated-names" in metadata:
                pdfmeta["author"] = metadata["associated-names"]

            # Date
            if "date" in metadata:
                try:
                    date_str = metadata["date"][:4] if isinstance(metadata["date"], str) else str(metadata["date"])[:4]
                    pdfmeta["creationdate"] = datetime.strptime(date_str, "%Y")
                except Exception as e:
                    logger.debug(f"Could not parse date from metadata: {e}")

        # Keywords (add Archive.org URL)
        if book_id:
            pdfmeta["keywords"] = [f"https://archive.org/details/{book_id}"]

        # Convert images to PDF
        logger.info(f"Creating PDF with {len(image_paths)} images...")

        # Convert Path objects to strings
        image_paths_str = [str(p) for p in image_paths]

        pdf_data = img2pdf.convert(image_paths_str, **pdfmeta)

        # Write PDF file
        with open(output_path, "wb") as f:
            f.write(pdf_data)

        logger.info(f"PDF created successfully: {output_path}")
        return output_path

    except Exception as e:
        raise ConversionError(f"Failed to create PDF: {e}") from e


def get_unique_output_path(base_path: Path, directory: Optional[Path] = None) -> Path:
    """Get unique output path by adding numbers if file exists.

    Args:
        base_path: Base file path
        directory: Optional output directory

    Returns:
        Unique file path

    Example:
        If book.pdf exists, returns book(1).pdf
    """
    if directory:
        output_path = directory / base_path.name
    else:
        output_path = base_path

    if not output_path.exists():
        return output_path

    # File exists, add number suffix
    stem = output_path.stem
    suffix = output_path.suffix
    parent = output_path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem}({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def cleanup_temp_directory(directory: Path) -> None:
    """Remove temporary directory and all its contents.

    Args:
        directory: Directory to remove
    """
    try:
        if directory.exists() and directory.is_dir():
            shutil.rmtree(directory)
            logger.debug(f"Cleaned up temporary directory: {directory}")
    except Exception as e:
        logger.warning(f"Failed to cleanup directory {directory}: {e}")
