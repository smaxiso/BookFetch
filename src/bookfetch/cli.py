"""Command-line interface for BookFetch."""

import sys
from pathlib import Path
from typing import Optional

import click

from bookfetch import __version__
from bookfetch.config.settings import get_settings
from bookfetch.core.authenticator import ArchiveAuthenticator
from bookfetch.core.converter import EPUBConverter
from bookfetch.core.downloader import ArchiveDownloader
from bookfetch.core.models import AuthCredentials, DownloadConfig, OutputFormat
from bookfetch.core.searcher import ArchiveSearcher
from bookfetch.utils.exceptions import BookFetchError
from bookfetch.utils.logger import setup_logger
from bookfetch.utils.validators import validate_archive_urls


@click.group()
@click.version_option(version=__version__, prog_name="bookfetch")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """BookFetch - Professional Archive.org book downloader.

    Download books from Archive.org and convert EPUB files to PDF format.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Setup logging
    setup_logger(verbose=verbose)


@cli.command()
@click.argument("query")
@click.option(
    "-l",
    "--limit",
    default=10,
    help="Number of results to show (default: 10)",
    type=click.IntRange(1, 100),
)
@click.option(
    "-d",
    "--download",
    is_flag=True,
    help="Interactively download a book after searching",
)
@click.pass_context
def search(ctx: click.Context, query: str, limit: int, download: bool) -> None:
    """Search for books on Archive.org.

    Examples:
        bookfetch search "python programming"
        bookfetch search "clean code" --limit 5
        bookfetch search "python" --download
    """
    try:
        searcher = ArchiveSearcher()
        click.echo(f"🔍 Searching for: '{query}'...")

        results = searcher.search(query, limit)

        if not results:
            click.echo("❌ No results found.")
            sys.exit(0)

        # Print detailed results
        click.echo(f"\nFound {len(results)} results:\n")
        click.echo(f"{'INDEX':<6} {'ID':<25} {'TITLE':<40} {'PAGES':<8} {'SIZE':<10} {'YEAR'}")
        click.echo("-" * 100)

        for i, res in enumerate(results, 1):
            title = res.title[:37] + "..." if len(res.title) > 37 else res.title
            size_mb = f"{res.item_size / (1024 * 1024):.1f}MB" if res.item_size else "?"
            click.echo(
                f"{i:<6} {res.identifier:<25} {title:<40} {res.image_count:<8} {size_mb:<10} {res.date}"
            )
        click.echo("-" * 100)

        # Interactive download flow
        if download:
            click.echo("\n👉 Enter the Index or Book ID to download (or 'q' to quit)")
            choice = click.prompt("Selection", type=str)

            if choice.lower() in ("q", "quit", "exit"):
                click.echo("👋 Exiting.")
                sys.exit(0)

            # Determine book ID
            book_id = ""
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(results):
                    book_id = results[idx - 1].identifier
                    click.echo(f"Selected: {results[idx - 1].title}")
            else:
                book_id = choice  # User typed ID directly

            if book_id:
                # Invoke interactive download command
                ctx.invoke(download_command, urls=(book_id,))
            else:
                click.echo("❌ Invalid selection.")

    except BookFetchError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Search cancelled by user", err=True)
        sys.exit(130)


@cli.command(name="download")
@click.option(
    "-e",
    "--email",
    help="Archive.org email (or set ARCHIVE_ORG_EMAIL env var)",
    type=str,
)
@click.option(
    "-p",
    "--password",
    help="Archive.org password (or set ARCHIVE_ORG_PASSWORD env var)",
    type=str,
)
@click.option(
    "-u",
    "--url",
    "urls",
    multiple=True,
    help="Book URL (can be used multiple times)",
    type=str,
)
@click.option(
    "-f",
    "--file",
    "url_file",
    help="File containing book URLs (one per line)",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "-r",
    "--resolution",
    help="Image resolution (0-10, 0=highest quality) [default: from config or 3]",
    type=click.IntRange(0, 10),
)
@click.option(
    "-t",
    "--threads",
    help="Number of download threads [default: from config or 50]",
    type=click.IntRange(1, 200),
)
@click.option(
    "-d",
    "--output-dir",
    help="Output directory [default: from config or ./downloads]",
    type=click.Path(path_type=Path),
)
@click.option(
    "--format",
    "output_format",
    help="Output format [default: pdf]",
    type=click.Choice(["pdf", "jpg"], case_sensitive=False),
)
@click.option(
    "-m",
    "--metadata",
    "save_metadata",
    is_flag=True,
    help="Save book metadata to JSON file",
)
@click.pass_context
def download_command(
    ctx: click.Context,
    email: Optional[str],
    password: Optional[str],
    urls: tuple,
    url_file: Optional[Path],
    resolution: Optional[int],
    threads: Optional[int],
    output_dir: Optional[Path],
    output_format: Optional[str],
    save_metadata: bool,
) -> None:
    """Download books from Archive.org."""
    try:
        # Load settings
        settings = get_settings()
        verbose = ctx.obj.get("verbose", False)

        # Get credentials
        email = email or settings.archive_email
        password = password or settings.archive_password

        if not email or not password:
            click.echo(
                "Error: Email and password required. "
                "Use --email/--password or set ARCHIVE_ORG_EMAIL/ARCHIVE_ORG_PASSWORD env vars.",
                err=True,
            )
            sys.exit(1)

        # Get URLs
        url_list: list[str] = list(urls)

        if url_file:
            with open(url_file) as f:
                file_urls = [line.strip() for line in f if line.strip()]
                url_list.extend(file_urls)

        if not url_list:
            click.echo("Error: At least one URL required (use --url or --file)", err=True)
            sys.exit(1)

        # Validate URLs
        try:
            validate_archive_urls(url_list)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

        # Build configuration
        config = DownloadConfig(
            resolution=resolution if resolution is not None else settings.default_resolution,
            threads=threads if threads is not None else settings.default_threads,
            output_dir=output_dir if output_dir else settings.default_output_dir,
            output_format=OutputFormat(output_format) if output_format else OutputFormat.PDF,
            save_metadata=save_metadata,
            verbose=verbose,
        )

        # Ensure output directory exists
        config.output_dir.mkdir(parents=True, exist_ok=True)

        click.echo(f"📚 BookFetch v{__version__}")
        click.echo(f"📖 Books to download: {len(url_list)}")
        click.echo(f"📁 Output directory: {config.output_dir}")
        click.echo()

        # Authenticate
        click.echo("🔐 Logging in to Archive.org...")
        authenticator = ArchiveAuthenticator()
        credentials = AuthCredentials(email=email, password=password)
        session = authenticator.login(credentials)

        # Download each book
        downloader = ArchiveDownloader(session, config)

        for idx, url in enumerate(url_list, 1):
            try:
                click.echo(f"\n{'=' * 60}")
                click.echo(f"📥 Downloading book {idx}/{len(url_list)}")
                click.echo(f"🔗 URL: {url}")

                # Get book info
                book = downloader.get_book_info(url)

                # Download
                output_path = downloader.download_book(book)

                click.echo(f"✅ Success: {output_path}")

            except BookFetchError as e:
                click.echo(f"❌ Failed: {e}", err=True)
                continue

        click.echo(f"\n{'=' * 60}")
        click.echo("🎉 All downloads complete!")

    except BookFetchError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Download cancelled by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("epub_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    "pdf_file",
    help="Output PDF file path (default: same name as EPUB)",
    type=click.Path(path_type=Path),
)
@click.pass_context
def convert(ctx: click.Context, epub_file: Path, pdf_file: Optional[Path]) -> None:
    """Convert EPUB file to PDF."""
    try:
        verbose = ctx.obj.get("verbose", False)

        click.echo("📚 Converting EPUB to PDF...")
        click.echo(f"📄 Input: {epub_file}")

        converter = EPUBConverter()
        output_path = converter.convert(epub_file, pdf_file)

        click.echo(f"✅ Success: {output_path}")

    except BookFetchError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.pass_context
def configure(ctx: click.Context) -> None:
    """Show current configuration."""
    settings = get_settings()

    click.echo("📋 Current Configuration")
    click.echo("=" * 60)
    click.echo(f"Email: {settings.archive_email or '(not set)'}")
    click.echo(f"Password: {'*' * 8 if settings.archive_password else '(not set)'}")
    click.echo(f"Default Resolution: {settings.default_resolution}")
    click.echo(f"Default Threads: {settings.default_threads}")
    click.echo(f"Default Output Dir: {settings.default_output_dir}")
    click.echo(f"Default Output Format: {settings.default_output_format}")
    click.echo(f"Log Level: {settings.log_level}")
    click.echo("=" * 60)

    if not settings.has_credentials():
        click.echo(
            "\n⚠️  No credentials configured. "
            "Create a .env file with ARCHIVE_ORG_EMAIL and ARCHIVE_ORG_PASSWORD"
        )


def main() -> None:
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
