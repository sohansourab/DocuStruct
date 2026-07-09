from __future__ import annotations

from pathlib import Path

from schema import LineItem, StructuredDocument
from storage import db


def test_sqlite_persistence_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "docustruct.db")
    db.init_db()

    doc = StructuredDocument(
        vendor="Blue Bottle Coffee",
        document_date="2026-06-14",
        currency="USD",
        subtotal=17.25,
        tax=1.55,
        total=18.80,
        line_items=[LineItem(description="Latte", quantity=2.0, unit_price=4.50, line_total=9.00)],
        raw_text="Blue Bottle Coffee\nTotal 18.80",
        extractor_used="rule_based",
        field_confidence={"total": 1.0},
        overall_confidence=0.95,
        source_file="receipt_cafe.png",
        processing_ms=12.3,
    )

    doc_id = db.save_document(doc, validation_issues=[])
    rows = db.query_documents()
    items = db.get_line_items(doc_id)

    assert doc_id == 1
    assert rows[0]["vendor"] == "Blue Bottle Coffee"
    assert rows[0]["validation_issues_json"] == "[]"
    assert items[0]["description"] == "Latte"
