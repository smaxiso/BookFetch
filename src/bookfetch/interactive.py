"""Interactive mode for BookFetch."""

import sys
from typing import Optional

import click

from bookfetch.cli import download_command
from bookfetch.core.models import SearchResult
from bookfetch.core.searcher import ArchiveSearcher
from bookfetch.utils.logger import get_logger

logger = get_logger(__name__)


class InteractiveSession:
    """Manages the interactive CLI session."""

    def __init__(self, ctx: click.Context):
        self.ctx = ctx
        self.searcher = ArchiveSearcher()
        self.current_results: list[SearchResult] = []
        self.current_page = 1
        self.last_query = ""
        self.page_size = 10
        # Caching
        self.cached_results: list[SearchResult] = []
        self.cached_query = ""
        self.cached_limit = 0

    def start(self):
        """Start the main menu loop."""
        while True:
            click.clear()
            click.echo("\n📚 BookFetch Interactive Mode")
            click.echo("===========================")
            click.echo("1. 🔍 Search for a book")
            click.echo("2. 📥 Download a book (by ID/URL)")
            click.echo("3. 🚪 Exit")
            click.echo("===========================")

            choice = click.prompt(
                "Select an option", type=click.Choice(["1", "2", "3"]), show_choices=False
            )

            if choice == "1":
                self.search_flow()
            elif choice == "2":
                self.download_flow()
            elif choice == "3":
                click.echo("👋 Goodbye!")
                sys.exit(0)

    def search_flow(self):
        """Handle search interaction."""
        click.echo("\n🔍 Search")
        query = click.prompt("Enter keywords")
        self.last_query = query
        self.current_page = 1

        while True:
            self.show_results()

            # Sub-menu options depend on state
            click.echo("\nOptions:")
            click.echo("n. Next Page")
            click.echo("d. Download a book from this list")
            click.echo("s. Search new book")
            click.echo("m. Return to Main Menu")

            choice = click.prompt("Action", type=str).lower()

            if choice == "n":
                self.current_page += 1
                # In a real pagination implementation, searcher.search needs offset/page
                # For now, we'll implement a basic one or update searcher
                continue
            elif choice == "d":
                self.download_selection_flow()
            elif choice == "s":
                self.search_flow()  # Recursive restart
                return
            elif choice == "m":
                return
            else:
                click.echo("❌ Invalid option")

    def show_results(self):
        """Display current page of results."""
        click.clear()
        click.echo(f"🔍 Results for: '{self.last_query}' (Page {self.current_page})")

        # We need a searcher method that supports pages
        # Currently searcher.search takes a limit.
        # Ideally, we fetch (page * page_size) items?
        # Or better: Update ArchiveSearcher to support 'page' param

        # Implementing efficient pagination requires 'page' support in searcher
        # For now, let's fetch (page * 10) and slice the last 10
        # This is inefficient for deep pages but works for basic use

        limit = self.current_page * self.page_size

        # Check cache
        if self.last_query == self.cached_query and limit <= self.cached_limit:
            all_results = self.cached_results
        else:
            all_results = self.searcher.search(self.last_query, limit=limit)
            # Update cache
            self.cached_results = all_results
            self.cached_query = self.last_query
            self.cached_limit = limit

        # Slice for current page
        start_idx = (self.current_page - 1) * self.page_size
        self.current_results = all_results[start_idx:limit]

        if not self.current_results:
            click.echo("No more results found.")
            if self.current_page > 1:
                self.current_page -= 1  # Go back
            return

        click.echo(
            f"\n{'INDEX':<6} {'ID':<25} {'TITLE':<35} {'ACCESS':<12} {'PAGES':<8} {'SIZE':<10} {'YEAR'}"
        )
        click.echo("-" * 115)

        for i, res in enumerate(self.current_results, 1):
            title = res.title[:32] + "..." if len(res.title) > 32 else res.title
            size_mb = f"{res.item_size / (1024 * 1024):.1f}MB" if res.item_size else "?"

            access_color = "red" if res.is_restricted else "green"
            access_text = click.style(
                "Restricted" if res.is_restricted else "Free", fg=access_color
            )

            click.echo(
                f"{i:<6} {res.identifier:<25} {title:<35} {access_text:<21} {res.image_count:<8} {size_mb:<10} {res.date}"
            )
        click.echo("-" * 115)

    def download_selection_flow(self):
        """Handle selecting a book from the result list to download."""
        click.echo("\n👉 Enter the Index (1-10) or Book ID to download (or 'c' to cancel)")
        choice = click.prompt("Selection", type=str)

        if choice.lower() == "c":
            return

        book_id = ""
        selected_result = None

        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(self.current_results):
                selected_result = self.current_results[idx - 1]
                book_id = selected_result.identifier
        else:
            book_id = choice
            for r in self.current_results:
                if r.identifier == book_id:
                    selected_result = r
                    break

        if book_id:
            self._trigger_download(book_id, selected_result)
        else:
            click.echo("❌ Invalid selection.")
            click.pause()

    def download_flow(self):
        """Handle direct download interaction."""
        click.echo("\n📥 Direct Download")
        book_id = click.prompt("Enter Book ID or URL")
        self._trigger_download(book_id)

        # After download options
        while True:
            click.echo("\nOptions:")
            click.echo("d. Download another book")
            click.echo("m. Return to Main Menu")

            choice = click.prompt("Action", type=click.Choice(["d", "m"]), show_choices=False)

            if choice == "d":
                self.download_flow()
                return
            elif choice == "m":
                return

    def _trigger_download(self, book_id: str, result: Optional[SearchResult] = None):
        """Invoke the CLI download command."""
        # Check restriction if we have the result object
        if result and result.is_restricted:
            click.echo(
                "\n⚠️  WARNING: This book is designated as 'Restricted' (Limited Preview).", err=True
            )
            click.echo("   Downloads will likely contain placeholder pages only.", err=True)
            if not click.confirm("   Do you want to proceed?"):
                return

        click.echo(f"\n🚀 Starting download for: {book_id}")
        try:
            # We invoke the existing download_command
            # We need to pass the params.
            # Note: simple invoke might not populate defaults handled by click params unless passed
            self.ctx.invoke(download_command, urls=(book_id,), interactive=True)
        except Exception as e:
            click.echo(f"Error starting download: {e}")

        click.pause(info="Press any key to continue...")
