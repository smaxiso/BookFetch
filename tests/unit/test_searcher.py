"""Unit tests for ArchiveSearcher."""

from unittest.mock import MagicMock, patch

import pytest

from bookfetch.core.models import SearchResult
from bookfetch.core.searcher import ArchiveSearcher
from bookfetch.utils.exceptions import SearchError


class TestArchiveSearcher:
    """Test cases for ArchiveSearcher."""

    @pytest.fixture
    def searcher(self):
        """Create a searcher instance."""
        return ArchiveSearcher()

    @pytest.fixture
    def mock_search_items(self):
        """Mock internetarchive.search_items."""
        with patch("bookfetch.core.searcher.search_items") as mock:
            yield mock

    def test_search_success(self, searcher, mock_search_items):
        """Test successful search."""
        # Mock search results
        mock_item1 = {
            "identifier": "book1",
            "title": "Book 1",
            "creator": "Author 1",
            "date": "2023",
            "item_size": 1024,
            "imagecount": 100,
            "downloads": 50,
        }
        mock_item2 = {
            "identifier": "book2",
            "title": "Book 2",
            "creator": "Author 2",
            "date": "2022",
            "item_size": 2048,
            "imagecount": 200,
            "downloads": 100,
        }

        mock_results = MagicMock()
        mock_results.iter_as_results.return_value = [mock_item1, mock_item2]
        mock_search_items.return_value = mock_results

        # Perform search
        results = searcher.search("python")

        # Verify results
        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].identifier == "book1"
        assert results[0].title == "Book 1"
        assert results[1].identifier == "book2"
        assert results[1].title == "Book 2"

        # Verify query construction
        mock_search_items.assert_called_once()
        call_args = mock_search_items.call_args
        assert "(python) AND mediatype:texts" in call_args[0][0]

    def test_search_limit(self, searcher, mock_search_items):
        """Test search limit."""
        # Create mock iterator that returns 20 items
        mock_items = [{"identifier": f"book{i}"} for i in range(20)]
        mock_results = MagicMock()
        mock_results.iter_as_results.return_value = mock_items
        mock_search_items.return_value = mock_results

        # Search with limit 5
        results = searcher.search("python", limit=5)

        assert len(results) == 5
        assert results[0].identifier == "book0"
        assert results[4].identifier == "book4"

    def test_search_empty(self, searcher, mock_search_items):
        """Test empty search results."""
        mock_results = MagicMock()
        mock_results.iter_as_results.return_value = []
        mock_search_items.return_value = mock_results

        results = searcher.search("nonexistent")
        assert len(results) == 0

    def test_search_error(self, searcher, mock_search_items):
        """Test search failure handling."""
        mock_search_items.side_effect = Exception("API Error")

        with pytest.raises(SearchError, match="Failed to perform search: API Error"):
            searcher.search("python")

    def test_search_malformed_result(self, searcher, mock_search_items):
        """Test handling of malformed search results."""
        # One valid, one invalid result
        mock_item1 = {"identifier": "book1", "title": "Book 1"}
        # mock_item2 would be invalid handling

        # A simpler test for robust parsing: missing fields should have defaults
        mock_item3 = {"identifier": "book3"}  # Missing title, creator etc

        mock_results = MagicMock()
        mock_results.iter_as_results.return_value = [mock_item1, mock_item3]
        mock_search_items.return_value = mock_results

        results = searcher.search("python")

        assert len(results) == 2
        assert results[1].title == "Unknown Title"
