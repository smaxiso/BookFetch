"""Streamlit Web UI for BookFetch."""

import os
from pathlib import Path

import streamlit as st

from bookfetch.config.settings import get_settings
from bookfetch.core.authenticator import ArchiveAuthenticator
from bookfetch.core.downloader import ArchiveDownloader
from bookfetch.core.models import AuthCredentials, DownloadConfig, OutputFormat, SearchResult
from bookfetch.core.searcher import ArchiveSearcher

# Page Config
st.set_page_config(
    page_title="BookFetch UI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main Streamlit app."""

    # Initialize Session State
    if "results" not in st.session_state:
        st.session_state.results = []
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    # Handle Query Param Persistence (Simple Sync)
    # If query params exist and session is empty, load from params
    # Note: st.query_params is the new API in newer Streamlit versions,
    # but we pinned >=1.30.0 so we used st.query_params (if available) or experimental
    # We will assume standard `st.query_params` dictionary access for reading

    # Simple persistence: Just use session state, user complained about "refresh".
    # st.query_params is stateful in URL.
    try:
        q_params = st.query_params
        param_q = q_params.get("q", "")
    except AttributeError:
        # Fallback for older streamlit
        try:
            q_params = st.experimental_get_query_params()
            param_q = q_params.get("q", [""])[0]
        except Exception:
            param_q = ""

    if "last_query" not in st.session_state:
        st.session_state.last_query = param_q

    # Caching and Deduplication
    if "page_cache" not in st.session_state:
        st.session_state.page_cache = {}  # {page_num: results_list}
    if "seen_ids" not in st.session_state:
        st.session_state.seen_ids = set()

    st.title("📚 BookFetch")
    st.markdown("Professional Archive.org Book Downloader")

    # --- Sidebar: Configuration ---
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Load settings
        settings = get_settings()

        # Credentials
        with st.expander("Credentials", expanded=False):
            email = st.text_input("Email", value=settings.archive_email or "")
            password = st.text_input(
                "Password", value=settings.archive_password or "", type="password"
            )

            if not email or not password:
                st.warning("Please configure credentials.")

        # Download Settings
        output_dir_str = st.text_input("Output Directory", value=str(settings.default_output_dir))
        output_dir = Path(output_dir_str)

        resolution = st.slider("Quality (0=Best, 10=Fastest)", 0, 10, settings.default_resolution)
        threads = st.slider("Threads", 1, 100, settings.default_threads)

        st.divider()
        st.header("📥 Direct Download")
        with st.form("direct_download"):
            direct_id = st.text_input("Book ID / URL")
            if st.form_submit_button("Download Now", type="primary", use_container_width=True):
                if not direct_id:
                    st.error("Please enter an ID or URL.")
                elif not email or not password:
                    st.error("Credentials required!")
                else:
                    # Create a dummy result for the downloader wrapper
                    dummy_res = SearchResult(
                        identifier=direct_id.split("/")[-1],
                        title="Direct Download",
                        creator="Unknown",
                        date="Unknown",
                        item_size=0,
                        image_count=0,
                        downloads=0,
                        is_restricted=False,  # Can't know yet
                    )
                    download_book(dummy_res, email, password, output_dir, resolution, threads)

    # --- Main Area: Tabs ---
    tab1, tab2 = st.tabs(["🔍 Search", "📂 Local Library"])

    with tab1:
        search_interface(email, password, output_dir, resolution, threads)

    with tab2:
        library_tab(output_dir)


def search_interface(email, password, output_dir, resolution, threads):
    """Search interface with pagination."""

    # Search Form
    with st.form("search_form"):
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            query = st.text_input(
                "Search",
                placeholder="Keywords...",
                value=st.session_state.last_query,
            )
        with col2:
            limit = st.number_input("Per Page", 5, 50, 10)
        with col3:
            # Spacer to align button
            st.write("")
            st.write("")
            submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

        # Filter (Outside columns or inside?) Inside form is better
        filter_free = st.checkbox("Show only free books (Hide Restricted)", value=False)

    # Clear Button (outside form)
    if st.button("Clear Results"):
        st.session_state.results = []
        st.session_state.last_query = ""
        st.session_state.current_page = 1
        st.session_state.page_cache = {}
        st.session_state.seen_ids = set()
        # Clear URL params
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()

    # Handle Search Submission
    if submitted and query:
        st.session_state.current_page = 1  # Reset page on new search
        st.session_state.last_query = query
        # Reset cache on new search
        st.session_state.page_cache = {}
        st.session_state.seen_ids = set()

        # Update URL params
        try:
            st.query_params["q"] = query
        except Exception:
            pass

        perform_search(query, limit, 1, filter_free)

    # Pagination Controls (Top)
    if st.session_state.results:
        render_pagination("top", limit, filter_free)

    # Display Results
    if st.session_state.results:
        display_results(st.session_state.results, email, password, output_dir, resolution, threads)
        # Pagination Controls (Bottom)
        render_pagination("bottom", limit, filter_free)


def render_pagination(key_prefix, limit, filter_restricted):
    """Render Next/Prev buttons."""
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1:
        if st.session_state.current_page > 1:
            if st.button("⬅️ Previous", key=f"{key_prefix}_prev", use_container_width=True):
                st.session_state.current_page -= 1
                perform_search(
                    st.session_state.last_query,
                    limit,
                    st.session_state.current_page,
                    filter_restricted,
                )
                st.rerun()
    with c3:
        # We don't verify total results count easily, so always show Next if we have full page
        if len(st.session_state.results) >= limit:
            if st.button("Next ➡️", key=f"{key_prefix}_next", use_container_width=True):
                st.session_state.current_page += 1
                perform_search(
                    st.session_state.last_query,
                    limit,
                    st.session_state.current_page,
                    filter_restricted,
                )
                st.rerun()
    with c2:
        st.markdown(
            f"<p style='text-align: center; padding-top: 5px;'>Page <b>{st.session_state.current_page}</b></p>",
            unsafe_allow_html=True,
        )


def perform_search(query, limit, page, filter_restricted):
    """Execute search and store in session state with caching and deduplication."""

    # Check Cache (only if cache matches filter? simplified: invalidate cache if filter changes logic is hard)
    # Ideally cache key should include filter status.
    # For now, we assume user keeps same filter during pagination.
    # If filter toggled, user hits Search, which resets cache.

    if page in st.session_state.page_cache:
        st.session_state.results = st.session_state.page_cache[page]
        return

    searcher = ArchiveSearcher()
    with st.spinner(f"Searching page {page}..."):
        try:
            results = searcher.search(
                query, limit=limit, page=page, filter_restricted=filter_restricted
            )

            unique_results = []
            current_seen = st.session_state.seen_ids

            for r in results:
                if r.identifier in current_seen:
                    pass  # Skip duplicates seen on previous pages

                if r.identifier not in current_seen:
                    unique_results.append(r)
                    current_seen.add(r.identifier)

            st.session_state.seen_ids = current_seen
            st.session_state.results = unique_results
            st.session_state.page_cache[page] = unique_results

            if not unique_results and results:
                st.warning("All results on this page were duplicates or filtered.")
            elif not results:
                st.info("No results found.")

        except Exception as e:
            st.error(f"Search failed: {e}")


def display_results(results, email, password, output_dir, resolution, threads):
    """Render search results grid."""
    for result in results:
        with st.container(border=True):
            col_img, col_info, col_action = st.columns([1, 5, 2])

            with col_img:
                # Cover image if available
                cover_url = f"https://archive.org/services/img/{result.identifier}"
                st.image(cover_url, width=120)

            with col_info:
                st.subheader(result.title)
                st.caption(f"ID: `{result.identifier}` | Year: {result.date}")

                # Metadata tags
                tags = []
                tags.append(f"📄 {result.image_count} Pages")
                if result.item_size:
                    tags.append(f"💾 {result.item_size / (1024 * 1024):.1f} MB")

                st.markdown(" | ".join(tags))

                # Access Status
                if result.is_restricted:
                    st.error("🔒 Restricted (Limited Preview)")
                else:
                    st.success("🔓 Free Access")

            with col_action:
                st.write("")  # Spacer

                # Symmetrical buttons using columns
                b1, b2 = st.columns(2)

                # Unique key for buttons

                with b1:
                    if st.button(
                        "📥 Download", key=f"dl_{result.identifier}", use_container_width=True
                    ):
                        if not email or not password:
                            st.error("Login req.")
                        else:
                            download_book(result, email, password, output_dir, resolution, threads)
                with b2:
                    st.link_button(
                        "↗️ View",
                        f"https://archive.org/details/{result.identifier}",
                        use_container_width=True,
                    )


def download_book(result, email, password, output_dir, resolution, threads):
    """Handle download process."""
    try:
        # Authenticate
        authenticator = ArchiveAuthenticator()
        credentials = AuthCredentials(email=email, password=password)

        # Create a placeholder for progress
        progress_bar = st.progress(0, text="Starting download...")
        status_text = st.empty()

        # Callback function to update UI
        def update_progress(progress, text):
            progress_bar.progress(progress, text=text)

        with st.status("Downloading...", expanded=True) as status:
            status.write("🔐 Logging in...")
            session = authenticator.login(credentials)

            # Setup Downloader
            config = DownloadConfig(
                resolution=resolution,
                threads=threads,
                output_dir=output_dir,
                output_format=OutputFormat.PDF,
                verbose=False,
            )
            config.output_dir.mkdir(parents=True, exist_ok=True)

            downloader = ArchiveDownloader(session, config)

            status.write("📖 Fetching metadata...")
            book = downloader.get_book_info(result.identifier)

            # Check restriction for direct downloads
            if book.is_restricted:
                status.write("⚠️ Book is restricted!")
                st.warning("Restricted Book: Placeholder download only.")

            status.write(f"📥 Downloading {book.pages} pages...")

            # Pass callback!
            output_path = downloader.download_book(book, on_progress=update_progress)

            progress_bar.progress(1.0, text="Done!")
            status.update(label="✅ Download Complete!", state="complete", expanded=False)
            status_text.success(f"Saved: {output_path.name}")
            # st.balloons() # Maybe too much?

    except Exception as e:
        st.error(f"Download failed: {e}")


def library_tab(output_dir):
    """Show downloaded files."""
    st.header("📂 Local Library")
    if not output_dir.exists():
        st.info("Output directory does not exist yet.")
        return

    files = sorted(output_dir.glob("*.pdf"), key=os.path.getmtime, reverse=True)

    if not files:
        st.info("No PDF files found.")
        return

    for f in files:
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"### 📄 {f.name}")
                st.caption(
                    f"Size: {f.stat().st_size / (1024 * 1024):.1f} MB | Modified: {os.path.getmtime(f)}"
                )
            with col2:
                # Open button - reads file bytes
                with open(f, "rb") as pdf_file:
                    st.download_button(
                        label="📂 Open PDF",
                        data=pdf_file,
                        file_name=f.name,
                        mime="application/pdf",
                        use_container_width=True,
                    )


if __name__ == "__main__":
    main()
