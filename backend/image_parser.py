"""Extract text from images using OCR (Tesseract)."""

import io
from typing import Union, BinaryIO

# Allowed image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}


def extract_text_from_image(source: Union[str, BinaryIO, bytes]) -> str:
    """
    Extract text from an image using OCR (Tesseract).
    source: file path (str), file-like object, or bytes.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "pytesseract and Pillow are required. Install with: pip install pytesseract Pillow. "
            "Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract"
        ) from e

    if isinstance(source, bytes):
        source = io.BytesIO(source)

    try:
        img = Image.open(source)
    except Exception as e:
        raise ValueError(f"Could not open image: {e}") from e

    # Convert to RGB if necessary (e.g. RGBA, P mode)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    text = pytesseract.image_to_string(img)
    return (text or "").strip()
