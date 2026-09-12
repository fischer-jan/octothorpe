from pathlib import Path

import pytest

from mdconvert.convert import ConvertError, ConvertOptions, convert_file
from mdconvert.ocr import run_ocr
from mdconvert.sanitize import SanitizeError

FIXTURES = Path(__file__).parent / "fixtures"


def test_convert_txt_smoke(tmp_path: Path) -> None:
    src = FIXTURES / "hello.txt"
    dest = convert_file(
        src,
        ConvertOptions(output_dir=tmp_path, ocr_mode="never"),
    )
    assert dest == tmp_path / "hello.md"
    text = dest.read_text(encoding="utf-8")
    assert "Hello from mdconvert" in text


def test_convert_refuses_overwrite(tmp_path: Path) -> None:
    src = FIXTURES / "hello.txt"
    convert_file(src, ConvertOptions(output_dir=tmp_path, ocr_mode="never"))
    with pytest.raises(SanitizeError, match="--force"):
        convert_file(src, ConvertOptions(output_dir=tmp_path, ocr_mode="never"))
    dest = convert_file(
        src,
        ConvertOptions(output_dir=tmp_path, ocr_mode="never", force=True),
    )
    assert dest.exists()


def test_ocr_sidecar_then_markitdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = FIXTURES / "tiny.png"

    def fake_ocr(path: Path, engine: str = "rapidocr") -> str:
        assert path.resolve() == src.resolve()
        assert engine == "rapidocr"
        return "OCR LINE ONE\nOCR LINE TWO"

    monkeypatch.setattr("mdconvert.convert.run_ocr", fake_ocr)
    dest = convert_file(
        src,
        ConvertOptions(output_dir=tmp_path, ocr_mode="auto", ocr_engine="rapidocr"),
    )
    text = dest.read_text(encoding="utf-8")
    assert "OCR LINE ONE" in text
    assert "OCR LINE TWO" in text


def test_run_ocr_rejects_office(tmp_path: Path) -> None:
    docx = tmp_path / "x.docx"
    docx.write_bytes(b"PK")
    with pytest.raises(Exception):
        run_ocr(docx, engine="rapidocr")


def test_convert_unknown_extension_fails(tmp_path: Path) -> None:
    src = tmp_path / "nope.bin"
    src.write_text("x", encoding="utf-8")
    with pytest.raises(SanitizeError):
        convert_file(src, ConvertOptions(output_dir=tmp_path))


def test_convert_error_wraps_markitdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "note.txt"
    src.write_text("hi", encoding="utf-8")

    def boom(_path: Path) -> str:
        raise RuntimeError("markitdown down")

    monkeypatch.setattr("mdconvert.convert._markitdown_text", boom)
    with pytest.raises(ConvertError, match="markitdown down"):
        convert_file(src, ConvertOptions(output_dir=tmp_path, ocr_mode="never"))
