"""Sanitize → optional OCR → MarkItDown → write markdown."""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from mdconvert.ocr import run_ocr, should_ocr
from mdconvert.sanitize import (
    output_markdown_path,
    sanitize_input,
    sanitize_output_dir,
)

log = logging.getLogger("mdconvert")


class ConvertError(RuntimeError):
    """Conversion failed after sanitization."""


@dataclass
class ConvertOptions:
    output_dir: Path | str
    ocr_mode: str = "auto"
    ocr_engine: str = "rapidocr"
    force: bool = False


def _markitdown_text(source: Path) -> str:
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise ConvertError(
            "markitdown is not installed. Run: pip install -e '.[dev,gui,ocr]'"
        ) from exc
    converter = MarkItDown()
    result = converter.convert(str(source))
    text = getattr(result, "text_content", None)
    if text is None:
        text = getattr(result, "markdown", None)
    if text is None:
        raise ConvertError("MarkItDown returned no text")
    return str(text)


def convert_file(user_path: str | Path, options: ConvertOptions) -> Path:
    """Convert one file to markdown under the configured output directory."""
    source = sanitize_input(user_path)
    output_dir = sanitize_output_dir(options.output_dir)
    dest = output_markdown_path(source, output_dir, force=options.force)

    convert_source = source
    tmp_dir = None
    try:
        if should_ocr(source, options.ocr_mode):
            log.info("OCR %s (%s)", source.name, options.ocr_engine)
            text = run_ocr(source, engine=options.ocr_engine)
            tmp_dir = tempfile.TemporaryDirectory(prefix="mdconvert-")
            sidecar = Path(tmp_dir.name) / f"{source.stem}.txt"
            sidecar.write_text(text or "", encoding="utf-8")
            convert_source = sidecar
        log.info("MarkItDown %s → %s", convert_source.name, dest)
        markdown = _markitdown_text(convert_source)
        dest.write_text(markdown, encoding="utf-8")
    except ConvertError:
        raise
    except Exception as exc:
        raise ConvertError(f"failed to convert {source}: {exc}") from exc
    finally:
        if tmp_dir is not None:
            tmp_dir.cleanup()
    return dest
