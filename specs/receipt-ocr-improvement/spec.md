# Feature Spec: Receipt OCR and Extraction Improvements

## Problem
Receipt and invoice images vary widely in quality, layout, and formatting. The current pipeline can fail or produce incomplete structured output for skewed, low-contrast, or nonstandard receipts.

## Goals
- Increase OCR reliability for real-world receipt and invoice photos.
- Improve extraction accuracy and validation coverage.
- Provide clearer user feedback in the Streamlit app for partial or failed processing.

## Non-Goals
- Adding cloud OCR or external APIs.
- Replacing the existing offline rule-based extractor with a full ML model.

## Proposed Solution
- Enhance image preprocessing in `ingest/ocr_ingest.py` with better scaling, deskew, and binarization.
- Extend the rule-based extraction heuristics in `extract/extractor.py` to handle more vendor formats and malformed totals.
- Add UI messaging in `streamlit_app.py` for partial results, OCR confidence issues, and retry guidance.
- Cover the changes with regression tests for both pipeline and evaluation flows.

## Constraints
- Must remain offline / CPU-only (see constitution.md)
- Must not introduce cloud dependencies or external API calls
- Should keep existing SQLite storage and Streamlit UX intact

## Open Questions
- Should the UI explicitly expose OCR confidence metrics or keep the display simplified?
- Which additional receipt sample categories are highest priority for coverage?
- How should partial/failed results be surfaced to users in the current Streamlit layout?