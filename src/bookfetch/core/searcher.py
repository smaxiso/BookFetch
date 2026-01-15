"""Search module for finding books on Archive.org."""

from internetarchive import search_items

from bookfetch.core.models import SearchResult
from bookfetch.utils.exceptions import SearchError
from bookfetch.utils.logger import get_logger

logger = get_logger(__name__)


class ArchiveSearcher:
    """Handles searching for items on Archive.org."""

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search for books on Archive.org.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of SearchResult objects

        Raises:
            SearchError: If search fails
        """
        logger.info(f"Searching for: '{query}' (limit: {limit})")

        try:
            # Construct advanced query to find texts/books
            # mediatype:texts ensures we find books
            # -mediatype:collection excludes collections
            full_query = f"({query}) AND mediatype:texts AND -mediatype:collection"

            fields = [
                "identifier",
                "title",
                "creator",
                "date",
                "item_size",
                "imagecount",
                "downloads",
            ]

            results = []
            search = search_items(full_query, fields=fields)

            for item in search.iter_as_results():
                if len(results) >= limit:
                    break

                try:
                    result = SearchResult(
                        identifier=item.get("identifier", ""),
                        title=item.get("title", "Unknown Title"),
                        creator=item.get("creator", "Unknown Author"),
                        date=item.get("date", "Unknown Date"),
                        item_size=int(item.get("item_size", 0)),
                        image_count=int(item.get("imagecount", 0)),
                        downloads=int(item.get("downloads", 0)),
                    )
                    results.append(result)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping malformed search result: {e}")
                    continue

            logger.info(f"Found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(f"Failed to perform search: {e}") from e
