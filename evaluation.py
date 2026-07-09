"""Repeatable scoring helpers for DocuStruct demo and hackathon reporting."""

from __future__ import annotations

import re
from pathlib import Path
from statistics import mean
from typing import Iterable

from schema import LineItem, StructuredDocument


SAMPLE_GROUND_TRUTH = {
    "receipt_cafe.png": {
        "vendor": "Blue Bottle Coffee",
        "document_date": "2026-06-14",
        "currency": "USD",
        "subtotal": 17.25,
        "tax": 1.55,
        "total": 18.80,
        "line_items": [
            {"description": "Latte", "quantity": 2.0, "unit_price": 4.50, "line_total": 9.00},
            {"description": "Croissant", "quantity": 1.0, "unit_price": 3.25, "line_total": 3.25},
            {"description": "Bagel", "quantity": 2.0, "unit_price": 2.75, "line_total": 5.50},
        ],
    },
    "receipt_hardware.png": {
        "vendor": "Ace Hardware Store",
        "document_date": "2026-06-20",
        "currency": "USD",
        "subtotal": 72.00,
        "tax": 6.12,
        "total": 78.12,
        "line_items": [
            {"description": "Hammer", "quantity": 1.0, "unit_price": 15.00, "line_total": 15.00},
            {"description": "Nails Box", "quantity": 3.0, "unit_price": 4.00, "line_total": 12.00},
            {"description": "Paint Can", "quantity": 2.0, "unit_price": 22.50, "line_total": 45.00},
        ],
    },
    "receipt_grocery.png": {
        "vendor": "Green Valley Grocery",
        "document_date": "2026-06-25",
        "currency": "USD",
        "subtotal": 17.70,
        "tax": 1.42,
        "total": 19.12,
        "line_items": [
            {"description": "Milk", "quantity": 1.0, "unit_price": 3.50, "line_total": 3.50},
            {"description": "Bread", "quantity": 2.0, "unit_price": 2.20, "line_total": 4.40},
            {"description": "Eggs", "quantity": 1.0, "unit_price": 4.00, "line_total": 4.00},
            {"description": "Apples", "quantity": 5.0, "unit_price": 0.80, "line_total": 4.00},
        ],
    },
}


def _norm_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _norm_number(value):
    if value is None:
        return None
    return round(float(value), 2)


def _scalar_score(actual, expected) -> float:
    if expected is None and actual is None:
        return 1.0
    if expected is None or actual is None:
        return 0.0
    if isinstance(expected, (int, float)) or isinstance(actual, (int, float)):
        return 1.0 if abs(_norm_number(actual) - _norm_number(expected)) <= 0.05 else 0.0
    return 1.0 if _norm_text(actual) == _norm_text(expected) else 0.0


def _line_item_signature(item) -> tuple:
    if isinstance(item, LineItem):
        return (_norm_text(item.description), _norm_number(item.quantity), _norm_number(item.unit_price), _norm_number(item.line_total))
    return (
        _norm_text(item.get("description")),
        _norm_number(item.get("quantity")),
        _norm_number(item.get("unit_price")),
        _norm_number(item.get("line_total")),
    )


def score_document(doc: StructuredDocument, expected: dict) -> dict:
    scalar_fields = ["vendor", "document_date", "currency", "subtotal", "tax", "total"]
    field_scores = {field: _scalar_score(getattr(doc, field), expected.get(field)) for field in scalar_fields}

    expected_items = [_line_item_signature(item) for item in expected.get("line_items", [])]
    actual_items = [_line_item_signature(item) for item in doc.line_items]
    matched = 0
    remaining = list(expected_items)
    for actual in actual_items:
        for index, candidate in enumerate(remaining):
            if actual[0] == candidate[0] and actual[1:] == candidate[1:]:
                matched += 1
                remaining.pop(index)
                break

    line_item_accuracy = matched / max(len(expected_items), len(actual_items), 1)
    scalar_accuracy = mean(field_scores.values()) if field_scores else 0.0
    field_accuracy = round((scalar_accuracy * 0.75) + (line_item_accuracy * 0.25), 3)
    validation_pass = not doc.validate()

    return {
        "field_scores": field_scores,
        "line_item_accuracy": round(line_item_accuracy, 3),
        "field_accuracy": field_accuracy,
        "validation_pass": validation_pass,
    }


def evaluate_runs(runs: Iterable[dict]) -> dict:
    runs = list(runs)
    known_scores = []
    for run in runs:
        doc = run.get("structured")
        if not isinstance(doc, StructuredDocument):
            continue
        name = Path(run.get("source_label") or run.get("file") or "").name
        if name in SAMPLE_GROUND_TRUTH:
            known_scores.append(score_document(doc, SAMPLE_GROUND_TRUTH[name]))

    validation_pass_rate = sum(not run.get("validation_issues") for run in runs) / len(runs) if runs else 0.0
    offline_success_rate = sum(1 for run in runs if run.get("offline_success")) / len(runs) if runs else 0.0
    avg_latency_ms = mean(run.get("total_wall_ms", 0.0) for run in runs) if runs else 0.0
    avg_peak_kb = mean(run.get("peak_memory_kb", 0.0) for run in runs) if runs else 0.0
    avg_confidence = mean(run.get("overall_confidence", 0.0) for run in runs) if runs else 0.0
    field_accuracy = mean(item["field_accuracy"] for item in known_scores) if known_scores else None
    line_item_accuracy = mean(item["line_item_accuracy"] for item in known_scores) if known_scores else None

    resource_score = max(0.0, 1.0 - (avg_latency_ms / 2500.0) - (avg_peak_kb / 2048.0))
    quality_score = field_accuracy if field_accuracy is not None else avg_confidence
    overall_score = round(100 * ((quality_score * 0.55) + (validation_pass_rate * 0.2) + (offline_success_rate * 0.15) + (resource_score * 0.1)), 1)

    return {
        "known_cases": len(known_scores),
        "field_accuracy": field_accuracy,
        "line_item_accuracy": line_item_accuracy,
        "validation_pass_rate": round(validation_pass_rate, 3),
        "offline_success_rate": round(offline_success_rate, 3),
        "avg_latency_ms": round(avg_latency_ms, 2),
        "avg_peak_memory_kb": round(avg_peak_kb, 1),
        "avg_confidence": round(avg_confidence, 3),
        "resource_score": round(resource_score, 3),
        "overall_score": overall_score,
    }