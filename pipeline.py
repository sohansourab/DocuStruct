"""Shared DocuStruct pipeline helpers used by the CLI and Streamlit UI."""

from __future__ import annotations

import time
import tracemalloc
from pathlib import Path
from typing import Optional

from extract.extractor import LocalLLMExtractor, RuleBasedExtractor
from ingest.ocr_ingest import ocr_image
from storage import db


def build_extractor(kind: str = "rule_based", model_path: Optional[str] = None):
    if kind == "local_slm":
        if not model_path:
            raise ValueError("model_path is required for local_slm")
        return LocalLLMExtractor(model_path=model_path)
    return RuleBasedExtractor()


def process_document(
    path: str,
    extractor,
    source_label: Optional[str] = None,
    use_cache: bool = True,
    persist: bool = True,
) -> dict:
    tracemalloc.start()
    t0 = time.time()
    ocr_result = {
        "text": "",
        "status": "failed",
        "from_cache": False,
        "processing_ms": 0.0,
        "attempts": 0,
        "error": None,
    }
    doc = None
    error = None
    try:
        ocr_result = ocr_image(path, use_cache=use_cache)
        doc = extractor.extract(ocr_result["text"])
        doc.source_file = source_label or path

        issues = doc.validate()
        doc_id = db.save_document(doc, validation_issues=issues) if persist else None
    except Exception as exc:  # noqa: BLE001 - pipeline should fail soft and report the reason
        error = str(exc)
        issues = [f"pipeline_error:{error}"]
        doc_id = None

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    wall_ms = round((time.time() - t0) * 1000, 2)

    return {
        "file": path,
        "source_label": source_label or Path(path).name,
        "doc_id": doc_id,
        "ocr_status": ocr_result["status"],
        "ocr_from_cache": ocr_result["from_cache"],
        "ocr_ms": ocr_result["processing_ms"],
        "extract_ms": getattr(doc, "processing_ms", 0.0),
        "total_wall_ms": wall_ms,
        "peak_memory_kb": round(peak / 1024, 1),
        "overall_confidence": getattr(doc, "overall_confidence", 0.0),
        "validation_issues": issues,
        "structured": doc,
        "error": error,
        "offline_success": error is None,
    }