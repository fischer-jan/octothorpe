"""Command-line entry: octothorpe INPUT..."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from octothorpe.config import load_config
from octothorpe.convert import ConvertError, ConvertOptions, convert_file
from octothorpe.ocr import OCR_ENGINES, OCR_MODES
from octothorpe.sanitize import SanitizeError

log = logging.getLogger("octothorpe")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="octothorpe",
        description="Convert documents to Markdown (optional OCR, then MarkItDown).",
    )
    parser.add_argument("inputs", nargs="+", help="input files")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="directory for .md files (default: config or current directory)",
    )
    parser.add_argument(
        "--ocr",
        choices=OCR_MODES,
        default=None,
        help="OCR mode (default: auto, or value from config)",
    )
    parser.add_argument(
        "--ocr-engine",
        choices=OCR_ENGINES,
        default=None,
        help="OCR engine (default: rapidocr)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing markdown files",
    )
    parser.add_argument(
        "--tidy",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="join hard-wrapped lines, remove hyphenation at line ends and collapse blank lines (default: on, or value from config)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print debug logs",
    )
    return parser


def resolve_output_dir(cli_value: str | None) -> Path:
    if cli_value:
        return Path(cli_value)
    config = load_config()
    if config.output_dir:
        return Path(config.output_dir)
    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    config = load_config()
    options = ConvertOptions(
        output_dir=resolve_output_dir(args.output_dir),
        ocr_mode=args.ocr or config.ocr,
        ocr_engine=args.ocr_engine or config.ocr_engine,
        force=args.force,
        tidy=config.tidy if args.tidy is None else args.tidy,
    )
    failures = 0
    for item in args.inputs:
        try:
            dest = convert_file(item, options)
        except (SanitizeError, ConvertError) as exc:
            print(f"error: {item}: {exc}", file=sys.stderr)
            failures += 1
            continue
        print(dest)
    return 1 if failures else 0
