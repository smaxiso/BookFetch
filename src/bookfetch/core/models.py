"""Data models for BookFetch."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class OutputFormat(str, Enum):
    """Output format options."""

    PDF = "pdf"
    JPG = "jpg"


class DownloadStatus(str, Enum):
    """Download status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Book:
    """Represents a book from Archive.org."""

    url: str
    book_id: str
    title: str
    pages: int
    image_links: list[str] = field(default_factory=list)
    metadata: Optional[dict] = None

    @property
    def safe_title(self) -> str:
        """Get a filesystem-safe version of the title."""
        from bookfetch.utils.validators import sanitize_filename

        return sanitize_filename(self.title)


@dataclass
class DownloadConfig:
    """Configuration for download operations."""

    resolution: int = 3
    threads: int = 50
    output_format: OutputFormat = OutputFormat.PDF
    output_dir: Path = Path("downloads")
    save_metadata: bool = False
    verbose: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir)
        if not isinstance(self.output_format, OutputFormat):
            self.output_format = OutputFormat(self.output_format)


@dataclass
class AuthCredentials:
    """Authentication credentials for Archive.org."""

    email: str
    password: str

    def __post_init__(self) -> None:
        """Validate credentials after initialization."""
        if not self.email or not self.password:
            from bookfetch.utils.exceptions import ValidationError

            raise ValidationError("Email and password are required")


@dataclass
class DownloadJob:
    """Represents a download job."""

    book: Book
    config: DownloadConfig
    status: DownloadStatus = DownloadStatus.PENDING
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    progress: int = 0  # Percentage (0-100)

    def mark_completed(self, output_path: Path) -> None:
        """Mark the job as completed."""
        self.status = DownloadStatus.COMPLETED
        self.output_path = output_path
        self.progress = 100

    def mark_failed(self, error_message: str) -> None:
        """Mark the job as failed."""
        self.status = DownloadStatus.FAILED
        self.error_message = error_message

    def mark_in_progress(self, progress: int = 0) -> None:
        """Mark the job as in progress."""
        self.status = DownloadStatus.IN_PROGRESS
        self.progress = progress
