"""Core data models."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class OutputFormat(str, Enum):
    """Output format for downloaded books."""

    PDF = "pdf"
    JPG = "jpg"


@dataclass
class AuthCredentials:
    """Authentication credentials for Archive.org."""

    email: str
    password: str

    def __post_init__(self):
        """Validate credentials."""
        if not self.email or not self.password:
            from bookfetch.utils.exceptions import ValidationError

            raise ValidationError("Email and password are required")


@dataclass
class DownloadConfig:
    """Configuration for book download."""

    resolution: int
    threads: int
    output_format: OutputFormat
    output_dir: Path
    save_metadata: bool = False
    verbose: bool = False


@dataclass
class Book:
    """Represents a book on Archive.org."""

    url: str
    book_id: str
    title: str
    pages: int
    image_links: list[str]
    metadata: dict = field(default_factory=dict)

    @property
    def safe_title(self) -> str:
        """Get filesystem-safe title."""
        from bookfetch.utils.validators import sanitize_filename

        return sanitize_filename(self.title)


@dataclass
class SearchResult:
    """Represents a search result from Archive.org."""

    identifier: str
    title: str
    creator: str
    date: str
    item_size: int
    image_count: int
    downloads: int = 0
