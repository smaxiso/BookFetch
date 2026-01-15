"""Format conversion utilities."""

import warnings
from pathlib import Path
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from ebooklib import epub
from fpdf import FPDF

from bookfetch.utils.exceptions import ConversionError
from bookfetch.utils.logger import get_logger

# Suppress warnings from ebooklib
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

logger = get_logger(__name__)


class PDF(FPDF):
    """Custom PDF class for EPUB conversion."""

    def header(self) -> None:
        """Add header to each page."""
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "EPUB to PDF Conversion", 0, 1, "C")

    def chapter_title(self, title: str) -> None:
        """Add chapter title.

        Args:
            title: Chapter title
        """
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(4)

    def chapter_body(self, body: str) -> None:
        """Add chapter body text.

        Args:
            body: Chapter text content
        """
        self.set_font("Arial", "", 12)
        # Encode to latin-1 and replace unsupported characters
        safe_body = body.encode("latin-1", "replace").decode("latin-1")
        self.multi_cell(0, 10, safe_body)
        self.ln()


class EPUBConverter:
    """Converter for EPUB to PDF format."""

    def __init__(self) -> None:
        """Initialize EPUB converter."""
        pass

    def convert(self, epub_path: Path, pdf_path: Optional[Path] = None) -> Path:
        """Convert EPUB file to PDF.

        Args:
            epub_path: Path to EPUB file
            pdf_path: Optional output PDF path (defaults to same name as EPUB)

        Returns:
            Path to created PDF file

        Raises:
            ConversionError: If conversion fails
        """
        if not epub_path.exists():
            raise ConversionError(f"EPUB file not found: {epub_path}")

        if not epub_path.suffix.lower() == ".epub":
            raise ConversionError(f"File is not an EPUB: {epub_path}")

        # Default output path
        if pdf_path is None:
            pdf_path = epub_path.with_suffix(".pdf")

        logger.info(f"Converting {epub_path} to {pdf_path}")

        try:
            # Read EPUB file
            book = epub.read_epub(str(epub_path))

            # Create PDF
            pdf = PDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Extract text from EPUB and add to PDF
            for item in book.get_items():
                if item.media_type == "application/xhtml+xml":
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    text = soup.get_text()
                    pdf.chapter_body(text)

            # Save PDF
            pdf.output(str(pdf_path))

            logger.info(f"Successfully converted to: {pdf_path}")
            return pdf_path

        except FileNotFoundError:
            raise ConversionError(f"EPUB file not found: {epub_path}")
        except PermissionError:
            raise ConversionError("Permission denied when accessing files")
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise ConversionError(f"Failed to convert EPUB to PDF: {e}")


class ImageToPDFConverter:
    """Converter for images to PDF format."""

    def __init__(self) -> None:
        """Initialize image to PDF converter."""
        from bookfetch.utils.pdf_utils import create_pdf_from_images

        self._create_pdf = create_pdf_from_images

    def convert(
        self, image_paths: List[Path], output_path: Path, metadata: Optional[Dict] = None
    ) -> Path:
        """Convert images to PDF.

        Args:
            image_paths: List of image file paths
            output_path: Output PDF path
            metadata: Optional metadata dictionary

        Returns:
            Path to created PDF file

        Raises:
            ConversionError: If conversion fails
        """
        return self._create_pdf(image_paths, output_path, metadata)

