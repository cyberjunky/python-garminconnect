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


def test_main_refuses_suspect_names(gen, tmp_path, monkeypatch, capsys):
    html_file = tmp_path / "picker.html"
    html_file.write_text(
        '<li data-category-key="X" data-exercise-key="Y">'
        "<span>user@example.com</span></li>"
    )
    monkeypatch.setattr("sys.argv", ["generate_exercises.py", str(html_file)])
    with pytest.raises(SystemExit, match="session data"):
        gen.main()
