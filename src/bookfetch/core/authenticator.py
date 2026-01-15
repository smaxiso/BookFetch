"""Authentication module for Archive.org."""

import random
import string
from typing import Optional

import requests

from bookfetch.config.constants import ARCHIVE_BASE_URL, ARCHIVE_LOGIN_URL
from bookfetch.core.models import AuthCredentials
from bookfetch.utils.exceptions import AuthenticationError, InvalidCredentialsError
from bookfetch.utils.logger import get_logger

logger = get_logger(__name__)


class ArchiveAuthenticator:
    """Handles authentication with Archive.org."""

    def __init__(self) -> None:
        """Initialize authenticator."""
        self.session: Optional[requests.Session] = None

    def login(self, credentials: AuthCredentials) -> requests.Session:
        """Login to Archive.org and create authenticated session.

        Args:
            credentials: Authentication credentials

        Returns:
            Authenticated requests session

        Raises:
            InvalidCredentialsError: If credentials are invalid
            AuthenticationError: If login fails for other reasons
        """
        logger.info("Logging in to Archive.org...")

        session = requests.Session()

        # Get initial cookies
        try:
            session.get(ARCHIVE_LOGIN_URL)
        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to connect to Archive.org: {e}")

        # Generate random boundary for multipart form data
        content_type = "----WebKitFormBoundary" + "".join(
            random.sample(string.ascii_letters + string.digits, 16)
        )

        headers = {"Content-Type": f"multipart/form-data; boundary={content_type}"}

        data = self._format_multipart_data(
            content_type,
            {
                "username": credentials.email,
                "password": credentials.password,
                "submit_by_js": "true",
            },
        )

        # Submit login request
        try:
            response = session.post(ARCHIVE_LOGIN_URL, data=data, headers=headers)
        except requests.RequestException as e:
            raise AuthenticationError(f"Login request failed: {e}")

        # Check response
        if "bad_login" in response.text:
            logger.error("Invalid credentials provided")
            raise InvalidCredentialsError("Invalid email or password")
        elif "Successful login" in response.text:
            logger.info("Successfully logged in to Archive.org")
            self.session = session
            return session
        else:
            logger.error(f"Unexpected login response: {response.status_code}")
            raise AuthenticationError(
                f"Login failed with unexpected response (status {response.status_code})"
            )

    def _format_multipart_data(self, content_type: str, fields: dict) -> str:
        """Format fields as multipart form data.

        Args:
            content_type: Content type boundary string
            fields: Dictionary of field names and values

        Returns:
            Formatted multipart data string
        """
        data = ""
        for name, value in fields.items():
            data += (
                f"--{content_type}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n'
                f"\r\n"
                f"{value}\r\n"
            )
        data += content_type + "--"
        return data

    def get_session(self) -> Optional[requests.Session]:
        """Get current authenticated session.

        Returns:
            Current session or None if not logged in
        """
        return self.session

    def is_authenticated(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self.session is not None
