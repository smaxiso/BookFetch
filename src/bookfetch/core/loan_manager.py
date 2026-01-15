"""Loan management module for Archive.org books."""

import requests
from typing import Optional, Tuple

from bookfetch.config.constants import ARCHIVE_LOAN_URL, ARCHIVE_SEARCH_INSIDE_URL
from bookfetch.utils.exceptions import LoanError
from bookfetch.utils.logger import get_logger

logger = get_logger(__name__)


class LoanManager:
    """Manages book borrowing and returning on Archive.org."""

    def __init__(self, session: requests.Session) -> None:
        """Initialize loan manager.

        Args:
            session: Authenticated requests session
        """
        self.session = session

    def borrow_book(
        self, book_id: str, verbose: bool = True
    ) -> Tuple[requests.Session, Optional[str]]:
        """Borrow a book from Archive.org.

        Args:
            book_id: Archive.org book identifier
            verbose: If True, log borrow status

        Returns:
            Tuple of (session, token)
            Token is None if book doesn't need borrowing or error occurs.

        Raises:
            LoanError: If borrowing fails
        """
        if verbose:
            logger.info(f"Attempting to borrow book: {book_id}")

        # ... (implementation) ...

        # Grant access
        data = {"action": "grant_access", "identifier": book_id}

        try:
            response = self.session.post(ARCHIVE_SEARCH_INSIDE_URL, data=data)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.debug(f"Grant access request: {e}")

        # Browse book
        data["action"] = "browse_book"

        try:
            response = self.session.post(ARCHIVE_LOAN_URL, data=data)

            if response.status_code == 400:
                error_msg = response.json().get("error", "Unknown error")

                if (
                    error_msg
                    == "This book is not available to borrow at this time. Please try again later."
                ):
                    logger.info("This book doesn't need to be borrowed")
                    return self.session, None
                else:
                    raise LoanError(f"Cannot borrow book: {error_msg}")

            response.raise_for_status()

        except requests.RequestException as e:
            logger.error(f"Failed to browse book: {e}")
            # If browse fails, we can't proceed with token creation
            raise LoanError(f"Failed to borrow book {book_id}: {e}") from e

        # Create token
        data["action"] = "create_token"

        try:
            response = self.session.post(ARCHIVE_LOAN_URL, data=data)
            response.raise_for_status()

            if "token" in response.text:
                token_data = response.json()
                token = token_data.get("token")
                if verbose:
                    logger.info(f"Successfully borrowed book: {book_id}")
                    logger.debug(f"Loan token response: {response.text}")
                    logger.debug(f"Session cookies: {self.session.cookies.get_dict()}")
                return self.session, token
            else:
                logger.error(f"Failed to create token. Response: {response.text}")
                raise LoanError(
                    "Failed to create token. You may not have permission to borrow this book."
                )

        except requests.RequestException as e:
            logger.error(f"Failed to create token: {e}")
            raise LoanError(f"Failed to borrow book {book_id}: {e}") from e

    def return_book(self, book_id: str) -> None:
        """Return a borrowed book.

        Args:
            book_id: Archive.org book identifier

        Raises:
            LoanError: If returning fails
        """
        logger.info(f"Returning book: {book_id}")

        data = {"action": "return_loan", "identifier": book_id}

        try:
            response = self.session.post(ARCHIVE_LOAN_URL, data=data)
            response.raise_for_status()

            if response.status_code == 200 and response.json().get("success"):
                logger.info(f"Successfully returned book: {book_id}")
            else:
                logger.warning(f"Return book response: {response.text}")
                raise LoanError(f"Failed to return book {book_id}")

        except requests.RequestException as e:
            logger.error(f"Failed to return book: {e}")
            raise LoanError(f"Failed to return book {book_id}: {e}") from e
