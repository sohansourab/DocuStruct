from __future__ import annotations

from extract.extractor import RuleBasedExtractor


def test_rule_based_extractor_parses_dmy_dates():
    text = """
DINEFINE RESTAURANT
123 CULINARY AVENUE
DOWNTOWN DISTRICT
PHONE: (555) 123-4567
WWW. DINEFINE.COM
30/09/2025 20:15
RECEIPT: #R-2547 TABLE: 12
SERVER: MARIA G. GUESTS: 2
2X CAESAR SALAD $24.00
GRILLED SALMON $22.00
CHEESECAKE $7.50
2X SPARKLING WATER $6.00
SUBTOTAL: $47.50
TAX: $3.80
TOTAL: $51.32
"""

    doc = RuleBasedExtractor().extract(text)

    assert doc.vendor == "DINEFINE RESTAURANT"
    assert doc.document_date == "2025-09-30"
    assert doc.total == 51.32
    assert doc.subtotal == 47.5
    assert doc.tax == 3.8
    assert doc.validate() == []
