"""Remove line breaks that Markdown would not render anyway.

CommonMark renders a single newline inside a paragraph as a space, so a
hard-wrapped paragraph and a one-line paragraph look the same. MarkItDown
(and PDF extraction in particular) produces hard-wrapped text. This module
joins such lines and collapses runs of blank lines to one. When a line ends
in a hyphenated word fragment ("hy-" / "phenation"), the join also removes the
hyphen, so PDF hyphenation does not survive as "hy- phenation". A word cut
at a page or column break has a blank line inside it; when the next paragraph
then starts with a lower-case letter, the two paragraphs are joined as well.

It leaves alone everything where a newline matters: fenced and indented code,
tables, headings, list markers, block quotes, HTML blocks, hard line breaks
(two trailing spaces or a backslash), setext underlines, horizontal rules,
link reference definitions, and YAML front matter.
"""

from __future__ import annotations

import re

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,}|\${2})")
_HEADING = re.compile(r"^ {0,3}#{1,6}(\s|$)")
_BULLET = re.compile(r"^\s*[-*+](\s|$)")
_ORDERED = re.compile(r"^\s*\d{1,9}[.)](\s|$)")
_QUOTE = re.compile(r"^ {0,3}>")
_TABLE = re.compile(r"^\s*\|")
_HR = re.compile(r"^ {0,3}([-*_])(\s*\1){2,}\s*$")
_SETEXT = re.compile(r"^ {0,3}(=+|-+)\s*$")
_HTML = re.compile(r"^ {0,3}<")
_LINK_DEF = re.compile(r"^ {0,3}\[[^\]]+\]:\s")
_INDENTED = re.compile(r"^( {4,}|\t)")
_FOOTNOTE = re.compile(r"^ {0,3}\[\^[^\]]+\]:")
_FRONT_MATTER = re.compile(r"^(---|\+\+\+)\s*$")
# A word cut by a hyphen (or soft hyphen) at the end of a line.
_HYPHEN_END = re.compile(r"\w[-\u00ad]$")
# Suspended hyphens keep their hyphen: "pre- and post-war", "Vor- und Nachteile".
_SUSPENDED = re.compile(r"^(and|or|nor|und|oder|bzw\.?)(\W|$)", re.IGNORECASE)


def _starts_block(line: str) -> bool:
    """True if this line begins a construct that must not be glued to the line above."""
    return any(
        p.match(line)
        for p in (
            _FENCE, _HEADING, _BULLET, _ORDERED, _QUOTE, _TABLE, _HR,
            _SETEXT, _HTML, _LINK_DEF, _FOOTNOTE,
        )
    )


def _continues_paragraph(line: str) -> bool:
    """True if plain text may be glued onto the end of this line."""
    return not any(
        p.match(line)
        for p in (_HEADING, _QUOTE, _TABLE, _HR, _SETEXT, _HTML, _LINK_DEF, _FOOTNOTE)
    )


def _hard_break(line: str) -> bool:
    return line.endswith("  ") or line.endswith("\\")


def _join(prev: str, line: str) -> str:
    """Glue a continuation line onto the paragraph line above it.

    A hyphen at the end of the line is PDF hyphenation when the next line
    starts with a lower-case letter: drop it. Before a capital or a digit the
    hyphen is part of a compound ("Nord-Süd", "2019-2020"): keep it, but do
    not add a space. Everything else joins with a space.
    """
    prev = prev.rstrip()
    line = line.lstrip()
    if _HYPHEN_END.search(prev) and line and line[0].isalnum() and not _SUSPENDED.match(line):
        if line[0].islower() or prev.endswith("\u00ad"):
            return prev[:-1] + line
        return prev + line
    return prev + " " + line


def _cut_word(prev: str, line: str) -> bool:
    """True if a blank line falls inside a hyphenated word (page or column break)."""
    line = line.lstrip()
    return bool(
        _HYPHEN_END.search(prev.rstrip())
        and line
        and line[0].islower()
        and not _SUSPENDED.match(line)
    )


def tidy_markdown(text: str) -> str:
    """Join hard-wrapped paragraph lines and collapse blank lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "\n")
    lines = text.split("\n")
    out: list[str] = []
    para_open = False       # the last output line accepts plain-text continuation
    pending_blank = False
    cut_word = False        # the paragraph before the blank line ends mid-word
    in_fence: str | None = None
    in_front_matter = False

    for i, line in enumerate(lines):
        if i == 0 and _FRONT_MATTER.match(line):
            in_front_matter = True
            out.append(line)
            continue
        if in_front_matter:
            out.append(line)
            if _FRONT_MATTER.match(line):
                in_front_matter = False
            continue

        fence = _FENCE.match(line)
        if in_fence:
            out.append(line)
            if fence and fence.group(1)[0] == in_fence[0] and len(fence.group(1)) >= len(in_fence):
                in_fence = None
            continue
        if fence:
            if pending_blank and out:
                out.append("")
            pending_blank = False
            in_fence = fence.group(1)
            out.append(line)
            para_open = False
            cut_word = False
            continue

        if not line.strip():
            pending_blank = bool(out)
            # A paragraph that stops mid-word may continue after the blank line.
            if para_open:
                cut_word = bool(_HYPHEN_END.search(out[-1].rstrip()))
            para_open = False
            continue

        if para_open and not _starts_block(line) and not _hard_break(out[-1]):
            out[-1] = _join(out[-1], line)
            continue

        if pending_blank and cut_word and not _starts_block(line) and _cut_word(out[-1], line):
            out[-1] = _join(out[-1], line)
            pending_blank = False
            cut_word = False
            para_open = True
            continue

        if pending_blank:
            out.append("")
            pending_blank = False
        cut_word = False
        out.append(line)
        # After a blank line an indented line is a code block; keep it verbatim.
        para_open = _continues_paragraph(line) and not _INDENTED.match(line)

    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out) + ("\n" if out else "")
