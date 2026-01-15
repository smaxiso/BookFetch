"""Unit tests for ArchiveAuthenticator."""

import pytest
import requests
from unittest.mock import Mock, patch

from bookfetch.core.authenticator import ArchiveAuthenticator
from bookfetch.utils.exceptions import AuthenticationError, InvalidCredentialsError


class TestArchiveAuthenticator:
    """Test cases for ArchiveAuthenticator."""

    def test_init(self):
        """Test authenticator initialization."""
        auth = ArchiveAuthenticator()
        assert auth.session is None
        assert not auth.is_authenticated()

    def test_successful_login(self, sample_credentials):
        """Test successful login."""
        auth = ArchiveAuthenticator()

        # Mock successful login response
        mock_response = Mock()
        mock_response.text = "Successful login"
        mock_response.status_code = 200

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.return_value = Mock(status_code=200)
            mock_session.post.return_value = mock_response
            mock_session_class.return_value = mock_session

            session = auth.login(sample_credentials)

            assert session is not None
            assert auth.is_authenticated()
            assert auth.get_session() == mock_session
            mock_session.post.assert_called_once()

    def test_invalid_credentials(self, sample_credentials):
        """Test login with invalid credentials."""
        auth = ArchiveAuthenticator()

        # Mock bad login response
        mock_response = Mock()
        mock_response.text = "bad_login"
        mock_response.status_code = 200

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.return_value = Mock(status_code=200)
            mock_session.post.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(InvalidCredentialsError) as exc_info:
                auth.login(sample_credentials)

            assert "Invalid email or password" in str(exc_info.value)
            assert not auth.is_authenticated()

    def test_connection_error(self, sample_credentials):
        """Test login with connection error."""
        auth = ArchiveAuthenticator()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = requests.RequestException("Connection failed")
            mock_session_class.return_value = mock_session

            with pytest.raises(AuthenticationError) as exc_info:
                auth.login(sample_credentials)

            assert "Failed to connect" in str(exc_info.value)

    def test_login_request_failure(self, sample_credentials):
        """Test login when POST request fails."""
        auth = ArchiveAuthenticator()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.return_value = Mock(status_code=200)
            mock_session.post.side_effect = requests.RequestException("Request failed")
            mock_session_class.return_value = mock_session

            with pytest.raises(AuthenticationError) as exc_info:
                auth.login(sample_credentials)

            assert "Login request failed" in str(exc_info.value)

    def test_unexpected_response(self, sample_credentials):
        """Test login with unexpected response."""
        auth = ArchiveAuthenticator()

        # Mock unexpected response
        mock_response = Mock()
        mock_response.text = "Something unexpected"
        mock_response.status_code = 500

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.return_value = Mock(status_code=200)
            mock_session.post.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(AuthenticationError) as exc_info:
                auth.login(sample_credentials)

            assert "unexpected response" in str(exc_info.value)

    def test_format_multipart_data(self):
        """Test multipart data formatting."""
        auth = ArchiveAuthenticator()
        boundary = "----WebKitFormBoundary"
        fields = {"field1": "value1", "field2": "value2"}

        result = auth._format_multipart_data(boundary, fields)

        assert boundary in result
        assert "field1" in result
        assert "value1" in result
        assert "field2" in result
        assert "value2" in result
        assert "Content-Disposition" in result

    def test_get_session_before_login(self):
        """Test get_session before logging in."""
        auth = ArchiveAuthenticator()
        assert auth.get_session() is None

    def test_is_authenticated_before_login(self):
        """Test is_authenticated before logging in."""
        auth = ArchiveAuthenticator()
        assert not auth.is_authenticated()
