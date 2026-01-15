"""Unit tests for ArchiveAuthenticator (using internetarchive library)."""

import pytest

from bookfetch.core.authenticator import ArchiveAuthenticator
from bookfetch.core.models import AuthCredentials
from bookfetch.utils.exceptions import AuthenticationError


class TestArchiveAuthenticator:
    """Test cases for ArchiveAuthenticator."""

    def test_init(self):
        """Test authenticator initialization."""
        auth = ArchiveAuthenticator()
        assert auth.ia_session is None
        assert not auth.is_authenticated()

    def test_successful_login(self, sample_credentials):
        """Test successful login with internetarchive library."""
        auth = ArchiveAuthenticator()
        
        # Login will create a real session with the library
        session = auth.login(sample_credentials)
        
        assert session is not None
        assert auth.is_authenticated()
        assert auth.get_session() is not None

    def test_login_invalid_credentials(self):
        """Test login with completely invalid credentials format."""
        auth = ArchiveAuthenticator()
        invalid_creds = AuthCredentials(email="", password="")
        
        # Even with empty creds, the library creates a session
        # (it doesn't validate until you make actual API calls)
        session = auth.login(invalid_creds)
        assert session is not None

    def test_get_session_before_login(self):
        """Test get_session before logging in."""
        auth = ArchiveAuthenticator()
        assert auth.get_session() is None

    def test_is_authenticated_before_login(self):
        """Test is_authenticated before logging in."""
        auth = ArchiveAuthenticator()
        assert not auth.is_authenticated()
