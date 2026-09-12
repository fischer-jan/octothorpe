"""macOS-style drop-zone GUI. Same pipeline as the CLI."""

from __future__ import annotations

import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, ttk
from urllib.parse import unquote, urlparse

from mdconvert.config import AppConfig, load_config, save_config
from mdconvert.convert import ConvertError, ConvertOptions, convert_file
from mdconvert.ocr import OCR_ENGINES, OCR_MODES
from mdconvert.sanitize import SanitizeError

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    HAS_DND = True
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    HAS_DND = False

# Calm light neutrals on top of native ttk.
TEXT = "#1D1D1F"
TEXT_SECONDARY = "#6E6E73"
TEXT_TERTIARY = "#8E8E93"
ACCENT = "#007AFF"
OK = "#248A3D"
ERROR = "#D70015"
DROP_FILL = "#F5F5F7"
DROP_DASH = "#C7C7CC"
DROP_ACTIVE_FILL = "#F0F6FF"
DROP_ACTIVE_DASH = "#007AFF"
HAIRLINE = "#D8D8DC"
ROW_BG = "#FFFFFF"


def split_drop_paths(data: str, tcl: tk.Misc | None = None) -> list[str]:
    """Parse tkinterdnd2 / Tk file-drop payloads."""
    if not data or not str(data).strip():
        return []
    raw: tuple[str, ...] | list[str]
    if tcl is not None:
        try:
            raw = tcl.tk.splitlist(data)
        except tk.TclError:
            raw = _parse_tcl_list(data)
    else:
        raw = _parse_tcl_list(data)
    paths = []
    for part in raw:
        item = _normalize_drop_item(part)
        if item:
            paths.append(item)
    return paths


def _parse_tcl_list(data: str) -> list[str]:
    """Split a Tcl list without a live Tk interpreter."""
    items: list[str] = []
    current: list[str] = []
    brace = 0
    i = 0
    text = data.strip()
    while i < len(text):
        ch = text[i]
        if ch == "{" and brace == 0:
            brace = 1
            i += 1
            continue
        if ch == "}" and brace == 1:
            brace = 0
            items.append("".join(current))
            current = []
            i += 1
            while i < len(text) and text[i] in " \t\n":
                i += 1
            continue
        if ch == "\\" and i + 1 < len(text) and brace == 0:
            current.append(text[i + 1])
            i += 2
            continue
        if ch in " \t\n" and brace == 0:
            if current:
                items.append("".join(current))
                current = []
            i += 1
            continue
        current.append(ch)
        i += 1
    if current:
        items.append("".join(current))
    return items


def _normalize_drop_item(item: str) -> str:
    item = item.strip().strip('"')
    if item.startswith("file:"):
        parsed = urlparse(item)
        path = unquote(parsed.path or "")
        if parsed.netloc and parsed.netloc not in ("", "localhost"):
            path = f"/{parsed.netloc}{path}"
        item = path
    return item


def shorten_home(path: str) -> str:
    text = str(path)
    home = str(Path.home())
    if text == home:
        return "~"
    if text.startswith(home + "/") or text.startswith(home + "\\"):
        return "~" + text[len(home) :]
    return text


def truncate_path(path: str, max_len: int = 52) -> str:
    text = shorten_home(path)
    if len(text) <= max_len:
        return text
    return "…" + text[-(max_len - 1) :]


def display_parts(path: str) -> tuple[str, str]:
    p = Path(path)
    folder = truncate_path(str(p.parent))
    return p.name or path, folder


def row_status_text(status: str, detail: str = "") -> str:
    if status == "pending":
        return "Queued"
    if status == "converting":
        return "Converting…"
    if status == "ok":
        return "Done"
    if status == "error":
        if detail:
            return f"Failed — {detail}"
        return "Failed"
    return status


def format_done_status(ok: int, failed: int) -> str:
    if failed and ok:
        ok_bit = "1 file" if ok == 1 else f"{ok} files"
        fail_bit = "1 failed" if failed == 1 else f"{failed} failed"
        return f"Converted {ok_bit}, {fail_bit}"
    if failed:
        return "1 file failed" if failed == 1 else f"{failed} files failed"
    if ok == 1:
        return "Converted 1 file"
    return f"Converted {ok} files"


def short_error(exc: BaseException | str) -> str:
    text = str(exc).strip() or type(exc).__name__
    text = " ".join(text.split())
    if len(text) > 72:
        return text[:69] + "…"
    return text


def _pick_family() -> str:
    try:
        available = set(tkfont.families())
    except tk.TclError:
        available = set()
    for name in ("SF Pro Text", "SF Pro", "Helvetica Neue"):
        if name in available:
            return name
    if sys.platform == "darwin":
        return ".AppleSystemUIFont"
    return "Helvetica"


@dataclass
class QueueItem:
    path: str
    status: str = "pending"  # pending | converting | ok | error
    detail: str = ""


class MdconvertApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("MdConvert")
        self.root.minsize(560, 440)
        self.root.geometry("640x560")
        self.config = load_config()
        self.items: list[QueueItem] = []
        self._busy = False
        self._run_ok = 0
        self._run_fail = 0
        self._drop_active = False
        self._settings_win: tk.Toplevel | None = None
        self._fonts = self._make_fonts()
        self._build()
        self._bind_shortcuts()
        self._set_status("Ready")

    def _make_fonts(self) -> dict[str, tkfont.Font]:
        family = _pick_family()
        try:
            for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont"):
                tkfont.nametofont(name).configure(family=family)
        except tk.TclError:
            pass
        return {
            "body": tkfont.Font(family=family, size=13),
            "body_bold": tkfont.Font(family=family, size=13, weight="bold"),
            "small": tkfont.Font(family=family, size=11),
            "drop": tkfont.Font(family=family, size=15),
        }

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Command-o>", lambda e: self._add_files())
        self.root.bind("<Command-O>", lambda e: self._add_files())
        self.root.bind("<Command-comma>", lambda e: self._open_settings())
        self.root.bind("<Return>", lambda e: self._convert_clicked())

    def _build(self) -> None:
        status = ttk.Frame(self.root, padding=(16, 6))
        status.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Separator(self.root, orient="horizontal").pack(side=tk.BOTTOM, fill=tk.X)
        self.status_left = ttk.Label(status, text="Ready", anchor="w")
        self.status_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_left.configure(font=self._fonts["small"], foreground=TEXT_SECONDARY)

        main = ttk.Frame(self.root, padding=(16, 12, 16, 8))
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(main)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        self.add_btn = ttk.Button(toolbar, text="Add", command=self._add_files)
        self.add_btn.pack(side=tk.LEFT)
        self.clear_btn = ttk.Button(toolbar, text="Clear", command=self._clear)
        self.clear_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.convert_btn = ttk.Button(
            toolbar, text="Convert", command=self._convert_clicked, default="active"
        )
        self.convert_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.settings_btn = ttk.Button(toolbar, text="Settings", command=self._open_settings)
        self.settings_btn.pack(side=tk.RIGHT)

        self.body = ttk.Frame(main)
        self.body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.drop = tk.Canvas(
            self.body,
            bg=DROP_FILL,
            highlightthickness=0,
            bd=0,
            cursor="hand2" if HAS_DND else "arrow",
        )
        self.drop.pack(fill=tk.BOTH, expand=True)
        self.drop.bind("<Configure>", lambda e: self._draw_drop())
        self.drop.bind("<Button-1>", lambda e: self._add_files())
        if HAS_DND:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self._on_drop)
            self.drop.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.drop.dnd_bind("<<DragLeave>>", self._on_drag_leave)
            try:
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind("<<Drop>>", self._on_drop)
            except tk.TclError:
                pass

        list_wrap = ttk.Frame(self.body)
        self.list_wrap = list_wrap
        list_body = ttk.Frame(list_wrap)
        list_body.pack(fill=tk.BOTH, expand=True)
        self.list_canvas = tk.Canvas(list_body, highlightthickness=0, bd=0, bg=ROW_BG)
        scroll = ttk.Scrollbar(list_body, orient="vertical", command=self.list_canvas.yview)
        self.list_inner = ttk.Frame(self.list_canvas)
        self.list_inner.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all")),
        )
        self._list_window = self.list_canvas.create_window(
            (0, 0), window=self.list_inner, anchor="nw"
        )
        self.list_canvas.configure(yscrollcommand=scroll.set)
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.list_canvas.bind("<Configure>", self._on_list_canvas_configure)
        self.list_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.list_inner.bind("<MouseWheel>", self._on_mousewheel)

        self._draw_drop()
        self._set_controls()

    def _on_list_canvas_configure(self, event: tk.Event) -> None:
        self.list_canvas.itemconfigure(self._list_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _drop_copy(self) -> tuple[str, str]:
        compact = bool(self.items)
        if not HAS_DND:
            title = "Add files to convert"
            hint = "Drag-and-drop needs tkinterdnd2. Use Add, or pip install 'mdconvert[gui]'."
            return title, hint
        if compact:
            return "Drop files to convert", "Drop starts convert"
        return "Drop files to convert", "PDF, Office, images, HTML, text, and more"

    def _draw_drop(self) -> None:
        canvas = self.drop
        canvas.delete("all")
        w = max(canvas.winfo_width(), 40)
        h = max(canvas.winfo_height(), 40)
        pad = 6
        r = 10
        active = self._drop_active
        outline = DROP_ACTIVE_DASH if active else DROP_DASH
        fill = DROP_ACTIVE_FILL if active else DROP_FILL
        canvas.configure(bg=fill)
        self._rounded_rect(
            canvas,
            pad,
            pad,
            w - pad,
            h - pad,
            r,
            dash=(6, 4),
            outline=outline,
            width=1.5,
            fill=fill,
        )
        title, hint = self._drop_copy()
        cx = w / 2
        cy = h / 2
        if self.items:
            canvas.create_text(
                cx,
                cy,
                text=title,
                fill=TEXT_SECONDARY,
                font=self._fonts["body"],
            )
        else:
            canvas.create_text(
                cx,
                cy - 11,
                text=title,
                fill=TEXT,
                font=self._fonts["drop"],
            )
            canvas.create_text(
                cx,
                cy + 13,
                text=hint,
                fill=TEXT_TERTIARY,
                font=self._fonts["small"],
                width=max(w - 48, 80),
            )

    def _rounded_rect(
        self,
        canvas: tk.Canvas,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        r: float,
        **kwargs,
    ) -> None:
        r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
        points = (
            x1 + r,
            y1,
            x2 - r,
            y1,
            x2,
            y1,
            x2,
            y1 + r,
            x2,
            y2 - r,
            x2,
            y2,
            x2 - r,
            y2,
            x1 + r,
            y2,
            x1,
            y2,
            x1,
            y2 - r,
            x1,
            y1 + r,
            x1,
            y1,
        )
        canvas.create_polygon(points, smooth=True, **kwargs)

    def _layout_list(self) -> None:
        showing = bool(self.items)
        if showing:
            if not self.list_wrap.winfo_ismapped():
                self.drop.pack_configure(fill=tk.X, expand=False)
                self.drop.configure(height=76)
                self.list_wrap.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        else:
            if self.list_wrap.winfo_ismapped():
                self.list_wrap.pack_forget()
            self.drop.configure(height=1)
            self.drop.pack_configure(fill=tk.BOTH, expand=True)
        self.root.after_idle(self._draw_drop)

    def _find(self, path: str) -> QueueItem | None:
        for item in self.items:
            if item.path == path:
                return item
        return None

    def _queued_count(self) -> int:
        return sum(1 for item in self.items if item.status == "pending")

    def _add_paths(self, paths: list[str], *, start: bool) -> None:
        changed = False
        for path in paths:
            path = path.strip()
            if not path:
                continue
            existing = self._find(path)
            if existing is not None:
                if existing.status in ("ok", "error"):
                    existing.status = "pending"
                    existing.detail = ""
                    changed = True
                continue
            self.items.append(QueueItem(path=path))
            changed = True
        if changed:
            self._render_list()
        pending = self._queued_count()
        if start and pending:
            self._start_convert()
        elif changed and not self._busy:
            n = len(self.items)
            self._set_status("1 file queued" if n == 1 else f"{n} files queued")

    def _on_drop(self, event) -> None:
        self._drop_active = False
        self._draw_drop()
        self._add_paths(split_drop_paths(event.data, self.root), start=True)

    def _on_drag_enter(self, event) -> None:
        del event
        self._drop_active = True
        self._draw_drop()

    def _on_drag_leave(self, event) -> None:
        del event
        self._drop_active = False
        self._draw_drop()

    def _add_files(self) -> None:
        chosen = filedialog.askopenfilenames(title="Select files to convert")
        if chosen:
            self._add_paths(list(chosen), start=False)

    def _clear(self) -> None:
        if self._busy:
            return
        self.items.clear()
        self._render_list()
        self._set_status("Ready")

    def _convert_clicked(self) -> None:
        if self._busy:
            return
        if not self._queued_count():
            return
        self._start_convert()

    def _render_list(self) -> None:
        for child in self.list_inner.winfo_children():
            child.destroy()
        n = len(self.items)
        for index, item in enumerate(self.items):
            self._make_row(item, show_rule=index < n - 1)
        self._layout_list()
        self._set_controls()

    def _make_row(self, item: QueueItem, *, show_rule: bool) -> None:
        row = ttk.Frame(self.list_inner)
        row.pack(fill=tk.X)
        inner = ttk.Frame(row)
        inner.pack(fill=tk.X, padx=4, pady=7)

        # Pack status first (RIGHT) so the name column keeps a stable share.
        if item.status == "ok":
            status_text, color = "Done", OK
        elif item.status == "error":
            status_text, color = "Failed", ERROR
        elif item.status == "converting":
            status_text, color = "Converting…", ACCENT
        else:
            status_text, color = "Queued", TEXT_SECONDARY
        status_lbl = ttk.Label(inner, text=status_text, anchor="e", width=12)
        status_lbl.pack(side=tk.RIGHT, padx=(12, 4))
        status_lbl.configure(font=self._fonts["small"], foreground=color)

        text_col = ttk.Frame(inner)
        text_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        name, folder = display_parts(item.path)
        name_lbl = ttk.Label(text_col, text=name, anchor="w")
        name_lbl.pack(fill=tk.X)
        name_lbl.configure(font=self._fonts["body"], foreground=TEXT)
        path_lbl = ttk.Label(text_col, text=folder, anchor="w")
        path_lbl.pack(fill=tk.X)
        path_lbl.configure(font=self._fonts["small"], foreground=TEXT_TERTIARY)
        if item.status == "error" and item.detail:
            err_lbl = ttk.Label(
                text_col,
                text=short_error(item.detail),
                anchor="w",
                wraplength=420,
                justify="left",
            )
            err_lbl.pack(fill=tk.X, pady=(2, 0))
            err_lbl.configure(font=self._fonts["small"], foreground=ERROR)
        if show_rule:
            ttk.Separator(row, orient="horizontal").pack(fill=tk.X, padx=4)

    def _set_controls(self) -> None:
        queued = self._queued_count() > 0
        convert_state = "disabled" if self._busy or not queued else "normal"
        clear_state = "disabled" if self._busy or not self.items else "normal"
        try:
            self.convert_btn.configure(state=convert_state)
            self.clear_btn.configure(state=clear_state)
        except tk.TclError:
            pass

    def _status_style(self, text: str) -> tuple[str, str]:
        """Return (foreground, optional subtle status meaning) for the bar."""
        lower = text.lower()
        if "fail" in lower or "error" in lower:
            return ERROR, "error"
        if lower.startswith("converting"):
            return ACCENT, "busy"
        if lower.startswith("converted") or lower.startswith("done"):
            return OK, "ok"
        return TEXT_SECONDARY, "idle"

    def _set_status(self, text: str) -> None:
        color, _kind = self._status_style(text)
        self.status_left.configure(text=text, foreground=color)

    def _ui(self, fn) -> None:
        def wrapped() -> None:
            try:
                if not self.root.winfo_exists():
                    return
                fn()
            except tk.TclError:
                return

        self.root.after(0, wrapped)

    def _start_convert(self, *, new_run: bool = True) -> None:
        if self._busy:
            return
        pending = [item for item in self.items if item.status == "pending"]
        if not pending:
            return
        output = self.config.output_dir or str(Path.cwd())
        options = ConvertOptions(
            output_dir=output,
            ocr_mode=self.config.ocr,
            ocr_engine=self.config.ocr_engine,
            force=True,
        )
        if new_run:
            self._run_ok = 0
            self._run_fail = 0
        self._busy = True
        self._set_controls()
        snapshot = list(pending)
        already = self._run_ok + self._run_fail
        total = already + len(snapshot)

        def work() -> None:
            for index, item in enumerate(snapshot, start=1):
                position = already + index

                def mark_busy(it=item, i=position, n=total) -> None:
                    it.status = "converting"
                    it.detail = ""
                    self._render_list()
                    self._set_status(f"Converting {i} of {n}…")

                self._ui(mark_busy)
                try:
                    convert_file(item.path, options)
                except (SanitizeError, ConvertError, OSError, ValueError) as exc:
                    detail = short_error(exc)

                    def mark_err(it=item, msg=detail) -> None:
                        it.status = "error"
                        it.detail = msg
                        self._run_fail += 1
                        self._render_list()

                    self._ui(mark_err)
                else:

                    def mark_ok(it=item) -> None:
                        it.status = "ok"
                        it.detail = ""
                        self._run_ok += 1
                        self._render_list()

                    self._ui(mark_ok)

            def done() -> None:
                leftover = [item for item in self.items if item.status == "pending"]
                if leftover:
                    self._busy = False
                    self._start_convert(new_run=False)
                    return
                self._busy = False
                self._set_controls()
                self._set_status(format_done_status(self._run_ok, self._run_fail))

            self._ui(done)

        threading.Thread(target=work, daemon=True).start()

    def _open_settings(self) -> None:
        if self._settings_win is not None and self._settings_win.winfo_exists():
            self._settings_win.lift()
            self._settings_win.focus_force()
            return

        win = tk.Toplevel(self.root)
        self._settings_win = win
        win.title("Settings")
        win.transient(self.root)
        win.resizable(False, False)
        if sys.platform == "darwin":
            try:
                win.tk.call(
                    "::tk::unsupported::MacWindowStyle",
                    "style",
                    win._w,
                    "moveableModal",
                )
            except tk.TclError:
                pass

        pad = ttk.Frame(win, padding=(20, 16))
        pad.pack(fill=tk.BOTH, expand=True)

        ttk.Label(pad, text="Settings", font=self._fonts["body_bold"]).pack(anchor="w")
        hint = ttk.Label(pad, text="Used for the next convert.")
        hint.pack(anchor="w", pady=(0, 14))
        hint.configure(font=self._fonts["small"], foreground=TEXT_TERTIARY)

        ttk.Label(pad, text="Output folder", font=self._fonts["body_bold"]).pack(anchor="w")
        out_row = ttk.Frame(pad)
        out_row.pack(fill=tk.X, pady=(6, 4))
        out_var = tk.StringVar(value=self.config.output_dir)
        out_entry = ttk.Entry(out_row, textvariable=out_var, width=36)
        out_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def browse() -> None:
            chosen = filedialog.askdirectory(title="Markdown output directory")
            if chosen:
                out_var.set(chosen)

        ttk.Button(out_row, text="Choose…", command=browse).pack(side=tk.LEFT, padx=(8, 0))
        out_hint = ttk.Label(
            pad,
            text="Leave empty to write in the current working directory.",
            wraplength=420,
            justify="left",
        )
        out_hint.pack(fill=tk.X, pady=(0, 14))
        out_hint.configure(font=self._fonts["small"], foreground=TEXT_TERTIARY)

        ttk.Label(pad, text="OCR mode", font=self._fonts["body_bold"]).pack(anchor="w")
        ocr_var = tk.StringVar(value=self.config.ocr)
        ocr_labels = {
            "auto": "Auto — scanned PDFs and images",
            "always": "Always — images and PDFs",
            "never": "Never — skip OCR",
        }
        for mode in OCR_MODES:
            ttk.Radiobutton(
                pad,
                text=ocr_labels[mode],
                value=mode,
                variable=ocr_var,
            ).pack(anchor="w", pady=2)

        ttk.Label(pad, text="OCR engine", font=self._fonts["body_bold"]).pack(
            anchor="w", pady=(12, 0)
        )
        engine_var = tk.StringVar(value=self.config.ocr_engine)
        engine_labels = {
            "rapidocr": "RapidOCR — local, no Tesseract",
            "tesseract": "Tesseract — system binary",
        }
        for engine in OCR_ENGINES:
            ttk.Radiobutton(
                pad,
                text=engine_labels[engine],
                value=engine,
                variable=engine_var,
            ).pack(anchor="w", pady=2)

        btns = ttk.Frame(pad)
        btns.pack(fill=tk.X, pady=(18, 0))

        def close() -> None:
            win.destroy()
            self._settings_win = None

        def save() -> None:
            self.config = AppConfig(
                output_dir=out_var.get().strip(),
                ocr=ocr_var.get(),
                ocr_engine=engine_var.get(),
            )
            save_config(self.config)
            close()

        ttk.Button(btns, text="Done", command=save, default="active").pack(side=tk.RIGHT)
        ttk.Button(btns, text="Cancel", command=close).pack(side=tk.RIGHT, padx=(0, 8))

        win.protocol("WM_DELETE_WINDOW", close)
        win.update_idletasks()
        try:
            bx = self.settings_btn.winfo_rootx()
            by = self.settings_btn.winfo_rooty() + self.settings_btn.winfo_height()
            ww = win.winfo_width()
            bw = self.settings_btn.winfo_width()
            win.geometry(f"+{bx + bw - ww}+{by + 8}")
        except tk.TclError:
            pass
        out_entry.focus_set()


def main(argv: list[str] | None = None) -> int:
    del argv
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    MdconvertApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
