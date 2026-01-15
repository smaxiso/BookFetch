"""Unit tests for PDF utilities."""

from unittest.mock import MagicMock, patch

import pytest
from PIL import UnidentifiedImageError

from bookfetch.utils.exceptions import ConversionError
from bookfetch.utils.pdf_utils import create_pdf_from_images


class TestPDFUtils:
    """Test PDF utility functions."""

    @pytest.fixture
    def mock_img2pdf(self):
        """Mock img2pdf.convert."""
        with patch("bookfetch.utils.pdf_utils.img2pdf") as mock:
            yield mock

    @pytest.fixture
    def mock_pil_image(self):
        """Mock PIL.Image."""
        with patch("bookfetch.utils.pdf_utils.Image") as mock:
            yield mock

    def test_create_pdf_success(self, tmp_path, mock_img2pdf, mock_pil_image):
        """Test successful PDF creation."""
        # Setup valid image
        img_path = tmp_path / "1.jpg"
        img_path.touch()

        mock_img = MagicMock()
        mock_pil_image.open.return_value.__enter__.return_value = mock_img

        mock_img2pdf.convert.return_value = b"PDF_DATA"

        output_path = tmp_path / "output.pdf"

        result = create_pdf_from_images([img_path], output_path)

        assert result == output_path
        assert output_path.read_bytes() == b"PDF_DATA"
        mock_img.verify.assert_called_once()

    def test_create_pdf_skips_invalid_image(self, tmp_path, mock_img2pdf, mock_pil_image):
        """Test that invalid images are skipped."""
        # Setup one valid and one invalid image
        valid_path = tmp_path / "valid.jpg"
        valid_path.touch()

        invalid_path = tmp_path / "invalid.jpg"
        invalid_path.touch()

        output_path = tmp_path / "output.pdf"

        # Configure mock to raise error for invalid image
        mock_valid_img = MagicMock()

        def mock_open(path):
            if path == invalid_path:
                raise UnidentifiedImageError("Corrupt")
            cm = MagicMock()
            cm.__enter__.return_value = mock_valid_img
            return cm

        mock_pil_image.open.side_effect = mock_open
        mock_img2pdf.convert.return_value = b"PDF_DATA"

        create_pdf_from_images([valid_path, invalid_path], output_path)

        # Verify img2pdf was called with ONLY the valid image
        args, _ = mock_img2pdf.convert.call_args
        assert len(args[0]) == 1
        assert args[0][0] == str(valid_path)

    def test_create_pdf_fails_if_all_invalid(self, tmp_path, mock_pil_image):
        """Test failure when all images are invalid."""
        img_path = tmp_path / "bad.jpg"
        img_path.touch()

        mock_pil_image.open.side_effect = UnidentifiedImageError("Corrupt")

        with pytest.raises(ConversionError, match="No valid images found"):
            create_pdf_from_images([img_path], tmp_path / "out.pdf")

    def test_create_pdf_conversion_error(self, tmp_path, mock_img2pdf, mock_pil_image):
        """Test handling of img2pdf conversion errors."""
        img_path = tmp_path / "1.jpg"
        img_path.touch()

        mock_pil_image.open.return_value.__enter__.return_value = MagicMock()
        mock_img2pdf.convert.side_effect = Exception("Conversion Failed")

        with pytest.raises(ConversionError, match="img2pdf conversion failed"):
            create_pdf_from_images([img_path], tmp_path / "out.pdf")
