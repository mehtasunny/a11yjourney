# Contributing

Thanks for helping make mobile apps more accessible.

## Ground rules
- Keep the core dependency-free. Model integrations go behind the `Judge` seam.
- Every check maps to a specific WCAG success criterion in `wcag.py`.
- Add or update a test for any behavior you change.
- Run the full local check before opening a PR.

## Local setup
```bash
pip install -e ".[dev]"
ruff check .
mypy
pytest -q
```

## Reporting
Use the issue templates. For a false positive, include the smallest
accessibility-tree snippet that reproduces it.
