"""Unit tests for validators module."""

import pytest

from bookfetch.utils.exceptions import ValidationError
from bookfetch.utils.validators import (
    extract_book_id,
    sanitize_filename,
    validate_archive_url,
    validate_archive_urls,
    validate_email,
    validate_resolution,
    validate_threads,
)


class TestURLValidation:
    """Tests for URL validation."""

    def test_valid_url(self):
        """Test validation of valid Archive.org URL."""
        url = "https://archive.org/details/testbook"
        assert validate_archive_url(url)

    def test_valid_book_id(self):
        """Test validation of book ID."""
        book_id = "IntermediatePython"
        assert validate_archive_url(book_id)

    def test_invalid_url_empty(self):
        """Test validation of empty URL."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_archive_url("")

    def test_invalid_url_wrong_domain(self):
        """Test validation of wrong domain URL."""
        with pytest.raises(ValidationError, match="Invalid Archive.org URL"):
            validate_archive_url("https://example.com/details/book")

    def test_invalid_url_missing_details(self):
        """Test validation of URL missing /details/ path."""
        with pytest.raises(ValidationError, match="Invalid Archive.org URL"):
            validate_archive_url("https://archive.org/book123")

    def test_invalid_book_id_special_chars(self):
        """Test validation of book ID with invalid characters."""
        with pytest.raises(ValidationError, match="Invalid book ID"):
            validate_archive_url("Book With Spaces")

    def test_validate_multiple_urls(self):
        """Test validation of multiple URLs."""
        urls = [
            "https://archive.org/details/book1",
            "https://archive.org/details/book2",
            "IntermediatePython",
        ]
        assert validate_archive_urls(urls)


class TestFilenameSanitization:
    """Tests for filename sanitization."""

    def test_sanitize_basic_filename(self):
        """Test basic filename sanitization."""
        filename = "Hello World"
        assert sanitize_filename(filename) == "Hello_World"

    def test_sanitize_forbidden_characters(self):
        """Test removal of forbidden characters."""
        filename = 'Book: Chapter <1> - "Test"'
        result = sanitize_filename(filename)
        assert ":" not in result
        assert "<" not in result
        assert ">" not in result
        assert '"' not in result

    def test_sanitize_long_filename(self):
        """Test trimming of long filenames."""
        filename = "A" * 200
        result = sanitize_filename(filename, max_length=150)
        assert len(result) == 150

    def test_sanitize_preserves_valid_chars(self):
        """Test that valid characters are preserved."""
        filename = "Book_123-Title.pdf"
        result = sanitize_filename(filename)
        assert "123" in result
        assert "-" in result
        assert "." in result


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test validation of valid email."""
        assert validate_email("user@example.com") is True

    def test_valid_email_with_plus(self):
        """Test validation of email with plus sign."""
        assert validate_email("user+tag@example.com") is True

    def test_invalid_email_missing_at(self):
        """Test validation fails for email without @."""
        with pytest.raises(ValidationError, match="Invalid email"):
            validate_email("userexample.com")

    def test_invalid_email_missing_domain(self):
        """Test validation fails for email without domain."""
        with pytest.raises(ValidationError, match="Invalid email"):
            validate_email("user@")


class TestResolutionValidation:
    """Tests for resolution validation."""

    def test_valid_resolution_min(self):
        """Test validation of minimum resolution."""
        assert validate_resolution(0) is True

    def test_valid_resolution_max(self):
        """Test validation of maximum resolution."""
        assert validate_resolution(10) is True

    def test_valid_resolution_middle(self):
        """Test validation of middle resolution value."""
        assert validate_resolution(5) is True

    def test_invalid_resolution_too_low(self):
        """Test validation fails for resolution below 0."""
        with pytest.raises(ValidationError, match="Resolution must be between"):
            validate_resolution(-1)

    def test_invalid_resolution_too_high(self):
        """Test validation fails for resolution above 10."""
        with pytest.raises(ValidationError, match="Resolution must be between"):
            validate_resolution(11)


class TestThreadsValidation:
    """Tests for threads validation."""

    def test_valid_threads_min(self):
        """Test validation of minimum threads."""
        assert validate_threads(1) is True

    def test_valid_threads_normal(self):
        """Test validation of normal thread count."""
        assert validate_threads(50) is True

    def test_invalid_threads_zero(self):
        """Test validation fails for zero threads."""
        with pytest.raises(ValidationError, match="Threads must be at least 1"):
            validate_threads(0)

    def test_invalid_threads_too_many(self):
        """Test validation fails for too many threads."""
        with pytest.raises(ValidationError, match="Threads must be at most 200"):
            validate_threads(201)


class TestBookIDExtraction:
    """Tests for book ID extraction."""

    def test_extract_book_id_from_url(self):
        """Test extracting book ID from URL."""
        url = "https://archive.org/details/IntermediatePython"
        assert extract_book_id(url) == "IntermediatePython"

    def test_extract_book_id_from_url_with_query(self):
        """Test extracting book ID from URL with query params."""
        url = "https://archive.org/details/book123?ref=opensearch"
        assert extract_book_id(url) == "book123"

    def test_extract_book_id_from_plain_id(self):
        """Test extracting book ID when given just the ID."""
        book_id = "IntermediatePython"
        assert extract_book_id(book_id) == "IntermediatePython"

    def test_extract_book_id_empty(self):
        """Test extracting from empty string raises error."""
        with pytest.raises(ValidationError, match="Empty book ID"):
            extract_book_id("")
