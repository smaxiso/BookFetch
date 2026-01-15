"""Settings and configuration management."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from bookfetch.config.constants import DEFAULT_OUTPUT_DIR, DEFAULT_RESOLUTION, DEFAULT_THREADS


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Authentication
    archive_email: Optional[str] = Field(default=None, alias="ARCHIVE_ORG_EMAIL")
    archive_password: Optional[str] = Field(default=None, alias="ARCHIVE_ORG_PASSWORD")

    # Download settings
    default_resolution: int = Field(default=DEFAULT_RESOLUTION, ge=0, le=10)
    default_threads: int = Field(default=DEFAULT_THREADS, ge=1, le=200)
    default_output_dir: Path = Field(default=Path(DEFAULT_OUTPUT_DIR))
    default_output_format: str = Field(default="pdf")

    # Logging
    log_level: str = Field(default="INFO")
    log_file: Optional[Path] = None

    def has_credentials(self) -> bool:
        """Check if credentials are configured.

        Returns:
            True if both email and password are set
        """
        return bool(self.archive_email and self.archive_password)


def get_settings() -> Settings:
    """Get application settings.

    Returns:
        Settings instance
    """
    return Settings()
