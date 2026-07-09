# DocuStruct

An offline-first, local-only receipt and invoice digitization pipeline. DocuStruct ingests raw images, extracts structured data without relying on cloud APIs, and securely stores queryable records. 

Designed to be lightweight, resilient, and demoable, it runs entirely on CPU using system-level OCR and pluggable local Small Language Models (SLMs).

## Architecture Pipeline

The system is built on a strictly modular architecture to ensure separation of concerns and easy swapping of components.

1. **Ingestion Layer (`ocr_ingest.py`)**
   * **Input:** Raw photos or scanned images of receipts/invoices.
   * **Engine:** Tesseract OCR.
   * **Execution:** 100% local, CPU-bound, with no internet requirements or heavy model downloads.
   * **Output:** Unstructured raw text and bounding box data.

2. **Transformation & Extraction Layer (`extractor.py` & `schema.py`)**
   * **Target Schema:** Structured JSON enforcing strict fields (`vendor`, `date`, `total`, `tax`, `line_items`, `confidence`).
   * **Primary Engine:** Local rule-based/heuristic extraction for fast, predictable processing.
   * **Pluggable Interface:** Designed to dynamically swap in a quantized local SLM (e.g., `llama.cpp` + `Qwen2.5-0.5B-Instruct-GGUF`) for complex, messy, or non-standard documents without breaking downstream tasks.

3. **Storage Layer (`db.py`)**
   * **Engine:** SQLite.
   * **Function:** Maps the extracted JSON schema into queryable relational tables for permanent, offline persistence.

## Resilience & Reliability

DocuStruct treats failure as a first-class state, ensuring partial or failed extractions do not corrupt the database:
* **Retry Logic:** Automatic retries on OCR latency or execution failures.
* **Local Caching:** Caches intermediate OCR results to prevent re-running expensive ingestion steps during extraction debugging or retries.
* **Confidence Scoring:** Every extracted field and final document includes a confidence metric. Partial extractions are flagged for human review rather than silently marked as "done".

## Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Language** | Python 3.x | Core pipeline orchestration |
| **OCR** | Tesseract | System-level raw text extraction |
| **Extraction** | Regex / Pydantic | Heuristic rules and schema validation |
| **AI (Optional)** | llama.cpp / GGUF | Local SLM inference for complex parsing |
| **Database** | SQLite | Zero-config local relational storage |

## Getting Started

### Prerequisites
* Python 3.8+
* Tesseract OCR installed on your system (`apt install tesseract-ocr` or `brew install tesseract`)

### Installation
1. Clone the repository.
2. Install Python dependencies:
   `pip install -r requirements.txt`
3. Initialize the database:
   `python -m docustruct.storage.db --init`

### Usage
Run the pipeline on a sample image:
`python docustruct/app.py --input docustruct/samples/receipt_cafe.png`