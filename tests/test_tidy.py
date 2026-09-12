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


def test_hyphenation_at_line_end_is_removed() -> None:
    assert tidy_markdown("some hy-\nphenation here\n") == "some hyphenation here\n"
    assert tidy_markdown("soft­\nhyphen\n") == "softhyphen\n"


def test_compound_hyphens_stay() -> None:
    assert tidy_markdown("Nord-\nSüd\n") == "Nord-Süd\n"
    assert tidy_markdown("2019-\n2020\n") == "2019-2020\n"
    assert tidy_markdown("Vor-\nund Nachteile\n") == "Vor- und Nachteile\n"
    assert tidy_markdown("pre-\nand post-war\n") == "pre- and post-war\n"


def test_dash_after_a_space_is_not_hyphenation() -> None:
    assert tidy_markdown("a range -\nthe rest\n") == "a range - the rest\n"
    assert tidy_markdown("a **bold-**\nword\n") == "a **bold-** word\n"


def test_word_cut_at_page_break_joins_across_blank_line() -> None:
    assert tidy_markdown("Der Vorschlag ent-\n\nspricht dem.\n") == "Der Vorschlag entspricht dem.\n"
    assert tidy_markdown("Der Vorschlag ent-\n\n\n\nspricht dem.\n") == "Der Vorschlag entspricht dem.\n"
    # The next paragraph does not start with a lower-case letter: keep both.
    assert tidy_markdown("Ende mit EU-\n\nDie nächste.\n") == "Ende mit EU-\n\nDie nächste.\n"
    # A list item or other block after the blank line is never glued on.
    assert tidy_markdown("Ende mit ent-\n\n- item\n") == "Ende mit ent-\n\n- item\n"
    # Code before the blank line is not a paragraph.
    assert tidy_markdown("```\nx-\n```\n\nyz\n") == "```\nx-\n```\n\nyz\n"
