"""
schema.py
---------
The target structured schema for the "Local AI" hackathon pipeline.

Design goal: unstructured input (receipt/invoice image) -> this JSON shape.
This is the contract that BOTH extractors (rule-based and local-SLM) must satisfy,
so the rest of the pipeline (validation, storage, querying) never has to know
which extraction strategy produced the data.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json


@dataclass
class LineItem:
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None


@dataclass
class StructuredDocument:
    # Core fields
    vendor: Optional[str] = None
    document_date: Optional[str] = None          # ISO 8601 (YYYY-MM-DD) where possible
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    line_items: List[LineItem] = field(default_factory=list)

    # Provenance / trust metadata -- required by the "Model Performance" and
    # "Data Schema Alignment" validation criteria in the hackathon rubric.
    raw_text: str = ""
    extractor_used: str = ""                     # "rule_based" | "local_slm"
    field_confidence: dict = field(default_factory=dict)  # per-field 0-1 score
    overall_confidence: float = 0.0
    source_file: str = ""
    processing_ms: float = 0.0

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d, indent=2, ensure_ascii=False)

    def validate(self) -> List[str]:
        """Cheap schema-alignment check. Returns a list of problems (empty = clean)."""
        problems = []
        if not self.vendor:
            problems.append("missing:vendor")
        if not self.document_date:
            problems.append("missing:document_date")
        if self.total is None:
            problems.append("missing:total")
        if self.total is not None and self.subtotal is not None and self.tax is not None:
            expected = round(self.subtotal + self.tax, 2)
            if abs(expected - round(self.total, 2)) > 0.05:
                problems.append(f"math_mismatch:subtotal+tax={expected}!=total={self.total}")
        for i, li in enumerate(self.line_items):
            if li.quantity is not None and li.unit_price is not None and li.line_total is not None:
                expected_line = round(li.quantity * li.unit_price, 2)
                if abs(expected_line - round(li.line_total, 2)) > 0.05:
                    problems.append(f"line_item_math_mismatch:idx={i}")
        return problems
