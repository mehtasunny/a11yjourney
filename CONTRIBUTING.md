# Contributing

Thanks for helping make mobile apps more accessible.

## Ground rules
- Keep the core dependency-free. Model integrations go behind the `Judge` seam.
- Every check maps to a specific WCAG success criterion in `wcag.py`, with
  its level and the WCAG version that introduced it.
- Do not overstate. If a check estimates, mark the finding for review; if an
  input is unusable, skip the check and add a note rather than guess.
- Add or update a test for any behavior you change.
- Run the full local check before opening a PR.

## Local setup
```bash
pip install -e ".[dev]"
ruff check .
mypy
pytest -q
python benchmark/run.py
```

## Reporting
Use the issue templates. For a false positive, include the smallest
accessibility-tree snippet that reproduces it.

Never attach captures or screenshots that show real personal data. Reproduce
with a test account or edit the text out of the XML first.
