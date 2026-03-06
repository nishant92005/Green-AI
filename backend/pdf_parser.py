"""Extract text from PDF files."""

import io
from typing import BinaryIO, Union


def extract_text_from_pdf(source: Union[str, BinaryIO, bytes]) -> str:
    """
    Extract all text from a PDF file.
    source: file path (str), file-like object, or bytes.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise RuntimeError("PyMuPDF is required. Install with: pip install pymupdf")

    if isinstance(source, bytes):
        source = io.BytesIO(source)

    doc = fitz.open(stream=source, filetype="pdf")
    parts = []
    try:
        for page in doc:
            parts.append(page.get_text())
    finally:
        doc.close()
    return "\n\n".join(p.strip() for p in parts if p.strip())
