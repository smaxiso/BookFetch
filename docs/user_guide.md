# BookFetch User Guide

Complete guide to using BookFetch for downloading books from Archive.org.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Basic Usage](#basic-usage)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Installation

### Prerequisites

- Python 3.9 or higher
- An Archive.org account (free to create at https://archive.org/account/signup)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/smaxiso/BookFetch.git
cd BookFetch

# Install in editable mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Install from PyPI (once published)

```bash
pip install bookfetch
```

### Verify Installation

```bash
bookfetch --help
```

You should see the main help menu with available commands.

## Configuration

### Environment Variables

BookFetch uses a `.env` file to store your Archive.org credentials securely.

1. **Copy the example file:**

```bash
cp .env.example .env
```

2. **Edit the `.env` file:**

```bash
# Required: Your Archive.org credentials
ARCHIVE_ORG_EMAIL=your_email@example.com
ARCHIVE_ORG_PASSWORD=your_password_here

# Optional: Default settings
DEFAULT_RESOLUTION=3          # Image quality (0-10, 0=highest)
DEFAULT_THREADS=50            # Number of concurrent downloads
DEFAULT_OUTPUT_DIR=downloads  # Where to save files
```

### View Current Configuration

```bash
bookfetch configure
```

## Basic Usage

### Download a Single Book

```bash
bookfetch download -u https://archive.org/details/IntermediatePython
```

This will:
1. Authenticate with Archive.org using credentials from `.env`
2. Borrow the book
3. Download all pages
4. Create a PDF in the `downloads/` directory
5. Return the book

### Download with Custom Settings

```bash
bookfetch download \
  -u https://archive.org/details/IntermediatePython \
  -r 0 \              # Highest quality
  -t 100              # 100 concurrent downloads (faster)
```

### Download Multiple Books

```bash
bookfetch download \
  -u https://archive.org/details/book1 \
  -u https://archive.org/details/book2 \
  -u https://archive.org/details/book3
```

### Batch Download from File

Create a text file with URLs (one per line):

```bash
# Create urls.txt
cat > urls.txt << EOF
https://archive.org/details/IntermediatePython
https://archive.org/details/another_book
https://archive.org/details/third_book
EOF

# Download all
bookfetch download -f urls.txt
```

## Advanced Usage

### Download as Individual Images

Instead of creating a PDF, keep images as separate JPG files:

```bash
bookfetch download \
  -u https://archive.org/details/book_id \
  --format jpg
```

### Save Metadata

Save book metadata to a JSON file alongside the download:

```bash
bookfetch download \
  -u https://archive.org/details/book_id \
  -m
```

This creates a `.json` file with title, author, date, and other metadata.

### Convert EPUB to PDF

```bash
# Basic conversion
bookfetch convert mybook.epub

# Custom output path
bookfetch convert mybook.epub -o /path/to/output.pdf
```

### Override Credentials

You can override `.env` credentials with command-line arguments:

```bash
bookfetch download \
  -e different@email.com \
  -p differentpassword \
  -u https://archive.org/details/book_id
```

### Verbose Logging

Enable detailed logging to troubleshoot issues:

```bash
bookfetch download -u URL -v
```

### Custom Output Directory

```bash
bookfetch download \
  -u URL \
  -d /path/to/custom/directory
```

## Troubleshooting

### "Invalid credentials" Error

**Problem:** Login fails with "Invalid email or password"

**Solution:**
1. Verify your credentials are correct
2. Check if you can log in at https://archive.org
3. Ensure `.env` file is in your current directory
4. Try with explicit credentials: `bookfetch download -e email -p password -u URL`

### "Book not available" Error

**Problem:** Cannot borrow the book

**Solution:**
1. Check if the book has lending enabled on Archive.org
2. Some books may have limited copies available
3. Try again later if all copies are currently borrowed

### Download Stops or Hangs

**Problem:** Download freezes partway through

**Solution:**
1. Reduce thread count: `-t 10` (lower = more stable)
2. Check your internet connection
3. Try with verbose logging: `-v` to see where it stops
4. Some books have DRM protection that prevents download

### File Already Exists

**Problem:** "File already exists" warning

**Solution:**
BookFetch automatically creates unique filenames by adding suffixes like `(1)`, `(2)`, etc.
The download will proceed with a new filename.

### Permission Denied

**Problem:** Cannot write to output directory

**Solution:**
1. Ensure you have write permissions to the directory
2. Try a different output directory: `-d ~/Downloads`
3. Check disk space: `df -h`

## FAQ

**Q: Is this legal?**

A: BookFetch respects Archive.org's borrowing system. It borrows books just like the website's built-in reader and returns them after download. Only download books you have the right to access.

**Q: Can I download books permanently?**

A: BookFetch downloads books as PDFs that you can keep. However, please respect copyright and authors' rights.

**Q: Why is download slow?**

A: Try increasing threads: `-t 100`. However, too many threads may cause instability or get rate-limited.

**Q: What's the best resolution setting?**

A: `0` is highest quality (largest file size), `10` is lowest. We recommend `3` (default) as a good balance.

**Q: Can I download from Open Library?**

A: Yes! Open Library links work the same way:
```bash
bookfetch download -u https://openlibrary.org/books/...
```

**Q: How do I uninstall?**

```bash
pip uninstall bookfetch
```

## Getting Help

- **Documentation:** https://github.com/smaxiso/BookFetch
- **Issues:** https://github.com/smaxiso/BookFetch/issues
- **Discussions:** https://github.com/smaxiso/BookFetch/discussions

## See Also

- [Development Guide](development.md) - For contributing to BookFetch
- [README](../README.md) - Quick start and overview
