"""Image processing utilities."""

from pathlib import Path


def generate_image_filename(page_num: int, total_pages: int, directory: Path) -> Path:
    """Generate zero-padded image filename.

    Args:
        page_num: Page number (0-indexed)
        total_pages: Total number of pages
        directory: Output directory

    Returns:
        Path to image file

    Example:
        >>> generate_image_filename(5, 100, Path("/tmp"))
        Path('/tmp/005.jpg')
    """
    # Calculate number of digits needed for zero padding
    num_digits = len(str(total_pages))

    # Generate zero-padded filename
    filename = f"{str(page_num).zfill(num_digits)}.jpg"

    return directory / filename


def get_image_files(directory: Path, total_pages: int) -> list[Path]:
    """Get list of all downloaded image files in order.

    Args:
        directory: Directory containing images
        total_pages: Total number of pages

    Returns:
        Sorted list of image file paths
    """
    images = []
    for i in range(total_pages):
        image_path = generate_image_filename(i, total_pages, directory)
        if image_path.exists():
            images.append(image_path)

    return images
