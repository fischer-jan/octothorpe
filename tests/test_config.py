from pathlib import Path

from mdconvert.config import AppConfig, load_config, save_config


def test_load_missing_returns_defaults(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "nope.json")
    assert cfg.ocr == "auto"
    assert cfg.ocr_engine == "rapidocr"
    assert cfg.output_dir == ""


def test_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    save_config(
        AppConfig(output_dir="/tmp/md", ocr="never", ocr_engine="tesseract"),
        path=path,
    )
    cfg = load_config(path)
    assert cfg.output_dir == "/tmp/md"
    assert cfg.ocr == "never"
    assert cfg.ocr_engine == "tesseract"


def test_invalid_values_fall_back(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"ocr": "banana", "ocr_engine": "magic"}', encoding="utf-8")
    cfg = load_config(path)
    assert cfg.ocr == "auto"
    assert cfg.ocr_engine == "rapidocr"
