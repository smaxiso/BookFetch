![made-with-python](https://img.shields.io/badge/Made%20with-Python3-brightgreen)
![version](https://img.shields.io/badge/version-2.0.0-blue)
![license](https://img.shields.io/badge/license-MIT-green)

# BookFetch

**Professional Archive.org book downloader and EPUB converter**

Download books from [Archive.org](https://archive.org) and [Open Library](https://openlibrary.org) in PDF format, bypassing the temporary borrowing limitations. Also includes EPUB to PDF conversion utilities.

## ✨ Features

- 📚 **Download books from Archive.org** - Get books in high-quality PDF format
- 🔄 **EPUB to PDF conversion** - Convert EPUB files to PDF
- ⚡ **Multi-threaded downloads** - Fast parallel downloading with configurable threads
- 🎨 **Configurable quality** - Choose image resolution (0-10, where 0 is highest quality)
- 📦 **Batch processing** - Download multiple books from a URL list
- 🔐 **Secure credential management** - Store credentials in `.env` file
- 📝 **Metadata preservation** - Embed book metadata in generated PDFs
- 🎯 **Modern CLI** - User-friendly command-line interface with progress bars
- ✅ **Type-safe** - Built with type hints and Pydantic models
- 🧪 **Well-tested** - Comprehensive unit and integration tests

## 📋 Requirements

- Python 3.9 or higher
- Archive.org account (free to create)

## 🚀 Installation

### From Source (Development)

```bash
# Clone the repository
git clone git@github.com:smaxiso/BookFetch.git
cd BookFetch

# Install in editable mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Using pip (after publishing to PyPI)

```bash
pip install bookfetch
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in your working directory:

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

Add your Archive.org credentials:

```env
ARCHIVE_ORG_EMAIL=your_email@example.com
ARCHIVE_ORG_PASSWORD=your_password_here

# Optional settings
DEFAULT_RESOLUTION=3
DEFAULT_THREADS=50
DEFAULT_OUTPUT_DIR=downloads
```

## 📖 Usage

### Download Books

**Single book download:**

```bash
bookfetch download \\
  -e your_email@example.com \\
  -p your_password \\
  -u https://archive.org/details/IntermediatePython
```

**Multiple books with custom settings:**

```bash
bookfetch download \\
  -r 0 \\
  -t 100 \\
  -u https://archive.org/details/book1 \\
  -u https://archive.org/details/book2 \\
  -u https://archive.org/details/book3
```

**Batch download from file:**

```bash
# Create a file with URLs (one per line)
echo "https://archive.org/details/IntermediatePython" > books.txt
echo "https://archive.org/details/another_book" >> books.txt

# Download all
bookfetch download -f books.txt
```

**Download as individual JPGs instead of PDF:**

```bash
bookfetch download \\
  -u https://archive.org/details/book_id \\
  --format jpg \\
  -m  # Also save metadata
```

### Convert EPUB to PDF

```bash
# Basic conversion
bookfetch convert book.epub

# With custom output path
bookfetch convert book.epub -o /path/to/output.pdf
```

### View Configuration

```bash
bookfetch configure
```

### CLI Options

```bash
bookfetch download --help
bookfetch convert --help
```

**Download options:**

- `-e, --email` - Archive.org email (or set `ARCHIVE_ORG_EMAIL`)
- `-p, --password` - Archive.org password (or set `ARCHIVE_ORG_PASSWORD`)
- `-u, --url` - Book URL (can be used multiple times)
- `-f, --file` - File containing book URLs (one per line)
- `-r, --resolution` - Image resolution 0-10 (0=highest) [default: 3]
- `-t, --threads` - Number of download threads [default: 50]
- `-d, --output-dir` - Output directory [default: ./downloads]
- `--format` - Output format: pdf or jpg [default: pdf]
- `-m, --metadata` - Save book metadata to JSON file
- `-v, --verbose` - Enable verbose logging

## 📁 Project Structure

```
BookFetch/
├── src/bookfetch/          # Main package
│   ├── core/               # Core business logic
│   │   ├── authenticator.py
│   │   ├── downloader.py
│   │   ├── loan_manager.py
│   │   ├── converter.py
│   │   └── models.py
│   ├── utils/              # Utility modules
│   │   ├── validators.py
│   │   ├── logger.py
│   │   ├── image_utils.py
│   │   ├── pdf_utils.py
│   │   └── exceptions.py
│   ├── config/             # Configuration
│   │   ├── settings.py
│   │   └── constants.py
│   └── cli.py              # CLI interface
├── tests/                  # Test suite
├── docs/                   # Documentation
├── downloads/              # Default download directory
├── .env.example            # Environment template
├── pyproject.toml          # Package configuration
└── README.md
```

## 🧪 Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/bookfetch --cov-report=html

# Run specific test file
pytest tests/unit/test_validators.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/bookfetch
```

## 📝 Migration from v1.x

If you were using the old scripts (`archive-org-downloader.py`), here's how to migrate:

**Old way:**
```bash
python archive-org-downloader.py -e email -p pass -u URL
```

**New way:**
```bash
bookfetch download -e email -p pass -u URL
```

The old scripts are preserved in the `legacy/` directory for reference.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational purposes and personal use only. Please respect Archive.org's terms of service and only download books you have the right to access. Support authors by purchasing books when possible.

## 🙏 Acknowledgments

- Original concept from [Archive.org-Downloader](https://github.com/MiniGlome/Archive.org-Downloader)
- Completely rewritten and modernized for BookFetch v2.0

## 📬 Support

- 🐛 Report bugs: [GitHub Issues](https://github.com/smaxiso/BookFetch/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/smaxiso/BookFetch/discussions)

---

**Made with ❤️ by BookFetch Contributors**
