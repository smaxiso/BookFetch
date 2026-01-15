"""Constants for BookFetch."""

# Archive.org URLs
ARCHIVE_BASE_URL = "https://archive.org"
ARCHIVE_LOGIN_URL = f"{ARCHIVE_BASE_URL}/account/login"
ARCHIVE_LOAN_URL = f"{ARCHIVE_BASE_URL}/services/loans/loan/"
ARCHIVE_SEARCH_INSIDE_URL = f"{ARCHIVE_BASE_URL}/services/loans/loan/searchInside.php"
ARCHIVE_DETAILS_URL = f"{ARCHIVE_BASE_URL}/details/"

# Default settings
DEFAULT_RESOLUTION = 3
DEFAULT_THREADS = 50
DEFAULT_OUTPUT_DIR = "downloads"
DEFAULT_OUTPUT_FORMAT = "pdf"

# Image resolution range
MIN_RESOLUTION = 0  # Highest quality
MAX_RESOLUTION = 10  # Lowest quality

# File naming
FORBIDDEN_CHARS = '<>:"/\\|?*'
MAX_FILENAME_LENGTH = 150

# HTTP headers
DEFAULT_HEADERS = {
    "Referer": "https://archive.org/",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Dest": "image",
}

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1
