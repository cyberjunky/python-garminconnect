# Contributing

Thanks for helping improve python-garminconnect. This page explains how to set
up a development environment, what CI checks, and what a pull request needs.

Found a security problem? Don't open a public issue. Report it privately as
described in [SECURITY.md](SECURITY.md).

## Development setup

```bash
git clone https://github.com/cyberjunky/python-garminconnect.git
cd python-garminconnect
python3 -m venv .venv --copies
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install pdm
python3 -m pdm install --group :all
pre-commit install --install-hooks
```

The pre-commit hooks run ruff, ruff-format, mypy, codespell and gitleaks on
each commit. If a hook reformats a file, stage the change and commit again.

## Checks

CI runs these on Python 3.12, 3.13 and 3.14. Run them before you push:

```bash
pdm run ruff check .
pdm run ruff format --check .
pdm run mypy garminconnect --ignore-missing-imports
pdm run pytest tests/ -v --tb=short --vcr-record=none
```

CI also runs `bandit` and `pip-audit`. Ruff formats Python code blocks in
Markdown files too, so examples in `README.md` must be ruff-formatted.

The default test run never contacts Garmin. Unit tests mock
`Garmin.connectapi` (see `tests/test_garmin_unit.py`). The tests in
`tests/test_garmin.py` are marked `integration`: they need a real account or a
private VCR recording, and are skipped unless you run `pytest -m integration`.

## Adding or changing an API method

1. **Add the method to `Garmin`** in `garminconnect/__init__.py`, next to
   related methods, with a docstring that says what it returns.
2. **Validate every input before it goes into a URL or payload.** Use the
   existing helpers: `_coerce_positive_id` for IDs, `_validate_date_format` and
   `_validate_date_range` for dates, `_validate_uuid`, `_validate_sport_key`,
   and so on. Don't call `int()` on an ID yourself, because that rounds
   `1.9` down to `1`.
3. **Don't log or raise sensitive data.** Log messages and exception text must
   not contain response bodies, tokens, tickets, cookies, passwords or account
   details. Log the status code instead.
4. **Base write endpoints on a real request.** Copy the URL, method and payload
   from a request the Garmin Connect web or mobile app actually sends, then
   check the result live by reading the object back after the write. Say in the
   PR how you tested it.
5. **Add tests** that check the URL, parameters and payload, plus the inputs
   that must be rejected. Use mocks or cassettes, not a live account.
6. **Add it to `demo.py`.** Add an entry to the matching category in
   `menu_categories` and a matching key in the `execute_api_call` dispatch
   table. Write methods get a prompt for each input, like the existing ones.
7. **Update `README.md`.** Run `python3 scripts/gen_method_reference.py` to
   regenerate the method reference from the docstrings (a test fails when it
   is out of date), so give the method a docstring whose first sentence says
   what it does. Recompute the method and category counts from
   `menu_categories` in `demo.py`, and document new behavior that callers need
   to know about.

## Pull requests

- Keep each PR to one change, and branch from `master`.
- Describe what changed, why, and how you tested it. For bug fixes, link the
  issue.
- Add a line under the unreleased version in [CHANGELOG.md](CHANGELOG.md) for
  any change users will notice.
- Expect review comments from the maintainer and from CodeRabbit. Fork PRs
  need the maintainer to approve the CI run before it starts.
