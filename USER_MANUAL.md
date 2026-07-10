# DocuStruct User Manual

## Overview

DocuStruct turns photos of receipts and invoices into structured, queryable data,
entirely offline (OCR, extraction, and storage all run locally — no cloud calls).

## Installation

```bash
git clone https://code.swecha.org/Sohansourab27/docustruct.git
cd docustruct
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You will also need the Tesseract OCR engine installed on your system:

```bash
# Debian/Ubuntu
sudo apt-get install tesseract-ocr
```

## Running the App

### Streamlit UI (recommended)

```bash
streamlit run streamlit_app.py
```

Then open the printed local URL in your browser. From there you can:

- Upload receipt/invoice images (`PNG`, `JPG`, `JPEG`, `WEBP`) or use the camera capture.
- View the structured extraction result and validation status.
- Browse previously processed documents in the database explorer.
- View analytics/scoring on bundled sample receipts.

### Command Line

```bash
python3 app.py samples/receipt_cafe.png samples/receipt_hardware.png
python3 app.py samples/*.png --report
```

This prints structured JSON for each document and, with `--report`, an evaluation summary.

## Sample Data

Bundled sample images live in `samples/` and are the best starting point for a demo:

- `samples/receipt_cafe.png`
- `samples/receipt_grocery.png`
- `samples/receipt_hardware.png`

## Data Storage

Processed documents are persisted to a local SQLite database (default:
`storage/docustruct.db`), configurable via `DOCUSTRUCT_DB_PATH` in `.env`
(see `.env.example`). OCR results are cached under `storage/ocr_cache/`.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `TesseractNotFoundError` | Tesseract not installed / not on PATH | Install `tesseract-ocr` and restart shell |
| Empty/garbled extraction | Low-quality or angled photo | Use a full-frame, well-lit photo |
| Stale OCR result after code change | OCR cache reused | Clear `storage/ocr_cache/` |
