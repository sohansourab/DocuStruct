# Contributing to DocuStruct

Thanks for your interest in contributing! This project is offline-first and CPU-only —
please keep that constraint in mind for any new dependency or feature.

## Getting Started

```bash
git clone https://code.swecha.org/Sohansourab27/docustruct.git
cd docustruct
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pre-commit ruff mypy bandit vulture pip-audit
pre-commit install
```

## Development Workflow

1. Create a branch off `main`: `git checkout -b feature/short-description`.
2. Make your changes, keeping functions small and typed where practical.
3. Run the local checks before committing:
   ```bash
   ruff check .
   mypy .
   bandit -r . -x tests,.venv
   vulture . --min-confidence 80
   pytest --cov
   ```
4. Stage your changes and commit — pre-commit hooks only scan **staged** files, so
   run `git add` before `git commit`.
5. Push your branch and open a Merge Request against `main`.

## Commit Messages

Use short, imperative commit messages (e.g. `Add retry logic to OCR ingest`).
Conventional Commit prefixes (`feat:`, `fix:`, `docs:`, `chore:`) are encouraged since
the changelog is generated automatically from commit history.

## Code Style

- Formatting/linting is enforced by `ruff`.
- Type hints are checked with `mypy`.
- Dead code is flagged by `vulture`.
- Security issues are flagged by `bandit` and `semgrep`.

## Tests

New features and bug fixes should include tests under `tests/`. Run the full suite with:

```bash
pytest --cov=. --cov-report=term-missing
```

## Reporting Issues

Use the GitLab issue tracker. For security vulnerabilities, see `SECURITY.md` instead of
opening a public issue.
