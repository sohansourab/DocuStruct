<div align="center">

<img src="https://code.swecha.org/Sohansourab27/docustruct/-/raw/main/main.jpeg" width="500" alt="DocuStruct Logo" />

<br/>

<p><em>Offline-first AI document pipeline for extracting structured data from receipts and invoices.</em></p>

<a href="https://docustruct.streamlit.app/">
  <img src="https://img.shields.io/badge/🚀%20Live%20Demo-docustruct.streamlit.app-305CDE?style=for-the-badge&logo=streamlit&logoColor=white" alt="Live Demo" />
</a>

<br/><br/>

`Streamlit` &nbsp;•&nbsp; `EasyOCR` &nbsp;•&nbsp; `SQLite` &nbsp;•&nbsp; `llama.cpp` &nbsp;•&nbsp; `Python 3.10+`

</div>

---

# DocuStruct

DocuStruct is an offline-first, CPU-optimized document pipeline that turns receipt and invoice images into structured, queryable data. It is built for the Local AI hackathon brief: no external APIs, no cloud dependencies, and fully local inference and storage.

## What It Does

DocuStruct processes a receipt image through four stages:

1. OCR ingestion with preprocessing, retry, soft timeout, and on-disk cache.
2. Structured extraction into the shared schema defined in `schema.py`.
3. Validation of required fields and arithmetic consistency.
4. SQLite persistence for browsing and analytics.

## Architecture

![docuStruct System Architecture](https://code.swecha.org/Sohansourab27/docustruct/-/raw/main/diagram-export-7-9-2026-3_08_54-PM.png)

## Current Status

The following is implemented and working end to end:

- Offline OCR to structured output pipeline.
- Streamlit UI with upload, camera capture, database explorer, and analytics.
- Shared CLI and UI pipeline logic.
- OCR cache versioning to avoid stale results.
- Rule-based extraction with support for messy receipt formats.
- Optional local `llama-cpp-python` extractor for a GGUF model.
- Repeatable scoring for bundled sample receipts.
- Tests for OCR cache behavior, extraction, storage, evaluation, and pipeline flow.

## What to Upload

For the best demo and for real scoring, start with the bundled sample images:

- `samples/receipt_cafe.png`
- `samples/receipt_grocery.png`
- `samples/receipt_hardware.png`

You can also upload real receipt or invoice images in `PNG`, `JPG`, `JPEG`, or `WEBP` format. Full-frame, well-lit photos work best.

## Installation

Install the project locally in a Python virtual environment:

```bash
cd /path/to/docustruct
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Usage

Run the CLI demo to process sample receipt images and generate a report:

```bash
python app.py samples/*.png --report
```

Run the Streamlit UI for an interactive local demo:

```bash
streamlit run streamlit_app.py
```

The repository also includes a legacy compatibility entrypoint: `streamlit.py` forwards to the same app.

## Deployment & Access URLs

### For Users
- **Try it locally:** `http://localhost:8501` (see [Installation](#installation) above)
- **Demo instance:** Coming soon — publicly hosted version for testing
- **Self-hosted:** Deploy your own using Docker or on your server (see [DEPLOYMENT.md](DEPLOYMENT.md))

### Deployment Options
Choose based on your user base size and infrastructure:

| Option | URL | Best For | Users |
|--------|-----|----------|-------|
| **Local** | `http://localhost:8501` | Developers, individuals | 1-5 |
| **Shared Server** | `https://docustruct.yourcompany.com` | Teams, SMBs | 5-100 |
| **Docker/Kubernetes** | `https://api.docustruct.io` | Enterprises, scaling | 100+ |
| **API-Only** | `https://api.docustruct.io/v1/` | Integrations, mobile apps | N/A |

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for detailed setup instructions for each option.

## Growth & Continuous Improvement

### Roadmap for User Growth
1. **Phase 1 (Months 1-2):** Foundation — Document deployment, analytics setup
2. **Phase 2 (Months 3-4):** Community — Public demo, tutorials, Docker release
3. **Phase 3 (Months 5-6):** Enterprise — SaaS, authentication, premium support

### How We Improve Features
We use a **feedback-driven development cycle**:
```
Collect user feedback → Analyze needs → Prioritize → Implement → Release
```

**Contribute your ideas:**
- 📝 Open a [GitHub Issue](https://code.swecha.org/Sohansourab27/docustruct/-/issues) with feature requests
- 💬 Discuss in [GitHub Discussions](https://code.swecha.org/Sohansourab27/docustruct/-/discussions)
- 📊 Check our [Future Scope](#future-scope) section below

### Planned Features (Q3-Q4 2026)
- PDF ingestion support
- Multilingual OCR (Spanish, French, German)
- Batch API for bulk document processing
- CSV/JSONL export formats
- Advanced analytics dashboard
- Mobile app support

See full roadmap in [DEPLOYMENT.md → Continuous Feature Improvement](DEPLOYMENT.md#continuous-feature-improvement-process).

## Contributing

Contributions are welcome. See `CONTRIBUTING.md` for:

- development setup and environment requirements
- code style and formatting expectations
- testing and pre-commit hook usage
- how to submit merge requests

If you are improving the OCR or extraction pipeline, add new feature specs under `specs/<feature-name>/` with `spec.md`, `plan.md`, and `tasks.md`.

## Evaluation and Metrics

The analytics page and CLI report surface real numbers from the sample set:

- Field accuracy
- Line-item accuracy
- Validation pass rate
- Offline success rate
- Latency
- Peak memory
- Overall score

These numbers are grounded in the bundled sample receipts, which have known expected outputs.

## Local Model Support

DocuStruct includes a local SLM integration path through `llama-cpp-python`. To use it, point the extractor at a local `.gguf` file:

```python
from extract.extractor import LocalLLMExtractor
extractor = LocalLLMExtractor(model_path="./models/model.gguf")
```

This keeps the rest of the pipeline unchanged.

## Future Scope

Planned next steps for the project:

- Add PDF ingestion in addition to images.
- Improve OCR handling for heavily skewed or low-light receipts.
- Add more robust line-item parsing for retail receipts with complex layouts.
- Support multilingual OCR and extraction.
- Extend the scoring harness with larger labeled benchmark sets.
- Add export formats such as CSV and JSONL.
- Add a review workflow for low-confidence extractions.
- Expand the local model path with better prompt templates and structured decoding.

## Repository Layout

```text
docustruct/
├── app.py
├── evaluation.py
├── extract/
├── ingest/
├── pipeline.py
├── schema.py
├── storage/
├── streamlit_app.py
├── streamlit.py
├── tests/
└── samples/
```

## Support & Resources

### Documentation
- **[USER_MANUAL.md](USER_MANUAL.md)** — How to install and use DocuStruct locally
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Deployment options, scaling, growth strategy, and user improvement process
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Developer guide for contributing
- **[ROADMAP.md](docs/ROADMAP.md)** — Long-term project vision

### Get Help
- 📖 Read the [USER_MANUAL.md](USER_MANUAL.md) for setup issues
- 🐛 Report bugs via [GitHub Issues](https://code.swecha.org/Sohansourab27/docustruct/-/issues)
- 💡 Suggest features via [GitHub Discussions](https://code.swecha.org/Sohansourab27/docustruct/-/discussions)
- 🤝 Contribute code via [Pull Requests](https://code.swecha.org/Sohansourab27/docustruct/-/merge_requests)

### Community
- Join discussions to help shape DocuStruct's future
- Share your use cases and success stories
- Help test new features and provide feedback

---

**Questions about scaling or deploying DocuStruct? See [DEPLOYMENT.md](DEPLOYMENT.md).**