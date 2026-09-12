"""Persist GUI/CLI defaults under ~/.config/mdconvert/config.json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from mdconvert.ocr import OCR_ENGINES, OCR_MODES

CONFIG_DIR = Path.home() / ".config" / "mdconvert"
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    output_dir: str = ""
    ocr: str = "auto"
    ocr_engine: str = "rapidocr"


def _normalize(data: dict) -> AppConfig:
    ocr = str(data.get("ocr") or "auto").lower()
    if ocr not in OCR_MODES:
        ocr = "auto"
    engine = str(data.get("ocr_engine") or "rapidocr").lower()
    if engine not in OCR_ENGINES:
        engine = "rapidocr"
    output_dir = str(data.get("output_dir") or "")
    return AppConfig(output_dir=output_dir, ocr=ocr, ocr_engine=engine)


def load_config(path: Path | None = None) -> AppConfig:
    cfg_path = path or CONFIG_PATH
    if not cfg_path.is_file():
        return AppConfig()
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppConfig()
    if not isinstance(data, dict):
        return AppConfig()
    return _normalize(data)


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    cfg_path = path or CONFIG_PATH
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(config)
    cfg_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return cfg_path
