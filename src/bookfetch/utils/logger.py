"""Logging configuration for BookFetch."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "bookfetch",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    verbose: bool = False,
) -> logging.Logger:
    """Set up logger with console and optional file handlers.

    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        verbose: If True, set level to DEBUG

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)

    # Set level based on verbose flag
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Create formatters
    detailed_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(simple_formatter if not verbose else detailed_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "bookfetch") -> logging.Logger:
    """Get the logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
