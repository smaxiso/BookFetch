"""Search module for finding books on Archive.org."""

from internetarchive import search_items

from bookfetch.core.models import SearchResult
from bookfetch.utils.exceptions import SearchError
from bookfetch.utils.logger import get_logger

logger = get_logger(__name__)


class ArchiveSearcher:
    """Handles searching for items on Archive.org."""

    def search(
        self, query: str, limit: int = 10, page: int = 1, filter_restricted: bool = False
    ) -> list[SearchResult]:
        """Search for books on Archive.org.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            page: Page number (1-based)
            filter_restricted: If True, exclude restricted items

        Returns:
            List of SearchResult objects
        """
        logger.info(f"Searching for: '{query}' (page: {page}, limit: {limit})")

        try:
            # Construct advanced query to find texts/books
            full_query = f"({query}) AND mediatype:texts AND -mediatype:collection"

            if filter_restricted:
                full_query += " AND -access-restricted-item:true"

            fields = [
                "identifier",
                "title",
                "creator",
                "date",
                "item_size",
                "imagecount",
                "downloads",
                "access-restricted-item",
                "collection",
            ]

            results = []
            # Use 'params' to support pagination directly via internetarchive
            params = {"page": page, "rows": limit}
            search = search_items(full_query, fields=fields, params=params)

            for item in search.iter_as_results():
                # Note: 'rows' param handles limit on server side usually,
                # but iter_as_results might iterate all. We double check limit.
                if len(results) >= limit:
                    break

                try:
                    # Filter out items with 0 pages or 0 size (likely invalid/empty)
                    # Use .get() with default 0 for safety, converting to int
                    try:
                        pages = int(item.get("imagecount", 0))
                        size = int(item.get("item_size", 0))
                    except (ValueError, TypeError):
                        continue

                    if pages == 0 or size == 0:
                        continue

                    # Check for restricted status
                    is_restricted = False
                    restricted_flag = item.get("access-restricted-item")
                    if restricted_flag and str(restricted_flag).lower() == "true":
                        is_restricted = True

                    # Also check collection for library indicators if flag is missing
                    if not is_restricted:
                        collections = item.get("collection", [])
                        if isinstance(collections, str):
                            collections = [collections]
                        if any(
                            c in ["inlibrary", "lendinglibrary", "printdisabled"]
                            for c in collections
                        ):
                            is_restricted = True

                    result = SearchResult(
                        identifier=item.get("identifier", ""),
                        title=item.get("title", "Unknown Title"),
                        creator=item.get("creator", "Unknown Author"),
                        date=item.get("date", "Unknown Date"),
                        item_size=int(item.get("item_size", 0)),
                        image_count=int(item.get("imagecount", 0)),
                        downloads=int(item.get("downloads", 0)),
                        is_restricted=is_restricted,
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
