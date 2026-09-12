"""Convert documents to Markdown with optional OCR and MarkItDown."""

__version__ = "0.1.0"

from mdconvert.convert import ConvertError, ConvertOptions, convert_file
from mdconvert.sanitize import SanitizeError

__all__ = [
    "ConvertError",
    "ConvertOptions",
    "SanitizeError",
    "convert_file",
    "__version__",
]
