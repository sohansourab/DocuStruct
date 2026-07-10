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
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from evaluation import evaluate_runs
from pipeline import build_extractor, process_document
from storage import db


def process_file(path: str, extractor) -> dict:
    return process_document(path, extractor)


def main():
    parser = argparse.ArgumentParser(description="DocuStruct offline extraction pipeline")
    parser.add_argument("files", nargs="+", help="Image file(s) to process (globs OK)")
    parser.add_argument("--report", action="store_true", help="Print resource/efficiency report")
    parser.add_argument(
        "--extractor",
        choices=["rule_based", "local_slm"],
        default="rule_based",
        help="Extraction strategy. 'local_slm' requires --model-path and llama-cpp-python installed.",
    )
    parser.add_argument(
        "--model-path",
        default=None,
        help="Path to a local GGUF file, required when --extractor local_slm is used.",
    )
    args = parser.parse_args()

    # Expand globs manually (portable across shells)
    files = []
    for pattern in args.files:
        matches = glob.glob(pattern)
        files.extend(matches if matches else [pattern])

    db.init_db()
    if args.extractor == "local_slm" and not args.model_path:
        parser.error("--extractor local_slm requires --model-path /path/to/model.gguf")
    extractor = build_extractor(args.extractor, args.model_path)

    results = []
    for f in files:
        if not Path(f).exists():
            print(f"[skip] file not found: {f}")
            continue
        print(f"\n=== Processing {f} ===")
        r = process_file(f, extractor)
        results.append(r)

        if r["error"]:
            print(f"Error: {r['error']}")
            continue
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
            print(
                f"{fname:<28}{r['total_wall_ms']:>10}{r['peak_memory_kb']:>10}{r['overall_confidence']:>12}"
            )
        avg_ms = sum(r["total_wall_ms"] for r in results) / len(results)
        avg_conf = sum(r["overall_confidence"] for r in results) / len(results)
        print(f"\nAvg wall time: {avg_ms:.1f}ms | Avg confidence: {avg_conf:.2f}")
        scorecard = evaluate_runs(results)
        print("\n=== Hackathon Scorecard ===")
        print(f"Known cases: {scorecard['known_cases']}")
        if scorecard["field_accuracy"] is not None:
            print(f"Field accuracy: {scorecard['field_accuracy']:.3f}")
            print(f"Line-item accuracy: {scorecard['line_item_accuracy']:.3f}")
        else:
            print("Field accuracy: unavailable for unlabeled inputs")
        print(f"Validation pass rate: {scorecard['validation_pass_rate']:.3f}")
        print(f"Offline success rate: {scorecard['offline_success_rate']:.3f}")
        print(
            f"Avg latency: {scorecard['avg_latency_ms']:.1f}ms | Avg peak memory: {scorecard['avg_peak_memory_kb']:.1f}KB"
        )
        print(f"Overall score: {scorecard['overall_score']}/100")
        print("(All processing above ran fully offline, CPU-only, no external API calls.)")


if __name__ == "__main__":
    main()
