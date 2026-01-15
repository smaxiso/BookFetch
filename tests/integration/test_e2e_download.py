"""Integration tests for end-to-end download workflow."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import requests
from bookfetch.core.authenticator import ArchiveAuthenticator
from bookfetch.core.downloader import ArchiveDownloader
from bookfetch.core.models import AuthCredentials, DownloadConfig, OutputFormat


class TestE2EDownload:
    """End-to-end integration tests for book download workflow."""

    @pytest.fixture
    def auth_credentials(self):
        """Create test credentials."""
        return AuthCredentials(email="test@example.com", password="testpass")

    @pytest.fixture
    def download_config(self, temp_output_dir):
        """Create test download configuration."""
        return DownloadConfig(
            resolution=5,
            threads=5,
            output_dir=temp_output_dir,
            output_format=OutputFormat.PDF,
            save_metadata=False,
            verbose=False,
        )

    @patch("requests.Session")
    def test_full_download_workflow(
        self, mock_session_class, auth_credentials, download_config, temp_output_dir
    ):
        """Test complete workflow from login to download."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock login responses
        mock_login_response = Mock()
        mock_login_response.text = "Successful login"
        mock_login_response.status_code = 200

        # Mock book info responses
        page_html = '"url":"//archive.org/download/testbook/__ia_metadata.json"'
        mock_page_response = Mock()
        mock_page_response.text = page_html
        mock_page_response.status_code = 200

        mock_metadata = {
            "data": {
                "metadata": {"title": "Test Book", "creator": "Test Author"},
                "brOptions": {
                    "bookTitle": "Test Book",
                    "data": [
                        [
                            {"uri": "https://example.com/page1.jpg"},
                            {"uri": "https://example.com/page2.jpg"},
                        ]
                    ],
                },
            }
        }
        mock_json_response = Mock()
        mock_json_response.json.return_value = mock_metadata
        mock_json_response.status_code = 200

        # Mock image download responses
        mock_image_response = Mock()
        mock_image_response.content = b"fake_image_data"
        mock_image_response.status_code = 200

        # Setup session response sequence
        mock_session.get.side_effect = [
            Mock(status_code=200),  # Initial login GET
        ]
        mock_session.post.return_value = mock_login_response

        # Test authentication
        authenticator = ArchiveAuthenticator()
        session = authenticator.login(auth_credentials)

        assert authenticator.is_authenticated()
        assert session is not None

        # Reset mock for download phase
        mock_session.get.side_effect = [
            mock_page_response,
            mock_json_response,
        ]

        # Test download
        downloader = ArchiveDownloader(session, download_config)

        with patch.object(downloader, "_download_images") as mock_download_images:
            with patch(
                "bookfetch.core.downloader.create_pdf_from_images"
            ) as mock_create_pdf:
                with patch(
                    "bookfetch.core.downloader.cleanup_temp_directory"
                ) as mock_cleanup:
                    with patch(
                        "bookfetch.core.downloader.get_unique_output_path"
                    ) as mock_unique:
                        # Mock return values
                        temp_dir = temp_output_dir / "Test Book"
                        temp_dir.mkdir(parents=True, exist_ok=True)

                        mock_unique.side_effect = [
                            temp_dir,
                            temp_output_dir / "Test Book.pdf",
                        ]
                        mock_download_images.return_value = [
                            temp_dir / "0001.jpg",
                            temp_dir / "0002.jpg",
                        ]

                        # Mock loan manager
                        downloader.loan_manager.borrow_book = Mock()
                        downloader.loan_manager.return_book = Mock()

                        # Get book info
                        book = downloader.get_book_info(
                            "https://archive.org/details/testbook"
                        )

                        assert book.title == "Test_Book"  # Title is sanitized
                        assert book.pages == 2

                        # Download book
                        result_path = downloader.download_book(book)

                        assert result_path == temp_output_dir / "Test Book.pdf"
                        mock_create_pdf.assert_called_once()
                        mock_cleanup.assert_called_once()
                        downloader.loan_manager.borrow_book.assert_called_once()

    @patch("requests.Session")
    def test_download_with_authentication_failure(
        self, mock_session_class, auth_credentials
    ):
        """Test workflow with authentication failure."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock failed login
        mock_login_response = Mock()
        mock_login_response.text = "bad_login"
        mock_login_response.status_code = 200

        mock_session.get.return_value = Mock(status_code=200)
        mock_session.post.return_value = mock_login_response

        authenticator = ArchiveAuthenticator()

        with pytest.raises(Exception):  # Should raise InvalidCredentialsError
            authenticator.login(auth_credentials)

        assert not authenticator.is_authenticated()

    def test_download_with_invalid_url(self, mock_session, download_config):
        """Test download with invalid book URL."""
        downloader = ArchiveDownloader(mock_session, download_config)

        # Mock network error
        mock_session.get.side_effect = requests.RequestException("Not found")

        with pytest.raises(Exception):  # Should raise DownloadError
            downloader.get_book_info("https://archive.org/details/nonexistent")
