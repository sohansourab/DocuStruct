# AGENTS.md

Guidance for AI coding agents (Claude, Copilot, etc.) working in this repository.

## Project Summary

DocuStruct is an offline-first, CPU-only pipeline that converts receipt/invoice images
into structured JSON and SQLite rows via OCR + rule-based/LLM extraction.

## Key Entry Points

- `app.py` — CLI entry point.
- `streamlit_app.py` — Streamlit UI entry point.
- `pipeline.py` — shared processing pipeline used by both CLI and UI.
- `ingest/ocr_ingest.py` — OCR ingestion (preprocessing, retry, caching).
- `extract/extractor.py` — structured extraction logic.
- `schema.py` — shared data schema/validation.
- `storage/db.py` — SQLite persistence layer.
- `evaluation.py` — scoring against sample receipts.

## Constraints Agents Must Respect

- **No network calls.** This project must remain fully offline — do not add API clients,
  telemetry, or remote model calls.
- **CPU-only.** Do not add dependencies that assume a GPU.
- Keep new dependencies in `requirements.txt` minimal and pinned with `>=`.
- Preserve the OCR cache versioning behavior in `ingest/ocr_ingest.py` — cache keys must
  change when extraction logic changes, to avoid serving stale results.

## Before Committing

Agents must run, and ensure passing:

```bash
ruff check .
mypy .
bandit -r . -x tests,.venv
pytest --cov
```

Stage files with `git add` before committing — pre-commit hooks only scan staged files.

## Skill Routing

This repository uses skill-specific guidance for AI agents.

- The root `AGENTS.md` file describes high-level repo goals and constraints.
- `skills.md` explains available skills and how to route requests to them.
- `.agents/skills/developing-with-streamlit/SKILL.md` is the Streamlit skill.

### Use the Streamlit skill when:

- the task involves `streamlit` or `st.` usage
- the task is editing or debugging `streamlit_app.py`
- the task is about app layout, widgets, themes, or UI behavior
- the task is building or packaging Streamlit components

### When to stay at the root level

Use `AGENTS.md` for:

- project-wide architectural changes
- offline/CPU-only dependency decisions
- build, CI, and packaging concerns
- requirements and environment constraints

## Testing

Tests live in `tests/` and cover OCR caching, extraction, storage, evaluation, and the
end-to-end pipeline. Add or update tests alongside any behavioral change.
