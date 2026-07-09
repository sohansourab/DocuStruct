from __future__ import annotations

from pipeline import process_document
from extract.extractor import RuleBasedExtractor
from storage import db


def test_process_document_runs_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "docustruct.db")
    db.init_db()

    from pipeline import ocr_image

    def fake_ocr(path, use_cache=True):
        return {
            "text": """
Blue Bottle Coffee
123 Market St, Palo Alto
Date: 2026-06-14

Latte        2  4.50
Croissant    1  3.25
Bagel        2  2.75

Subtotal   $17.25
Tax         $1.55
Total      $18.80
""",
            "status": "ok",
            "from_cache": False,
            "processing_ms": 4.2,
            "attempts": 1,
            "error": None,
        }

    monkeypatch.setattr("pipeline.ocr_image", fake_ocr)

    result = process_document("/tmp/receipt_cafe.png", RuleBasedExtractor(), source_label="receipt_cafe.png")

    assert result["error"] is None
    assert result["doc_id"] == 1
    assert result["structured"].vendor == "Blue Bottle Coffee"
    assert result["structured"].total == 18.8
