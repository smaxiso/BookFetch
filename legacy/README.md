# Legacy Scripts

This directory contains the original standalone scripts from BookFetch v1.x.

## ⚠️ Deprecated

These scripts are **no longer maintained** and are kept here for reference only.

### Original Scripts

- **`archive-org-downloader.py`** - Original Archive.org downloader script
- **`epub_to_pdf.py`** - Original EPUB to PDF converter script

## Migration to v2.0

Please use the new **BookFetch v2.0** CLI instead:

### Old Way (v1.x - Deprecated)
```bash
python archive-org-downloader.py -e email -p password -u URL
python epub_to_pdf.py input.epub
```

### New Way (v2.0 - Current)
```bash
bookfetch download -e email -p password -u URL
bookfetch convert input.epub
```

## Benefits of v2.0

- 🎯 Modern CLI with intuitive commands
- 📁 Organized project structure
- ✅ Type-safe with comprehensive testing
- 🔐 Secure credential management via `.env`
- 📝 Better logging and error handling
- 🚀 Improved performance

## Documentation

For full documentation, see the main [README.md](../README.md) in the project root.
