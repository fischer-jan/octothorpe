from pathlib import Path

import pytest

from octothorpe.ocr import pdf_needs_ocr, should_ocr

FIXTURES = Path(__file__).parent / "fixtures"


def test_image_auto_ocr() -> None:
    assert should_ocr(FIXTURES / "tiny.png", "auto") is True


def test_image_never_skips() -> None:
    assert should_ocr(FIXTURES / "tiny.png", "never") is False


def test_image_always_ocr() -> None:
    assert should_ocr(FIXTURES / "tiny.png", "always") is True


def test_text_pdf_auto_skips() -> None:
    pdf = FIXTURES / "hello.pdf"
    assert pdf_needs_ocr(pdf) is False
    assert should_ocr(pdf, "auto") is False


def test_blank_pdf_auto_ocr() -> None:
    pdf = FIXTURES / "blank.pdf"
    assert pdf_needs_ocr(pdf) is True
    assert should_ocr(pdf, "auto") is True


def test_pdf_always_ocr() -> None:
    assert should_ocr(FIXTURES / "hello.pdf", "always") is True


def test_pdf_never_skips() -> None:
    assert should_ocr(FIXTURES / "blank.pdf", "never") is False


def test_office_skips_even_always(tmp_path: Path) -> None:
    docx = tmp_path / "memo.docx"
    docx.write_bytes(b"PK\x03\x04not-a-real-docx")
    assert should_ocr(docx, "auto") is False
    assert should_ocr(docx, "always") is False


def test_txt_md_html_skip(tmp_path: Path) -> None:
    for name in ("a.txt", "b.md", "c.html"):
        path = tmp_path / name
        path.write_text("hello world", encoding="utf-8")
        assert should_ocr(path, "auto") is False
        assert should_ocr(path, "always") is False


def test_unknown_mode_raises() -> None:
    with pytest.raises(ValueError, match="unknown OCR mode"):
        should_ocr(FIXTURES / "tiny.png", "maybe")
