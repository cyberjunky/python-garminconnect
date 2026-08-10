"""Regression tests for scripts/generate_exercises.py (report #4024)."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def gen():
    spec = importlib.util.spec_from_file_location(
        "generate_exercises",
        Path(__file__).parent.parent / "scripts" / "generate_exercises.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PAGE = """<html><body>
  <div class="user-header">
    <span>user@example.com</span>
  </div>
  <ul id="picker">
    <li role="option" data-category-key="SQUAT" data-exercise-key="BACK_SQUAT"><span>Back Squat</span></li>
    <li role="option" data-category-key="LEAK" data-exercise-key="NO_SPAN_HERE"></li>
  </ul>
  <footer><span>JWT_WEB=eyJhbGciOi.FAKE.TOKEN</span></footer>
</body></html>"""


def test_parse_does_not_capture_span_outside_element(gen):
    rows = gen.parse(PAGE)
    assert rows == [
        {"name": "Back Squat", "category": "SQUAT", "exercise": "BACK_SQUAT"}
    ]


def test_parse_keeps_unclosed_items_separate(gen):
    # No </li> after the first item: the next <li> start tag is the
    # boundary, so the attribute-only item must not merge with (or borrow
    # the span of) the following one.
    rows = gen.parse(
        '<li data-category-key="LEAK" data-exercise-key="NO_SPAN">\n'
        '<li data-category-key="X" data-exercise-key="Y">'
        "<span>user@example.com</span></li>"
    )
    assert rows == [
        {"name": "user@example.com", "category": "X", "exercise": "Y"}
    ]


def test_main_refuses_suspect_names(gen, tmp_path, monkeypatch, capsys):
    html_file = tmp_path / "picker.html"
    html_file.write_text(
        '<li data-category-key="X" data-exercise-key="Y">'
        "<span>user@example.com</span></li>"
    )
    monkeypatch.setattr("sys.argv", ["generate_exercises.py", str(html_file)])
    with pytest.raises(SystemExit) as exc_info:
        gen.main()
    # The refusal must name positions only, never the suspected text.
    assert "user@example.com" not in str(exc_info.value)
    assert "session data" in str(exc_info.value)


@pytest.mark.parametrize(
    "label",
    [
        "see HTTPS://EXAMPLE.COM/x",  # uppercase URL scheme
        "id 9F8E7D6C-5B4A-4C3D-8E9F-0A1B2C3D4E5F",  # uppercase GUID
    ],
)
def test_suspect_regex_is_case_insensitive(gen, label):
    assert gen.SUSPECT.search(label)


def test_parse_accumulates_text_across_nested_tags(gen):
    # A nested <b> inside the span splits the label into two handle_data
    # calls; the "https://" prefix must not be dropped, or the SUSPECT
    # filter never sees the full (sensitive) label.
    rows = gen.parse(
        '<li data-category-key="X" data-exercise-key="Y">'
        "<span>https://host/<b>?ticket=secret</b></span></li>"
    )
    assert rows == [
        {
            "name": "https://host/?ticket=secret",
            "category": "X",
            "exercise": "Y",
        }
    ]
    assert gen.SUSPECT.search(rows[0]["name"])


def test_parse_flushes_final_item_without_closing_tag(gen):
    # HTMLParser.close() does not synthesize a missing </li>; the last
    # item in the source HTML must still be captured.
    rows = gen.parse(
        '<ul><li data-category-key="SQUAT" data-exercise-key="BACK_SQUAT">'
        "<span>Back Squat</span>"
    )
    assert rows == [
        {"name": "Back Squat", "category": "SQUAT", "exercise": "BACK_SQUAT"}
    ]


def test_parse_keeps_capturing_after_nested_span_closes(gen):
    # A plain in/out flag drops back "out of span" on the inner </span>,
    # losing text that follows it but is still inside the outer span.
    rows = gen.parse(
        '<li data-category-key="SQUAT" data-exercise-key="BACK_SQUAT">'
        "<span><span>Back</span> Squat</span></li>"
    )
    assert rows == [
        {"name": "Back Squat", "category": "SQUAT", "exercise": "BACK_SQUAT"}
    ]
