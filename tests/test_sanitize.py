from pathlib import Path

import pytest

from mdconvert.sanitize import (
    MAX_BYTES,
    SanitizeError,
    output_markdown_path,
    sanitize_input,
    sanitize_output_dir,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_allow_txt(tmp_path: Path) -> None:
    src = tmp_path / "note.txt"
    src.write_text("hello", encoding="utf-8")
    assert sanitize_input(src) == src.resolve()


def test_allow_fixture_pdf() -> None:
    pdf = FIXTURES / "hello.pdf"
    assert sanitize_input(pdf).name == "hello.pdf"


def test_allow_png() -> None:
    png = FIXTURES / "tiny.png"
    assert sanitize_input(png).suffix == ".png"


def test_reject_unknown_extension(tmp_path: Path) -> None:
    src = tmp_path / "payload.exe"
    src.write_bytes(b"MZ")
    with pytest.raises(SanitizeError, match="not allowed"):
        sanitize_input(src)


def test_reject_directory(tmp_path: Path) -> None:
    with pytest.raises(SanitizeError, match="not a regular file"):
        sanitize_input(tmp_path)


def test_reject_dotdot(tmp_path: Path) -> None:
    src = tmp_path / "ok.txt"
    src.write_text("x", encoding="utf-8")
    sneaky = str(tmp_path / ".." / tmp_path.name / "ok.txt")
    with pytest.raises(SanitizeError, match=r"\.\."):
        sanitize_input(sneaky)


def test_reject_null_byte(tmp_path: Path) -> None:
    with pytest.raises(SanitizeError, match="null byte"):
        sanitize_input(str(tmp_path / "a\x00.txt"))


def test_reject_missing(tmp_path: Path) -> None:
    with pytest.raises(SanitizeError, match="does not exist"):
        sanitize_input(tmp_path / "nope.txt")


def test_reject_oversize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("mdconvert.sanitize.MAX_BYTES", 8)
    src = tmp_path / "big.txt"
    src.write_text("0123456789", encoding="utf-8")
    with pytest.raises(SanitizeError, match="bytes"):
        sanitize_input(src)
    assert MAX_BYTES == 50 * 1024 * 1024


def test_reject_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    inner = tmp_path / "inbox"
    inner.mkdir()
    link = inner / "note.txt"
    link.symlink_to(outside)
    with pytest.raises(SanitizeError, match="symlink escape"):
        sanitize_input(link)


def test_allow_symlink_inside_dir(tmp_path: Path) -> None:
    inner = tmp_path / "inbox"
    inner.mkdir()
    real = inner / "note.txt"
    real.write_text("ok", encoding="utf-8")
    link = inner / "alias.txt"
    link.symlink_to(real)
    assert sanitize_input(link) == real.resolve()


def test_output_no_overwrite(tmp_path: Path) -> None:
    src = tmp_path / "doc.txt"
    src.write_text("x", encoding="utf-8")
    out = sanitize_output_dir(tmp_path / "out")
    dest = output_markdown_path(src, out, force=False)
    dest.write_text("old", encoding="utf-8")
    with pytest.raises(SanitizeError, match="--force"):
        output_markdown_path(src, out, force=False)
    same = output_markdown_path(src, out, force=True)
    assert same == dest


def test_output_stays_under_dir(tmp_path: Path) -> None:
    out = sanitize_output_dir(tmp_path / "md")
    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")
    dest = output_markdown_path(src, out, force=False)
    assert dest.parent == out
    assert dest.name == "a.md"


def test_reject_dotdot_output_dir(tmp_path: Path) -> None:
    with pytest.raises(SanitizeError, match=r"\.\."):
        sanitize_output_dir(str(tmp_path / "a" / ".." / "b"))
