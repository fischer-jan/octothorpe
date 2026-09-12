"""OCR mode decision and local OCR engines."""

from __future__ import annotations

import logging
from pathlib import Path

from mdconvert.sanitize import ALLOWED_EXTENSIONS

log = logging.getLogger("mdconvert.ocr")

OCR_MODES = ("auto", "always", "never")
OCR_ENGINES = ("rapidocr", "tesseract")

IMAGE_EXTENSIONS = frozenset(
    {"png", "jpg", "jpeg", "tiff", "tif", "webp", "bmp", "gif"}
)
PDF_EXTENSIONS = frozenset({"pdf"})

# Average alphanumeric characters per PDF page below this → treat as scanned.
PDF_OCR_CHAR_THRESHOLD = 40


class OcrError(RuntimeError):
    """OCR engine is missing or failed."""


def extension_of(path: Path) -> str:
    return path.suffix.lower().lstrip(".")


def pdf_alphanumeric_per_page(path: Path) -> float:
    """Return average alphanumeric character count per page."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = reader.pages
    if not pages:
        return 0.0
    total = 0
    for page in pages:
        text = page.extract_text() or ""
        total += sum(1 for char in text if char.isalnum())
    return total / len(pages)


def pdf_needs_ocr(path: Path, threshold: int = PDF_OCR_CHAR_THRESHOLD) -> bool:
    """True when the PDF looks empty or scanned."""
    try:
        avg = pdf_alphanumeric_per_page(path)
    except Exception:
        log.debug("could not read PDF text from %s; treat as scanned", path)
        return True
    return avg < threshold


def should_ocr(path: Path, mode: str) -> bool:
    """Decide whether this file should go through OCR.

    Images: OCR unless mode is never.
    PDFs: OCR when mode is always, or when mode is auto and the PDF looks scanned.
    Office, HTML, text, and other formats: never OCR.
    """
    if mode not in OCR_MODES:
        raise ValueError(f"unknown OCR mode: {mode}")
    if mode == "never":
        return False

    ext = extension_of(path)
    if ext not in ALLOWED_EXTENSIONS:
        return False
    if ext in IMAGE_EXTENSIONS:
        return True
    if ext in PDF_EXTENSIONS:
        if mode == "always":
            return True
        return pdf_needs_ocr(path)
    return False


def _texts_from_rapidocr(result) -> str:
    if result is None:
        return ""
    txts = getattr(result, "txts", None)
    if txts:
        return "\n".join(str(item) for item in txts if item)
    markdown = getattr(result, "to_markdown", None)
    if callable(markdown):
        text = markdown()
        if text:
            return str(text)
    if isinstance(result, (list, tuple)) and result:
        first = result[0]
        # Classic RapidOCR: (boxes, rec_res, elapsed) with rec_res = [(text, score), ...]
        if isinstance(first, (list, tuple)) and result[1:]:
            rec = result[1]
            lines = []
            if isinstance(rec, (list, tuple)):
                for item in rec:
                    if isinstance(item, (list, tuple)) and item:
                        lines.append(str(item[0]))
                    elif isinstance(item, str):
                        lines.append(item)
            if lines:
                return "\n".join(lines)
        lines = []
        for item in result:
            if isinstance(item, str):
                lines.append(item)
            elif isinstance(item, (list, tuple)) and item:
                lines.append(str(item[0]))
        if lines:
            return "\n".join(lines)
    return str(result).strip()


def _ocr_image_rapidocr(image) -> str:
    try:
        from rapidocr import RapidOCR
    except ImportError as exc:
        raise OcrError(
            "RapidOCR is not installed. Run: pip install 'mdconvert[ocr]'"
        ) from exc
    engine = RapidOCR()
    result = engine(image)
    return _texts_from_rapidocr(result)


def _ocr_image_tesseract(image) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise OcrError(
            "pytesseract is not installed. Run: pip install 'mdconvert[tesseract]'"
        ) from exc
    if not isinstance(image, Image.Image):
        with Image.open(image) as opened:
            return pytesseract.image_to_string(opened)
    return pytesseract.image_to_string(image)


def _ocr_image(path: Path, engine: str) -> str:
    if engine == "rapidocr":
        return _ocr_image_rapidocr(str(path))
    if engine == "tesseract":
        return _ocr_image_tesseract(str(path))
    raise OcrError(f"unknown OCR engine: {engine}")


def _iter_pdf_page_images(path: Path):
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise OcrError(
            "pypdfium2 is not installed. Run: pip install 'mdconvert[ocr]'"
        ) from exc
    doc = pdfium.PdfDocument(str(path))
    try:
        for index in range(len(doc)):
            page = doc[index]
            bitmap = page.render(scale=2)
            try:
                yield bitmap.to_pil()
            finally:
                bitmap.close()
                page.close()
    finally:
        doc.close()


def _ocr_pdf(path: Path, engine: str) -> str:
    pages = []
    for image in _iter_pdf_page_images(path):
        if engine == "rapidocr":
            pages.append(_ocr_image_rapidocr(image))
        elif engine == "tesseract":
            pages.append(_ocr_image_tesseract(image))
        else:
            raise OcrError(f"unknown OCR engine: {engine}")
    return "\n\n".join(part.strip() for part in pages if part and part.strip())


def run_ocr(path: Path, engine: str = "rapidocr") -> str:
    """OCR an image or a scanned PDF. Return plain text."""
    if engine not in OCR_ENGINES:
        raise OcrError(f"unknown OCR engine: {engine}")
    ext = extension_of(path)
    log.debug("OCR %s with %s", path, engine)
    if ext in PDF_EXTENSIONS:
        return _ocr_pdf(path, engine)
    if ext in IMAGE_EXTENSIONS:
        return _ocr_image(path, engine)
    raise OcrError(f"cannot OCR extension '.{ext}'")
