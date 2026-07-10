from __future__ import annotations

from extract.extractor import RuleBasedExtractor


def test_rule_based_extractor_handles_bare_digit_totals_and_line_items():
    text = """
Green Valley Grocery
45 Farm Road
Date: Jun 25, 2026

1 LG BLACK SAKURA 59,091
1 LONGAN 0
1 ROASTED ALMOND 0
1 NANGGO 0
1 MINERAL WATER (bundling) 5k

Sub Total 63,636
PB1 (10%) 6,364
Rounding 0
Total 70,000
"""

    doc = RuleBasedExtractor().extract(text)

    assert doc.vendor == "Green Valley Grocery"
    assert doc.document_date == "2026-06-25"
    assert doc.total == 70000.0
    assert doc.subtotal == 63636.0
    assert doc.tax == 6364.0
    assert any(
        item.description == "LG BLACK SAKURA" and item.unit_price == 59091.0
        for item in doc.line_items
    )
    assert any(
        item.description == "MINERAL WATER (bundling)" and item.unit_price == 5000.0
        for item in doc.line_items
    )
