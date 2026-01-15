"""Unit tests for ArchiveDownloader."""

import pytest
from unittest.mock import Mock, patch
import requests
from bookfetch.core.downloader import ArchiveDownloader
from bookfetch.core.models import Book, OutputFormat
from bookfetch.utils.exceptions import DownloadError


class TestArchiveDownloader:
    """Test cases for ArchiveDownloader."""

    @pytest.fixture
    def mock_downloader(self, mock_session, sample_download_config):
        """Create downloader with mocked dependencies."""
        return ArchiveDownloader(mock_session, sample_download_config)

    def test_init(self, mock_session, sample_download_config):
        """Test downloader initialization."""
        downloader = ArchiveDownloader(mock_session, sample_download_config)
        assert downloader.session == mock_session
        assert downloader.config == sample_download_config
        assert downloader.loan_manager is not None

    def test_get_book_info_success(self, mock_downloader, sample_book_url):
        """Test successful book info extraction."""
        # Mock page response
        page_html = '"url":"//archive.org/download/samplebook123/__ia_metadata.json"'
        mock_page_response = Mock()
        mock_page_response.text = page_html
        mock_page_response.status_code = 200

        # Mock metadata response
        mock_metadata = {
            "data": {
                "metadata": {
                    "title": "Sample Book",
                    "creator": "John Doe",
                },
                "brOptions": {
                    "bookTitle": "Sample Book",
                    "data": [
                        [
                            {"uri": "https://example.com/page1.jpg"},
                            {"uri": "https://example.com/page2.jpg"},
                            {"uri": "https://example.com/page3.jpg"},
                        ]
                    ],
                },
            }
        }
        mock_json_response = Mock()
        mock_json_response.json.return_value = mock_metadata
        mock_json_response.status_code = 200

        # Setup mock session
        mock_downloader.session.get.side_effect = [
            mock_page_response,
            mock_json_response,
        ]

        book = mock_downloader.get_book_info(sample_book_url)

        assert isinstance(book, Book)
        assert book.title == "Sample_Book"  # Title is sanitized (spaces -> underscores)
        assert book.pages == 3
        assert len(book.image_links) == 3
        assert book.book_id == "samplebook123"

    def test_get_book_info_no_images(self, mock_downloader, sample_book_url):
        """Test book info extraction with no images."""
        page_html = '"url":"//archive.org/download/samplebook123/__ia_metadata.json"'
        mock_page_response = Mock()
        mock_page_response.text = page_html
        mock_page_response.status_code = 200

        mock_metadata = {
            "data": {
                "metadata": {},
                "brOptions": {"bookTitle": "Empty Book", "data": []},
            }
        }
        mock_json_response = Mock()
        mock_json_response.json.return_value = mock_metadata
        mock_json_response.status_code = 200

        mock_downloader.session.get.side_effect = [
            mock_page_response,
            mock_json_response,
        ]

        with pytest.raises(DownloadError) as exc_info:
            mock_downloader.get_book_info(sample_book_url)

        assert "No image links found" in str(exc_info.value)

    def test_get_book_info_network_error(self, mock_downloader, sample_book_url):
        """Test book info extraction with network error."""
        mock_downloader.session.get.side_effect = requests.RequestException(
            "Connection failed"
        )

        with pytest.raises(DownloadError) as exc_info:
            mock_downloader.get_book_info(sample_book_url)

        assert "Failed to fetch book information" in str(exc_info.value)

    def test_get_book_info_parse_error(self, mock_downloader, sample_book_url):
        """Test book info extraction with parse error."""
        mock_response = Mock()
        mock_response.text = "Invalid HTML with no URL"
        mock_response.status_code = 200

        mock_downloader.session.get.return_value = mock_response

        with pytest.raises(DownloadError) as exc_info:
            mock_downloader.get_book_info(sample_book_url)

        assert "Failed to extract book information" in str(exc_info.value)

    @patch("bookfetch.core.downloader.get_unique_output_path")
    @patch("bookfetch.core.downloader.create_pdf_from_images")
    @patch("bookfetch.core.downloader.cleanup_temp_directory")
    def test_download_book_as_pdf(
        self,
        mock_cleanup,
        mock_create_pdf,
        mock_unique_path,
        mock_downloader,
        temp_output_dir,
    ):
        """Test downloading a book as PDF."""
        # Create sample book
        book = Book(
            url="https://archive.org/details/test",
            book_id="test123",
            title="Test Book",
            pages=3,
            image_links=[
                "https://example.com/page1.jpg",
                "https://example.com/page2.jpg",
                "https://example.com/page3.jpg",
            ],
            metadata={},
        )

        # Setup mocks
        temp_dir = temp_output_dir / "Test Book"
        mock_unique_path.side_effect = [temp_dir, temp_output_dir / "Test Book.pdf"]
        mock_create_pdf.return_value = None

        # Mock _download_images to return image paths
        with patch.object(
            mock_downloader,
            "_download_images",
            return_value=[
                temp_dir / "0001.jpg",
                temp_dir / "0002.jpg",
                temp_dir / "0003.jpg",
            ],
        ):
            # Mock loan manager
            mock_downloader.loan_manager.borrow_book = Mock()
            mock_downloader.loan_manager.return_book = Mock()

            result = mock_downloader.download_book(book)

            assert result == temp_output_dir / "Test Book.pdf"
            mock_create_pdf.assert_called_once()
            mock_cleanup.assert_called_once_with(temp_dir)

    @patch("bookfetch.core.downloader.get_unique_output_path")
    def test_download_book_as_jpg(
        self, mock_unique_path, mock_downloader, temp_output_dir
    ):
        """Test downloading a book as JPG images."""
        # Change output format to JPG
        mock_downloader.config.output_format = OutputFormat.JPG

        book = Book(
            url="https://archive.org/details/test",
            book_id="test123",
            title="Test Book",
            pages=2,
            image_links=[
                "https://example.com/page1.jpg",
                "https://example.com/page2.jpg",
            ],
            metadata={},
        )

        temp_dir = temp_output_dir / "Test Book"
        mock_unique_path.return_value = temp_dir

        with patch.object(
            mock_downloader,
            "_download_images",
            return_value=[temp_dir / "0001.jpg", temp_dir / "0002.jpg"],
        ):
            mock_downloader.loan_manager.borrow_book = Mock()
            mock_downloader.loan_manager.return_book = Mock()

            result = mock_downloader.download_book(book)

            assert result == temp_dir
            # Should not create PDF for JPG format

    @patch("bookfetch.core.downloader.cleanup_temp_directory")
    def test_download_book_failure(self, mock_cleanup, mock_downloader):
        """Test download failure handling."""
        book = Book(
            url="https://archive.org/details/test",
            book_id="test123",
            title="Test Book",
            pages=1,
            image_links=["https://example.com/page1.jpg"],
            metadata={},
        )

        # Mock _download_images to raise exception
        with patch.object(
            mock_downloader, "_download_images", side_effect=Exception("Download failed")
        ):
            mock_downloader.loan_manager.borrow_book = Mock()
            mock_downloader.loan_manager.return_book = Mock()

            with pytest.raises(DownloadError) as exc_info:
                mock_downloader.download_book(book)

            assert "Failed to download book" in str(exc_info.value)
            # Should cleanup on failure
            assert mock_cleanup.called
