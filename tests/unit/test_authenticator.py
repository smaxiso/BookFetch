"""Unit tests for ArchiveAuthenticator (using internetarchive library)."""

from bookfetch.core.authenticator import ArchiveAuthenticator


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

    def test_get_session_before_login(self):
        """Test get_session before logging in."""
        auth = ArchiveAuthenticator()
        assert auth.get_session() is None

    def test_is_authenticated_before_login(self):
        """Test is_authenticated before logging in."""
        auth = ArchiveAuthenticator()
        assert not auth.is_authenticated()
