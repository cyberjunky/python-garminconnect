"""The README method reference must match the Garmin class."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "gen_method_reference.py"


def test_readme_method_reference_is_current():
    spec = importlib.util.spec_from_file_location("gen_method_reference", SCRIPT)
    assert spec is not None and spec.loader is not None
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    readme = gen.README.read_text(encoding="utf-8")
    assert gen._replace_block(readme, gen.render()) == readme, (
        "README method reference is out of date; run "
        "python3 scripts/gen_method_reference.py"
    )
