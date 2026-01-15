# Changelog

All notable changes to BookFetch will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-15

### 🎉 Major Rewrite

Complete reorganization into a professional, industry-grade Python package.

### Added

- Modern Python package structure with `src/` layout
- Professional CLI using Click framework
- Configuration management via `.env` files and Pydantic Settings
- Comprehensive data models using dataclasses
- Type hints throughout the codebase
- Structured logging system
- Custom exception hierarchy for better error handling
- Multi-module architecture (authenticator, downloader, loan_manager, converter)
- Utility modules for validation, image processing, and PDF manipulation
- Testing framework with pytest
- Code quality tools (black, ruff, mypy)
- Comprehensive documentation
- MIT License

### Changed

- **BREAKING**: CLI command changed from `python archive-org-downloader.py` to `bookfetch download`
- **BREAKING**: Credentials now managed via `.env` file instead of command-line args only
- **BREAKING**: Downloaded files now go to `downloads/` directory by default
- Improved error handling and user feedback
- Better progress tracking with tqdm
- More robust retry logic for downloads
- Cleaner code organization and separation of concerns

### Improved

- Performance optimizations in multi-threaded downloading
- Better handling of duplicate file names
- Improved PDF metadata embedding
- More intuitive CLI with better help messages
- Enhanced logging with different verbosity levels

### Deprecated

- Old standalone scripts moved to `legacy/` directory
- Direct script execution (`python archive-org-downloader.py`) deprecated in favor of installed CLI

### Removed

- Hardcoded configuration values (now in settings)
- Print statements (replaced with structured logging)

## [1.0.0] - Legacy

Original standalone script implementation.

---

[2.0.0]: https://github.com/smaxiso/BookFetch/releases/tag/v2.0.0
[1.0.0]: https://github.com/smaxiso/BookFetch/releases/tag/v1.0.0
