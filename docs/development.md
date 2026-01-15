# BookFetch Development Guide

Guide for developers contributing to BookFetch.

## Table of Contents

- [Setting Up Development Environment](#setting-up-development-environment)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Contributing](#contributing)
- [Release Process](#release-process)

## Setting Up Development Environment

### Prerequisites

- Python 3.9 or higher
- Git
- An Archive.org account for testing

### Initial Setup

1. **Fork and clone the repository:**

```bash
git clone https://github.com/YOUR_USERNAME/BookFetch.git
cd BookFetch
```

2. **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode:**

```bash
pip install -e ".[dev]"
```

This installs BookFetch along with all development dependencies:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `black` - Code formatter
- `ruff` - Fast Python linter
- `mypy` - Static type checker
- `pre-commit` - Git hooks framework

4. **Install pre-commit hooks:**

```bash
pre-commit install
```

Now code quality checks will run automatically before each commit.

5. **Set up credentials:**

```bash
cp .env.example .env
# Edit .env with your Archive.org credentials
```

## Project Structure

```
BookFetch/
├── src/bookfetch/           # Main package
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # CLI interface (Click)
│   ├── core/                # Core business logic
│   │   ├── authenticator.py # Archive.org authentication
│   │   ├── downloader.py    # Book downloading
│   │   ├── loan_manager.py  # Book borrowing/returning
│   │   ├── converter.py     # EPUB to PDF conversion
│   │   └── models.py        # Data models (Pydantic)
│   ├── utils/               # Utility modules
│   │   ├── validators.py    # Input validation
│   │   ├── logger.py        # Logging configuration
│   │   ├── image_utils.py   # Image processing
│   │   ├── pdf_utils.py     # PDF manipulation
│   │   └── exceptions.py    # Custom exceptions
│   └── config/              # Configuration
│       ├── settings.py      # Pydantic settings
│       └── constants.py     # Project constants
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest fixtures
│   ├── unit/                # Unit tests
│   │   ├── test_authenticator.py
│   │   ├── test_downloader.py
│   │   └── test_validators.py
│   └── integration/         # Integration tests
│       └── test_e2e_download.py
├── docs/                    # Documentation
├── .github/workflows/       # CI/CD pipelines
├── pyproject.toml           # Package configuration
└── README.md                # Main documentation
```

## Development Workflow

### Making Changes

1. **Create a feature branch:**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**

Follow these guidelines:
- Write clean, readable code
- Add type hints to all functions
- Follow existing code style
- Update tests for your changes
- Update documentation if needed

3. **Run tests locally:**

```bash
pytest tests/ -v
```

4. **Check code quality:**

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/bookfetch
```

5. **Commit your changes:**

```bash
git add .
git commit -m "feat: add new feature"
```

Pre-commit hooks will run automatically. Fix any issues before committing.

### Commit Message Format

Follow conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
- `feat: add batch download from file`
- `fix: handle network timeout in downloader`
- `docs: update installation instructions`

## Testing

### Running Tests

**Run all tests:**
```bash
pytest tests/
```

**Run unit tests only:**
```bash
pytest tests/unit/
```

**Run integration tests only:**
```bash
pytest tests/integration/
```

**Run with coverage:**
```bash
pytest tests/ --cov=src/bookfetch --cov-report=html
```

Open `htmlcov/index.html` to view the coverage report.

**Run specific test file:**
```bash
pytest tests/unit/test_validators.py -v
```

**Run specific test:**
```bash
pytest tests/unit/test_validators.py::test_validate_url -v
```

### Writing Tests

**Unit test example:**

```python
import pytest
from bookfetch.utils.validators import validate_url

def test_validate_url_valid():
    """Test validation of valid Archive.org URL."""
    url = "https://archive.org/details/book123"
    assert validate_url(url) == True

def test_validate_url_invalid():
    """Test validation of invalid URL."""
    with pytest.raises(ValueError):
        validate_url("not-a-valid-url")
```

**Using fixtures:**

```python
def test_download(mock_session, sample_download_config):
    """Test using fixtures from conftest.py."""
    downloader = ArchiveDownloader(mock_session, sample_download_config)
    # Test logic here
```

## Code Quality

### Formatting

We use **Black** with 100-character line length:

```bash
# Format all code
black src/ tests/

# Check formatting without changing files
black --check src/ tests/
```

### Linting

We use **Ruff** for fast linting:

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix where possible
ruff check --fix src/ tests/
```

### Type Checking

We use **mypy** for static type checking:

```bash
# Type check the package
mypy src/bookfetch
```

All functions should have type hints:

```python
def download_image(url: str, output_path: Path) -> bool:
    """Download image from URL.
    
    Args:
        url: Image URL
        output_path: Where to save the image
        
    Returns:
        True if successful, False otherwise
    """
    # Implementation
```

### Pre-commit Hooks

The pre-commit configuration runs automatically on commit:

```bash
# Run manually on all files
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

## Contributing

### Pull Request Process

1. **Fork the repository** on GitHub

2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes** following the guidelines above

4. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature
   ```

5. **Open a Pull Request** on GitHub

6. **Wait for review** - maintainers will review your PR

7. **Address feedback** if requested

8. **Merge** - once approved, your PR will be merged

### PR Requirements

- ✅ All tests pass
- ✅ Code coverage doesn't decrease
- ✅ Code is formatted with Black
- ✅ No linting errors from Ruff
- ✅ Type hints added for new code
- ✅ Documentation updated if needed
- ✅ Commit messages follow convention

## Release Process

### Version Bumping

We use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Update version in `pyproject.toml`:

```toml
[project]
version = "2.1.0"
```

### Building and Publishing

1. **Update CHANGELOG.md** with release notes

2. **Build the package:**

```bash
python -m build
```

3. **Check the build:**

```bash
twine check dist/*
```

4. **Publish to PyPI:**

```bash
twine upload dist/*
```

5. **Create a Git tag:**

```bash
git tag v2.1.0
git push origin v2.1.0
```

6. **Create GitHub release** with release notes

## Architecture Notes

### Authentication Flow

1. `ArchiveAuthenticator.login()` creates a session
2. Returns authenticated `requests.Session`
3. Session is passed to other components

### Download Flow

1. `ArchiveDownloader.get_book_info()` extracts metadata
2. `LoanManager.borrow_book()` borrows the book
3. `ArchiveDownloader._download_images()` downloads pages
4. `create_pdf_from_images()` creates PDF
5. `LoanManager.return_book()` returns the book

### Error Handling

Custom exceptions in `utils/exceptions.py`:
- `BookFetchError` - Base exception
- `AuthenticationError` - Login/auth issues
- `DownloadError` - Download failures
- `ConversionError` - EPUB conversion issues

## Resources

- **Python Documentation:** https://docs.python.org/3/
- **Pytest Documentation:** https://docs.pytest.org/
- **Click Documentation:** https://click.palletsprojects.com/
- **Pydantic Documentation:** https://docs.pydantic.dev/

## Getting Help

- **GitHub Issues:** https://github.com/smaxiso/BookFetch/issues
- **Discussions:** https://github.com/smaxiso/BookFetch/discussions
