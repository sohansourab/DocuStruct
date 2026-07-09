from __future__ import annotations

from evaluation import evaluate_runs
from schema import LineItem, StructuredDocument


def test_evaluation_reports_real_scores_for_known_sample():
    doc = StructuredDocument(
        vendor="Blue Bottle Coffee",
        document_date="2026-06-14",
        currency="USD",
        subtotal=17.25,
        tax=1.55,
        total=18.80,
        line_items=[
            LineItem(description="Latte", quantity=2.0, unit_price=4.50, line_total=9.00),
            LineItem(description="Croissant", quantity=1.0, unit_price=3.25, line_total=3.25),
            LineItem(description="Bagel", quantity=2.0, unit_price=2.75, line_total=5.50),
        ],
        overall_confidence=0.9,
    )
    metrics = evaluate_runs([
        {
            "file": "/tmp/receipt_cafe.png",
            "source_label": "receipt_cafe.png",
            "structured": doc,
            "validation_issues": [],
            "offline_success": True,
            "total_wall_ms": 10.0,
            "peak_memory_kb": 128.0,
            "overall_confidence": 0.9,
        }
    ])

    assert metrics["known_cases"] == 1
    assert metrics["field_accuracy"] == 1.0
    assert metrics["validation_pass_rate"] == 1.0
    assert metrics["offline_success_rate"] == 1.0
