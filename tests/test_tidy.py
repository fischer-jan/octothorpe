from pathlib import Path

from octothorpe.tidy import tidy_markdown

FIXTURES = Path(__file__).parent / "fixtures"


def test_golden() -> None:
    source = (FIXTURES / "tidy_input.md").read_text(encoding="utf-8")
    expected = (FIXTURES / "tidy_expected.md").read_text(encoding="utf-8")
    assert tidy_markdown(source) == expected


def test_idempotent() -> None:
    expected = (FIXTURES / "tidy_expected.md").read_text(encoding="utf-8")
    assert tidy_markdown(expected) == expected


def test_empty_and_whitespace_only() -> None:
    assert tidy_markdown("") == ""
    assert tidy_markdown("\n\n  \n") == ""


def test_page_breaks_and_crlf_from_pdf_extraction() -> None:
    text = "Line one\r\nline two\r\n\x0c\r\nNext page\r\n"
    assert tidy_markdown(text) == "Line one line two\n\nNext page\n"


def test_unterminated_fence_is_left_alone() -> None:
    text = "```\nraw\nlines\n"
    assert tidy_markdown(text) == "```\nraw\nlines\n"


def test_emphasis_is_not_mistaken_for_a_list() -> None:
    assert tidy_markdown("Some text\n*emphasis* continues\n") == "Some text *emphasis* continues\n"
    assert tidy_markdown("Some text\n**bold** continues\n") == "Some text **bold** continues\n"
