# Implementation Plan: Receipt OCR and Extraction Improvements

## Affected Modules
- `ingest/ocr_ingest.py` — improve OCR preprocessing and caching logic
- `extract/extractor.py` — extend rule-based extraction heuristics
- `streamlit_app.py` — add partial-result messaging and retry guidance
- `tests/` — add regression coverage for real-world receipt parsing

## Steps
1. Review current OCR preprocessing and identify weak points for skew, contrast, and small text.
2. Adjust `_preprocess()` and helper steps in `ingest/ocr_ingest.py`.
3. Add extraction rules for additional receipt layout patterns in `extract/extractor.py`.
4. Update the Streamlit UI to show a status banner for partial/failed results.
5. Add end-to-end tests that simulate poor-quality receipts and verify structured outputs.
6. Run `pre-commit` and update docs with the new feature scope.

## Testing Strategy
- Unit tests for OCR preprocessing and `ocr_image()` caching behavior.
- Extraction regression tests on bundled receipt samples.
- Pipeline test ensuring `process_document()` returns valid structured data.
- Streamlit UI manual validation for partial result messaging.

## Rollout
- No migration/backfill needed for SQLite data.
- Existing database schema remains unchanged.
