#!/usr/bin/env python3
"""Regenerate ``garminconnect/exercises.py`` from the Garmin exercise picker.

The strength-exercise catalog is static data scraped from the Garmin Connect
workout editor's exercise picker.  To refresh it:

1. Open the workout editor at https://connect.garmin.com, add a strength
   exercise, and open the exercise picker.
2. Copy only the picker's ``<ul>`` HTML into a file.  Do not paste the
   whole page: it comes from an authenticated session and may contain
   account data, and the generated file is published to a public
   repository.
3. Run::

       python scripts/generate_exercises.py path/to/picker.html

Each selectable exercise is a ``<li role="option" ...>`` carrying
``data-category-key`` (movement group) and ``data-exercise-key`` (specific
variant) plus a display label.  Equipment/muscle-group filters are loaded
client-side and are not present in the HTML, so they are not extracted.
"""

from __future__ import annotations

import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "garminconnect" / "exercises.py"


class _PickerParser(HTMLParser):
    """Collect (category, exercise, name) rows, each scoped to its own <li>.

    Regex extraction with DOTALL can reach past an element boundary and
    capture a <span> from unrelated page chrome; a real parser cannot, and
    it also keeps items separate when a closing </li> is omitted.
    """

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[tuple[str, str, str]] = []
        self._cur: list[str | None] | None = None
        self._in_span = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "li":
            # An unclosed previous <li> ends here, not at its </li>.
            self._flush()
            if "data-category-key" in a and "data-exercise-key" in a:
                self._cur = [a["data-category-key"], a["data-exercise-key"], None]
        elif tag == "span" and self._cur is not None and self._cur[2] is None:
            self._in_span = True

    def handle_data(self, data: str) -> None:
        # A nested tag inside the span (e.g. <b>) triggers another
        # handle_data call for its own text; accumulate rather than
        # overwrite, or a fragment like the "https://" prefix of a stray
        # URL is dropped and the SUSPECT filter never sees it.
        if self._in_span and self._cur is not None:
            self._cur[2] = (self._cur[2] or "") + data

    def handle_endtag(self, tag: str) -> None:
        if tag == "span":
            self._in_span = False
        elif tag == "li" and self._cur is not None:
            self._flush()

    def _flush(self) -> None:
        # Attribute-only element (no span of its own): skip rather than
        # borrowing text from elsewhere in the document.
        if self._cur is not None and self._cur[2]:
            self.rows.append((self._cur[0] or "", self._cur[1] or "", self._cur[2]))
        self._cur = None
        self._in_span = False


# Names are display labels; anything shaped like session data means the
# extraction went out of scope (or the wrong HTML was pasted).
SUSPECT = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.]+"  # e-mail address
    r"|eyJ[\w-]{10,}"  # JWT
    r"|https?://"  # URL
    r"|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}",  # GUID
    re.IGNORECASE,
)


def parse(text: str) -> list[dict[str, str]]:
    """Extract unique (name, category, exercise) rows from picker HTML."""
    parser = _PickerParser()
    parser.feed(text)
    parser.close()
    # HTMLParser.close() doesn't synthesize a missing </li>, so the last
    # item (if the source HTML omits its closing tag) needs an explicit
    # flush here.
    parser._flush()
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for category, exercise, name in parser.rows:
        key = (category, exercise)
        if key in seen:
            continue  # the "Recent" block repeats items listed below
        seen.add(key)
        out.append(
            {
                "name": html.unescape(name).strip(),
                "category": category,
                "exercise": exercise,
            }
        )
    out.sort(key=lambda e: (e["category"], e["name"].lower()))
    return out


def render(exercises: list[dict[str, str]]) -> str:
    """Render the exercises as the ``garminconnect/exercises.py`` module source."""
    categories = sorted({e["category"] for e in exercises})
    lines = [
        '"""Garmin Connect strength-exercise catalog.',
        "",
        "Every selectable strength exercise from the Garmin Connect workout editor,",
        "with the ``category`` (movement/muscle group) and ``exercise`` (specific",
        "variant) enum values a strength workout step needs.  Use these with",
        "``create_strength_exercise_step`` / ``create_strength_set``.",
        "",
        f"Contains {len(exercises)} exercises across {len(categories)} categories.",
        "Regenerate with ``scripts/generate_exercises.py``.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "# Raw catalog rows as (display name, category, exercise) tuples.",
        '# ``exercise`` may be "" (the workout shows only the category name).',
        "_RAW: list[tuple[str, str, str]] = [",
    ]
    lines += [
        f"    ({e['name']!r}, {e['category']!r}, {e['exercise']!r})," for e in exercises
    ]
    lines += [
        "]",
        "",
        "# name -> {category, exercise}.",
        "EXERCISES: list[dict[str, str]] = [",
        '    {"name": name, "category": category, "exercise": exercise}',
        "    for name, category, exercise in _RAW",
        "]",
        "",
        "# Lookup by exact display name.",
        'BY_NAME: dict[str, dict[str, str]] = {e["name"]: e for e in EXERCISES}',
        "",
        "# All distinct exercise categories (movement/muscle groups).",
        f"CATEGORIES: list[str] = {categories!r}",
        "",
        "",
        "def resolve(name: str) -> dict[str, str] | None:",
        '    """Return the catalog entry for an exact display name, or None."""',
        "    return BY_NAME.get(name)",
        "",
        "",
        "def find(term: str) -> list[dict[str, str]]:",
        '    """Return exercises whose display name contains ``term`` (case-insensitive)."""',
        "    needle = term.lower()",
        '    return [e for e in EXERCISES if needle in e["name"].lower()]',
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/generate_exercises.py <picker.html>")
    exercises = parse(Path(sys.argv[1]).read_text(encoding="utf-8"))
    suspect = [i for i, e in enumerate(exercises) if SUSPECT.search(e["name"])]
    if suspect:
        # Report only row positions — the matched labels are exactly the
        # potentially sensitive text we refuse to write out.
        sys.exit(
            f"refusing to write: {len(suspect)} entr{'ies' if len(suspect) != 1 else 'y'} "
            "look like session data, not exercise names (rows "
            f"{suspect}; check the pasted HTML)"
        )
    OUT.write_text(render(exercises), encoding="utf-8")
    print(f"Wrote {len(exercises)} exercises to {OUT}")
    print("Run `pdm run format` to normalize quoting/formatting.")


if __name__ == "__main__":
    main()
