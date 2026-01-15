"""Custom exceptions for BookFetch."""


class BookFetchError(Exception):
    """Base exception for all BookFetch errors."""

    pass


class AuthenticationError(BookFetchError):
    """Raised when authentication fails."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""

    pass


class DownloadError(BookFetchError):
    """Raised when book download fails."""

    pass


class LoanError(BookFetchError):
    """Raised when book borrowing/returning fails."""

    pass


class SearchError(BookFetchError):
    """Raised when search fails."""

    pass


class ConversionError(BookFetchError):
    """Raised when file conversion fails."""

    pass


class ValidationError(BookFetchError):
    """Raised when input validation fails."""

    pass
