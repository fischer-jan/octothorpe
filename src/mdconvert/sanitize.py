"""Fail-closed path and file checks before conversion."""

from __future__ import annotations

import os
from pathlib import Path

# MarkItDown official formats plus the image types this pipeline OCRs.
ALLOWED_EXTENSIONS = frozenset(
    {
        "pdf",
        "docx",
        "pptx",
        "xlsx",
        "xls",
        "html",
        "htm",
        "txt",
        "text",
        "md",
        "markdown",
        "csv",
        "json",
        "jsonl",
        "xml",
        "rss",
        "atom",
        "epub",
        "ipynb",
        "png",
        "jpg",
        "jpeg",
        "tiff",
        "tif",
        "webp",
        "bmp",
        "gif",
        "wav",
        "mp3",
        "m4a",
        "mp4",
        "zip",
        "msg",
    }
)

MAX_BYTES = 50 * 1024 * 1024


class SanitizeError(ValueError):
    """Input or output path is not allowed."""


def _reject_null_and_dotdot(raw: str, *, label: str) -> None:
    if "\x00" in raw:
        raise SanitizeError(f"{label} contains a null byte")
    parts = Path(raw).parts
    if ".." in parts:
        raise SanitizeError(f"{label} contains '..'")


def sanitize_input(user_path: str | Path) -> Path:
    """Resolve a source file and reject unsafe or unsupported inputs."""
    raw = os.fsdecode(user_path)
    _reject_null_and_dotdot(raw, label="input path")

    abs_path = Path(os.path.abspath(os.path.expanduser(raw)))
    if not abs_path.exists():
        raise SanitizeError(f"input does not exist: {abs_path}")
    if not abs_path.is_file():
        raise SanitizeError(f"input is not a regular file: {abs_path}")

    resolved = abs_path.resolve()
    if not resolved.is_file():
        raise SanitizeError(f"input is not a regular file: {resolved}")

    intended_dir = abs_path.parent.resolve()
    try:
        resolved.relative_to(intended_dir)
    except ValueError as exc:
        raise SanitizeError(
            f"symlink escape: {abs_path} resolves to {resolved}"
        ) from exc

    ext = resolved.suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise SanitizeError(f"extension '.{ext}' is not allowed")

    size = resolved.stat().st_size
    if size > MAX_BYTES:
        raise SanitizeError(
            f"file is {size} bytes; max allowed is {MAX_BYTES} bytes"
        )

    return resolved


def sanitize_output_dir(user_dir: str | Path) -> Path:
    """Resolve the output directory. Create it if it is missing."""
    raw = os.fsdecode(user_dir)
    _reject_null_and_dotdot(raw, label="output dir")
    abs_dir = Path(os.path.abspath(os.path.expanduser(raw)))
    abs_dir.mkdir(parents=True, exist_ok=True)
    resolved = abs_dir.resolve()
    if not resolved.is_dir():
        raise SanitizeError(f"output dir is not a directory: {resolved}")
    return resolved


def output_markdown_path(source: Path, output_dir: Path, *, force: bool) -> Path:
    """Return the markdown path under output_dir. Reject overwrite unless force."""
    dest = (output_dir / f"{source.stem}.md").resolve()
    try:
        dest.relative_to(output_dir)
    except ValueError as exc:
        raise SanitizeError(
            f"output path {dest} is outside {output_dir}"
        ) from exc
    if dest.exists() and not force:
        raise SanitizeError(f"output exists (use --force to overwrite): {dest}")
    return dest
