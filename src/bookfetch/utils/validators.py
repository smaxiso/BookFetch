"""Input validation utilities."""

import re
from pathlib import Path

from bookfetch.config.constants import FORBIDDEN_CHARS, MAX_FILENAME_LENGTH
from bookfetch.utils.exceptions import ValidationError


def validate_archive_url(url: str) -> bool:
    """Validate Archive.org URL or book ID.
    
    Accepts both:
    - Full URL: https://archive.org/details/BookID
    - Just book ID: BookID
    
    Args:
        url: Archive.org URL or book ID to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If URL/ID format is invalid
    """
    if not url or not url.strip():
        raise ValidationError("URL or book ID cannot be empty")
    
    url = url.strip()
    
    # If it looks like a URL, validate it
    if url.startswith("http://") or url.startswith("https://"):
        if "archive.org/details/" not in url:
            raise ValidationError(
                f"Invalid Archive.org URL. Must contain 'archive.org/details/'. Got: {url}"
            )
    # Otherwise, treat it as a book ID (alphanumeric, dash, underscore, dot)
    elif not re.match(r"^[a-zA-Z0-9_.-]+$", url):
        raise ValidationError(
            f"Invalid book ID. Must contain only letters, numbers, dash, underscore, or dot. Got: {url}"
        )
    
    return True


def validate_archive_urls(urls: list[str]) -> bool:
    """Validate multiple Archive.org URLs.

    Args:
        urls: List of URLs to validate

    Returns:
        True if all valid

    Raises:
        ValidationError: If any URL is invalid
    """
    for url in urls:
        validate_archive_url(url)
    return True


def sanitize_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """Sanitize filename by removing forbidden characters and trimming length.

    Args:
        filename: Original filename
        max_length: Maximum length for the filename

    Returns:
        Sanitized filename
    """
    # Remove forbidden characters
    sanitized = "".join(c for c in filename if c not in FORBIDDEN_CHARS)

    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")

    # Trim to max length
    sanitized = sanitized[:max_length]

    return sanitized


def validate_email(email: str) -> bool:
    """Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If email is invalid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: {email}")
    return True


def validate_resolution(resolution: int) -> bool:
    """Validate resolution value.

    Args:
        resolution: Resolution value (0-10, 0 is highest quality)

    Returns:
        True if valid

    Raises:
        ValidationError: If resolution is invalid
    """
    if not 0 <= resolution <= 10:
        raise ValidationError(f"Resolution must be between 0 and 10, got {resolution}")
    return True


def validate_threads(threads: int) -> bool:
    """Validate number of threads.

    Args:
        threads: Number of threads

    Returns:
        True if valid

    Raises:
        ValidationError: If threads value is invalid
    """
    if threads < 1:
        raise ValidationError(f"Threads must be at least 1, got {threads}")
    if threads > 200:
        raise ValidationError(f"Threads must be at most 200, got {threads}")
    return True


def validate_output_dir(output_dir: Path) -> bool:
    """Validate and create output directory if it doesn't exist.

    Args:
        output_dir: Output directory path

    Returns:
        True if valid

    Raises:
        ValidationError: If directory is invalid or can't be created
    """
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        raise ValidationError(f"Cannot create output directory {output_dir}: {e}") from e


def extract_book_id(url: str) -> str:
    """Extract book ID from Archive.org URL or return the ID itself.
    
    Supports both:
    - Full URL: https://archive.org/details/BookID → BookID
    - Just ID: BookID → BookID

    Args:
        url: Archive.org URL or book ID

    Returns:
        Extracted book ID

    Raises:
        ValidationError: If book ID cannot be extracted or is invalid
    """
    try:
        url = url.strip()
        
        # If it's a URL, extract the ID
        if "archive.org/details/" in url:
            book_id = url.split("archive.org/details/")[1].split("?")[0].split("/")[0]
        else:
            # Already a book ID
            book_id = url
        
        if not book_id:
            raise ValidationError("Empty book ID")
            
        return book_id
    except (IndexError, ValueError) as e:
        raise ValidationError(f"Cannot extract book ID from URL {url}: {e}") from e
