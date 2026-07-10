"""
db.py
-----
Local SQLite persistence for structured documents. No external DB, no network.
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "docustruct.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT,
    vendor TEXT,
    document_date TEXT,
    currency TEXT,
    subtotal REAL,
    tax REAL,
    total REAL,
    extractor_used TEXT,
    overall_confidence REAL,
    processing_ms REAL,
    raw_text TEXT,
    field_confidence_json TEXT,
    validation_issues_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    description TEXT,
    quantity REAL,
    unit_price REAL,
    line_total REAL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def save_document(doc, validation_issues: list[str] | None = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO documents
           (source_file, vendor, document_date, currency, subtotal, tax, total,
            extractor_used, overall_confidence, processing_ms, raw_text,
            field_confidence_json, validation_issues_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            doc.source_file,
            doc.vendor,
            doc.document_date,
            doc.currency,
            doc.subtotal,
            doc.tax,
            doc.total,
            doc.extractor_used,
            doc.overall_confidence,
            doc.processing_ms,
            doc.raw_text,
            json.dumps(doc.field_confidence),
            json.dumps(validation_issues or []),
        ),
    )
    doc_id = cur.lastrowid
    for li in doc.line_items:
        cur.execute(
            """INSERT INTO line_items (document_id, description, quantity, unit_price, line_total)
               VALUES (?,?,?,?,?)""",
            (doc_id, li.description, li.quantity, li.unit_price, li.line_total),
        )
    conn.commit()
    conn.close()
    return doc_id


def query_documents(min_confidence: float = 0.0) -> list[dict]:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM documents WHERE overall_confidence >= ? ORDER BY created_at DESC",
        (min_confidence,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_line_items(document_id: int) -> list[dict]:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM line_items WHERE document_id = ?", (document_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
