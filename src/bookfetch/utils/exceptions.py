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
    """Raised when download fails."""

    pass


class LoanError(BookFetchError):
    """Raised when book borrowing/returning fails."""

    pass


class ConversionError(BookFetchError):
    """Raised when format conversion fails."""

    pass


class ValidationError(BookFetchError):
    """Raised when input validation fails."""

    pass
