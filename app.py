"""
app.py
------
DocuStruct: offline-first, CPU-only pipeline that turns receipt/invoice
images into structured JSON + SQLite rows.

Usage:
    python3 app.py samples/receipt_cafe.png samples/receipt_hardware.png
    python3 app.py samples/*.png --report
"""

import argparse
import glob
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from ingest.ocr_ingest import ocr_image
from extract.extractor import RuleBasedExtractor
from storage import db


def process_file(path: str, extractor) -> dict:
    tracemalloc.start()
    t0 = time.time()

    ocr_result = ocr_image(path)
    doc = extractor.extract(ocr_result["text"])
    doc.source_file = path

    issues = doc.validate()
    doc_id = db.save_document(doc, validation_issues=issues)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    wall_ms = round((time.time() - t0) * 1000, 2)

    return {
        "file": path,
        "doc_id": doc_id,
        "ocr_status": ocr_result["status"],
        "ocr_from_cache": ocr_result["from_cache"],
        "ocr_ms": ocr_result["processing_ms"],
        "extract_ms": doc.processing_ms,
        "total_wall_ms": wall_ms,
        "peak_memory_kb": round(peak / 1024, 1),
        "overall_confidence": doc.overall_confidence,
        "validation_issues": issues,
        "structured": doc,
    }


def main():
    parser = argparse.ArgumentParser(description="DocuStruct offline extraction pipeline")
    parser.add_argument("files", nargs="+", help="Image file(s) to process (globs OK)")
    parser.add_argument("--report", action="store_true", help="Print resource/efficiency report")
    args = parser.parse_args()

    # Expand globs manually (portable across shells)
    files = []
    for pattern in args.files:
        matches = glob.glob(pattern)
        files.extend(matches if matches else [pattern])

    db.init_db()
    extractor = RuleBasedExtractor()

    results = []
    for f in files:
        if not Path(f).exists():
            print(f"[skip] file not found: {f}")
            continue
        print(f"\n=== Processing {f} ===")
        r = process_file(f, extractor)
        results.append(r)

        print(f"OCR status: {r['ocr_status']} (cache={r['ocr_from_cache']}, {r['ocr_ms']}ms)")
        print(f"Extraction: {r['extract_ms']}ms, confidence={r['overall_confidence']}")
        if r["validation_issues"]:
            print(f"Validation issues: {r['validation_issues']}")
        else:
            print("Validation: clean")
        print(r["structured"].to_json())

    if args.report and results:
        print("\n\n=== Resource Efficiency Report ===")
        print(f"{'file':<28}{'wall_ms':>10}{'peak_kb':>10}{'confidence':>12}")
        for r in results:
            fname = Path(r["file"]).name
            print(f"{fname:<28}{r['total_wall_ms']:>10}{r['peak_memory_kb']:>10}{r['overall_confidence']:>12}")
        avg_ms = sum(r["total_wall_ms"] for r in results) / len(results)
        avg_conf = sum(r["overall_confidence"] for r in results) / len(results)
        print(f"\nAvg wall time: {avg_ms:.1f}ms | Avg confidence: {avg_conf:.2f}")
        print("(All processing above ran fully offline, CPU-only, no external API calls.)")


if __name__ == "__main__":
    main()
