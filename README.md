# Octothorpe

Octothorpe turns documents into Markdown. Drop a PDF, a Word file, or a scanned image on the window, and you get a `.md` file next to your other notes.

It is a small layer on top of [Microsoft MarkItDown](https://github.com/microsoft/markitdown). MarkItDown does the actual conversion. Octothorpe adds the parts that make it useful day to day:

- **OCR** for scanned PDFs and images, run locally on your machine.
- **Markdown cleanup** that joins hard-wrapped lines and removes PDF hyphenation.
- **A native Mac app** with a drop zone, plus a CLI for scripts.

The name comes from the `#` sign, which Markdown uses for headings.

## How it works

Each file goes through four steps:

1. **File checks.** Octothorpe accepts only file types MarkItDown can read, refuses files over 50 MB, and follows symlinks before it opens anything. It writes only into the output folder you chose. These checks look at the path and the size, not at the content. See [Limitations](#limitations).
2. **OCR, if needed.** Images always go through OCR. A PDF goes through OCR when it has almost no text of its own (fewer than 40 letters and digits per page on average). Everything else skips OCR.
3. **MarkItDown** converts the file, or the OCR text, to Markdown.
4. **Cleanup.** PDF and OCR text comes out hard-wrapped, one line per printed line. Markdown shows such line breaks as spaces, so they carry no meaning. The cleanup step joins those lines, removes the hyphen when a word was split at a line end (`hy-` / `phenation`), and collapses repeated blank lines. It does not touch code blocks, tables, headings, lists, block quotes, HTML, hard line breaks, or front matter.

## Supported formats

| Kind | Extensions |
| --- | --- |
| Documents | `pdf`, `docx`, `pptx`, `xlsx`, `xls`, `epub`, `msg` |
| Web and text | `html`, `htm`, `txt`, `text`, `md`, `markdown`, `csv`, `json`, `jsonl`, `xml`, `rss`, `atom`, `ipynb` |
| Images (OCR) | `png`, `jpg`, `jpeg`, `tiff`, `tif`, `webp`, `bmp`, `gif` |
| Other | `wav`, `mp3`, `m4a`, `mp4`, `zip` |

The Mac app does not queue `md` and `markdown` files. The CLI accepts them.

## Install

You need Python 3.10 to 3.13. Create a virtual environment inside the project folder and install the package with OCR support:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ocr]"
```

The `ocr` extra brings RapidOCR, ONNX Runtime, pypdfium2, and Pillow. Nothing else is needed; no Poppler, no system Tesseract.

If you prefer Tesseract, install the Tesseract binary yourself, then add the Python bridge:

```bash
pip install -e ".[tesseract]"
```

### Mac app

After the steps above, build and install the app:

```bash
bash scripts/install-mac.sh
```

This puts `Octothorpe.app` into `/Applications` (or `~/Applications`), links the CLI to `~/.local/bin/octothorpe`, and records the project path so the app can find the virtual environment. The app does not contain the converter itself; it calls the CLI from the virtual environment. Run the script again if you move the project folder.

Open the app from Spotlight or with `open -a Octothorpe`.

## Use the Mac app

Drop files on the window to convert them at once, or use **Add** to queue them and **Convert** to start. Each file gets a row with its type, its name, and its status. When a file is done, the row shows the name of the new `.md` file; hover the row for a **Reveal** button that opens it in Finder. Errors stay on the row and in the status bar.

**Settings** (⌘,) holds the output folder, the OCR mode, the OCR engine, and the cleanup toggle. The app overwrites an existing `.md` file so that a second drop of the same document does not stall.

## Use the CLI

```bash
octothorpe report.pdf
octothorpe scan.png notes.docx -o ~/Documents/md --force
```

The CLI prints the path of each written file. If one file fails, it prints the error, moves on, and exits with `1` at the end.

| Flag | Meaning |
| --- | --- |
| `-o`, `--output-dir DIR` | Folder for the `.md` files. Default: the config value, else the current folder. |
| `--ocr auto\|always\|never` | When to OCR. `always` still applies only to images and PDFs. Default: `auto`. |
| `--ocr-engine rapidocr\|tesseract` | Which OCR engine to use. Default: `rapidocr`. |
| `--tidy`, `--no-tidy` | Turn the cleanup step on or off. Default: on. |
| `--force` | Overwrite an existing `.md` file. Without it the CLI refuses. |
| `--verbose` | Print debug logs. |

## Configuration

The app and the CLI share one file: `~/.config/octothorpe/config.json`. The app writes it; you can edit it by hand.

```json
{
  "output_dir": "/Users/you/Documents/md",
  "ocr": "auto",
  "ocr_engine": "rapidocr",
  "tidy": true
}
```

CLI flags win over the config file.

## Limitations

- **Content passes through unchanged.** Octothorpe checks paths, types, and sizes. It does not inspect, filter, or clean the text inside a document. Text from an untrusted document ends up in your Markdown as it is, including any HTML or scripts it contains. Treat the output like you would treat the input.
- **Multi-column PDFs.** The PDF extractor in MarkItDown reads two-column layouts in the wrong order at times. Words then break across a page or column, and the cleanup step cannot always repair them.
- **OCR quality** depends on the scan. RapidOCR works well on clean pages and gets worse with skew, low resolution, or handwriting.
- **Mac only** for the app. The CLI runs wherever Python does. The package also includes a basic Tk window (`octothorpe-gui`, needs the `gui` extra) for use where the Mac app is not available.

## Development

Run the tests:

```bash
source .venv/bin/activate
pytest
```

The cleanup step has golden fixtures in `tests/fixtures/tidy_input.md` and `tidy_expected.md`. Add new cases there.

Build the Mac app without installing it:

```bash
cd MacApp
xcodebuild -project Octothorpe.xcodeproj -scheme Octothorpe -configuration Release -derivedDataPath ./DerivedData build
```

To check the UI from a terminal, set `OCTOTHORPE_SNAPSHOT=/path/out.png`. The app renders its window to that PNG and quits. Add `OCTOTHORPE_DEMO=1` for sample rows in every state, or `OCTOTHORPE_CONVERT_TO=/dir` to convert the test fixtures first. The app icon comes from `scripts/make-icon.swift`.

## License

MIT. See `LICENSE`.
