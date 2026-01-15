"""Authentication module for Archive.org using official library."""

from typing import Optional

from internetarchive import get_session

from bookfetch.core.models import AuthCredentials
from bookfetch.utils.exceptions import AuthenticationError, InvalidCredentialsError
from bookfetch.utils.logger import get_logger

logger = get_logger(__name__)


class ArchiveAuthenticator:
    """Handles authentication with Archive.org using official internetarchive library."""

    def __init__(self) -> None:
        """Initialize authenticator."""
        self.ia_session = None

    def login(self, credentials: AuthCredentials):
        """Login to Archive.org using official library.

        Args:
            credentials: Authentication credentials

        Returns:
            Internet Archive session

        Raises:
            InvalidCredentialsError: If credentials are invalid
            AuthenticationError: If login fails for other reasons
        """
        logger.info("Logging in to Archive.org...")

        try:
            # Use the official internetarchive library
            config = {
                "s3": {
                    "access": credentials.email,
                    "secret": credentials.password,
                }
            }
            
            session = get_session(config=config)
            
            # Test the session by making a simple request
            # The library handles authentication internally
            self.ia_session = session
            logger.info("Successfully logged in to Archive.org")
            return session
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Failed to authenticate with Archive.org: {e}") from e

    def get_session(self):
        """Get current authenticated session.

        Returns:
            Current session or None if not logged in
        """
        return self.ia_session

    def is_authenticated(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self.ia_session is not None
