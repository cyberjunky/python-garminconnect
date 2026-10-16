"""Generate the README method reference from the Garmin class.

Every public ``Garmin`` method is listed under the domain module that defines
it, with its parameters and the first line of its docstring. The list goes
between the ``METHODS:START`` / ``METHODS:END`` markers in README.md.

Usage:
    python3 scripts/gen_method_reference.py          # rewrite README.md
    python3 scripts/gen_method_reference.py --check  # exit 1 if out of date
"""

import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from garminconnect import Garmin  # noqa: E402

README = ROOT / "README.md"
START = "<!-- METHODS:START -->"
END = "<!-- METHODS:END -->"

# Domain module -> heading, in the order the sections appear.
SECTIONS = {
    "base": "Login, profile & account",
    "health": "Daily health & wellness",
    "metrics": "Performance metrics",
    "body": "Weight, body composition & blood pressure",
    "activities": "Activities",
    "workouts": "Workouts",
    "training": "Training plans, calendar, courses & reports",
    "achievements": "Goals, badges & challenges",
    "devices": "Devices",
    "gear": "Gear",
    "womens_health": "Women's health",
    "golf": "Golf",
}

MAX_OPTIONAL_SHOWN = 3


def _signature(func: object) -> str:
    """Render parameters compactly: required names, then a few defaults."""
    params = list(inspect.signature(func).parameters.values())[1:]  # type: ignore[arg-type]
    parts: list[str] = []
    optional = 0
    for p in params:
        if p.kind is p.VAR_POSITIONAL:
            parts.append(f"*{p.name}")
        elif p.kind is p.VAR_KEYWORD:
            parts.append(f"**{p.name}")
        elif p.default is inspect.Parameter.empty:
            parts.append(p.name)
        else:
            optional += 1
            if optional <= MAX_OPTIONAL_SHOWN:
                parts.append(f"{p.name}={p.default!r}")
    if optional > MAX_OPTIONAL_SHOWN:
        parts.append("…")
    return ", ".join(parts)


def _summary(func: object) -> str:
    """First sentence of the docstring's first paragraph, as Markdown."""
    doc = (inspect.getdoc(func) or "").strip()
    lines = []
    for line in doc.split("\n\n", 1)[0].splitlines():
        if line.lstrip().startswith((":", "Args:", "Returns:", "Raises:")):
            break  # parameter docs follow the summary without a blank line
        lines.append(line)
    paragraph = " ".join(" ".join(lines).split())
    # Don't end the sentence at an abbreviation such as "e.g." or "vs.".
    sentence = re.split(
        r"(?<!\be\.g\.)(?<!\bi\.e\.)(?<!\bincl\.)(?<!\bvs\.)(?<!\betc\.)(?<=[.!?])\s",
        paragraph,
        maxsplit=1,
    )[0]
    return sentence.replace("``", "`").replace("|", "\\|")


def render() -> str:
    """Return the Markdown that belongs between the README markers."""
    by_module: dict[str, list[tuple[str, object]]] = {}
    for name, func in inspect.getmembers(Garmin, inspect.isfunction):
        if name.startswith("_"):
            continue
        module = func.__module__.rsplit(".", 1)[-1]
        by_module.setdefault(module, []).append((name, func))

    unknown = sorted(set(by_module) - set(SECTIONS))
    if unknown:
        raise SystemExit(f"Add a heading for module(s) {unknown} to SECTIONS")

    total = sum(len(v) for v in by_module.values())
    lines = [
        f"{total} public methods on `Garmin`, generated from the code by "
        "`scripts/gen_method_reference.py`. Click a section to expand it.",
        "",
    ]
    for module, title in SECTIONS.items():
        methods = sorted(by_module.get(module, []))
        if not methods:
            continue
        lines += [
            f"<details><summary><b>{title}</b> ({len(methods)})</summary>",
            "",
            "| Method | Description |",
            "| --- | --- |",
        ]
        for name, func in methods:
            sig = _signature(func).replace("|", "\\|")
            lines.append(f"| `{name}({sig})` | {_summary(func)} |")
        lines += ["", "</details>", ""]
    return "\n".join(lines).rstrip() + "\n"


def _replace_block(text: str, block: str) -> str:
    head, sep, rest = text.partition(START)
    if not sep or END not in rest:
        raise SystemExit(f"README.md must contain {START} and {END}")
    _, _, tail = rest.partition(END)
    return f"{head}{START}\n{block}{END}{tail}"


def main() -> int:
    text = README.read_text(encoding="utf-8")
    new = _replace_block(text, render())
    if "--check" in sys.argv:
        if new != text:
            print("README method reference is out of date; run")
            print("  python3 scripts/gen_method_reference.py")
            return 1
        return 0
    README.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
