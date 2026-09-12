# mdconvert

Convert documents to Markdown. The tool always sanitizes the input, then it may run OCR, then it calls [Microsoft MarkItDown](https://github.com/microsoft/markitdown).

## Install

Use Python 3.10–3.13. Create a virtual environment in this folder:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ocr]"
```

- `dev` — pytest
- `ocr` — RapidOCR, ONNX Runtime, pypdfium2, Pillow
- `gui` — optional. Only needed if you run the leftover Tk window (`mdconvert-gui` in the venv)

Tesseract is optional. Install the binary yourself, then:

```bash
pip install -e ".[tesseract]"
```

## macOS app (Spotlight)

The product UI is a native SwiftUI app in `MacApp/`. It calls `.venv/bin/mdconvert`. It does not reimplement OCR or MarkItDown.

The look is "ink & amber": warm dark paper, an amber accent, a big drop zone, and one card per file with a type badge and its status. A finished row shows the written `.md` name; hover it for a **Reveal** button that opens the file in Finder. The app icon comes from `scripts/make-icon.swift` (re-run it and copy the PNGs into `Assets.xcassets/AppIcon.appiconset` to change it).

Debug hooks for checking the UI from a terminal, without screen recording: `MDCONVERT_SNAPSHOT=/path.png` renders the window to a PNG and quits; add `MDCONVERT_DEMO=1` for sample rows in every state, or `MDCONVERT_CONVERT_TO=/dir` to really convert the test fixtures first.

After the venv install above:

```bash
bash scripts/install-mac.sh
```

This builds the SwiftUI app, then installs:

- `/Applications/MdConvert.app` (or `~/Applications` if `/Applications` is not writable) — double-click or Spotlight: **MdConvert**
- `~/.local/bin/mdconvert` → the project `.venv` CLI
- `~/.local/bin/mdconvert-gui` → opens the SwiftUI app
- `~/Library/Application Support/MdConvert/project_root.txt` — path to this repo so the app finds the venv

Re-run `scripts/install-mac.sh` if you move this folder.

```bash
open -a MdConvert
```

To build without installing:

```bash
cd MacApp
xcodebuild -project MdConvert.xcodeproj -scheme MdConvert -configuration Release -derivedDataPath ./DerivedData build
```

## CLI

```bash
mdconvert INPUT...
python -m mdconvert INPUT...
```

Flags:

| Flag | Meaning |
| --- | --- |
| `-o` / `--output-dir` | Directory for `.md` files. Default: `output_dir` in config, else the current directory. |
| `--ocr auto\|always\|never` | OCR mode. Default: `auto`. |
| `--ocr-engine rapidocr\|tesseract` | OCR engine. Default: `rapidocr` (local, no system Tesseract). |
| `--force` | Overwrite an existing `.md` file. |
| `--verbose` | Debug logs. |

Examples:

```bash
mdconvert report.pdf -o ~/Documents/md
mdconvert scan.png notes.docx --ocr auto --force
```

The CLI prints each written markdown path. It continues after a per-file error and exits `1` if any file failed.

## GUI

The Mac app is SwiftUI. Open **MdConvert** from Spotlight, or `open -a MdConvert`. The CLI is unchanged.

The window converts documents **to** Markdown (PDF, Office, images, HTML, text, and the other allowed types). Markdown files are not queued in the app. The CLI still accepts them.

- **Add** — queue files. They show as Queued. Convert is still a click.
- **Drop** — queue files and start convert at once.
- **Convert** — run leftover Queued files. The button is off when the list is empty or nothing is Queued.
- **Clear** — empty the list. The status bar goes back to Ready.
- **Settings** (⌘,) — output folder, OCR mode, OCR engine.

The drop zone stays on screen. When files are in the list, it stays compact above the rows. Each row shows the name, a short path, and status: Queued, Converting…, Done, or Failed plus a short error.

The status bar at the bottom is always on. It shows Ready, progress (`Converting 2 of 5…`), a done line (`Converted 5 files`), or an error summary. The app does not open a success dialog when a run finishes. Convert errors stay on the row and in the status bar.

Settings are stored in `~/.config/mdconvert/config.json`. The app passes `-o`, `--ocr`, `--ocr-engine`, and `--force` on each CLI run. Convert overwrites existing `.md` files in the GUI so a second drop of the same file does not stall.

The Python command `mdconvert-gui` still opens the old Tk window. Do not use that as the product UI.

## Auto OCR

`--ocr auto` (default):

1. **Images** (`png`, `jpg`, `jpeg`, `tiff`, `tif`, `webp`, `bmp`, `gif`) — always OCR.
2. **PDF** — extract text with pypdf. If the average alphanumeric character count per page is below 40, or the PDF has no text, treat it as scanned and OCR it. Otherwise skip OCR and send the PDF to MarkItDown.
3. **Office / HTML / TXT / MD / CSV / JSON / XML / EPUB / other** — skip OCR.

`--ocr always` still OCRs only images and PDFs. `--ocr never` skips OCR for every file.

PDF OCR renders pages with pypdfium2 (no Poppler). Image/PDF OCR writes a temporary `.txt` sidecar, then MarkItDown converts that text to Markdown.

## Sanitize (always, fail closed)

- Resolve with `realpath`. Reject `..`, null bytes, non-files, and symlink targets outside the parent directory of the given path.
- Allow only extensions MarkItDown supports (Office, PDF, EPUB, HTML, text/data, images, plus zip/audio/msg/ipynb).
- Reject files larger than 50 MB.
- Write only under the configured output directory.
- Do not overwrite an existing `.md` file unless `--force` (CLI).

## Tests

```bash
source .venv/bin/activate
pytest
```
