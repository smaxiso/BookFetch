"""Pytest configuration and fixtures."""

from unittest.mock import Mock

import pytest
import requests


@pytest.fixture
def mock_session():
    """Create a mock requests session."""
    session = Mock(spec=requests.Session)
    return session


@pytest.fixture
def sample_book_metadata():
    """Sample book metadata from Archive.org."""
    return {
        "title": "Sample Book Title",
        "creator": "John Doe",
        "date": "2020",
        "identifier": "samplebook123",
        "brOptions": {
            "bookTitle": "Sample Book Title",
            "data": [
                [
                    {"uri": "https://example.com/image1.jpg"},
                    {"uri": "https://example.com/image2.jpg"},
                    {"uri": "https://example.com/image3.jpg"},
                ]
            ],
        },
        "metadata": {
            "title": "Sample Book Title",
            "creator": "John Doe",
            "date": "2020",
        },
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_book_url():
    """Sample Archive.org book URL."""
    return "https://archive.org/details/samplebook123"


@pytest.fixture
def sample_credentials():
    """Sample authentication credentials."""
    from bookfetch.core.models import AuthCredentials

    return AuthCredentials(email="test@example.com", password="testpassword")


@pytest.fixture
def sample_download_config(temp_output_dir):
    """Sample download configuration."""
    from bookfetch.core.models import DownloadConfig

    return DownloadConfig(
        resolution=3,
        threads=10,
        output_dir=temp_output_dir,
        verbose=False,
    )
