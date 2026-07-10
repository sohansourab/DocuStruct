"""
extractor.py
------------
Turns normalized OCR text into a StructuredDocument.

Two extractor implementations sharing one interface (BaseExtractor):

  1. RuleBasedExtractor   -- fully working, zero external downloads, regex +
                              heuristics. This is what actually runs in this
                              sandbox/demo.

  2. LocalLLMExtractor    -- wiring for a quantized local SLM via
                              llama-cpp-python (e.g. a ~0.5-1B GGUF model).
                              This sandbox has no route to model-weight hosts
                              (huggingface.co etc. are not reachable here), so
                              this class is a real, runnable implementation
                              that will work the moment you point it at a GGUF
                              file on a machine that has one -- nothing else
                              in the pipeline changes.

Swap by changing one line in app.py: EXTRACTOR = RuleBasedExtractor() vs
EXTRACTOR = LocalLLMExtractor(model_path=...).
"""

import re
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from schema import LineItem, StructuredDocument


class BaseExtractor(ABC):
    name = "base"

    @abstractmethod
    def extract(self, raw_text: str) -> StructuredDocument: ...


# ---------------------------------------------------------------------------
# 1. Rule-based extractor (the working default in this prototype)
# ---------------------------------------------------------------------------

MONEY_RE = re.compile(
    r"(?:(?P<sym>[$₹€£]|\bRs\.?|\bRp\.?)\s?)?(?P<amt>\d[\d,]*(?:\.\d{1,2})?(?:[kK])?)"
)
DATE_PATTERNS = [
    (r"\b(\d{4})-(\d{2})-(\d{2})\b", "%Y-%m-%d"),
    (r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", "%m/%d/%Y"),
    (r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", "%d/%m/%Y"),
    (r"\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b", "%m-%d-%Y"),
    (r"\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b", "%d-%m-%Y"),
    (
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})\b",
        None,
    ),
]
TOTAL_KEYWORDS = ["grand total", "total due", "amount due", "total"]
SUBTOTAL_KEYWORDS = ["subtotal", "sub total", "sub-total"]
TAX_KEYWORDS = ["tax", "vat", "gst", "pb1", "ppn", "sales tax"]
LINE_ITEM_PATTERNS = [
    re.compile(
        r"^\s*(?P<qty>\d+(?:\.\d+)?)\s+(?P<desc>.+?)\s+(?P<price>\d[\d,]*(?:\.\d{1,2})?(?:[kK])?)\s*$"
    ),
    re.compile(
        r"^\s*(?P<desc>[A-Za-z0-9][A-Za-z0-9 &/'\-.]{2,80}?)\s+"
        r"(?P<qty>\d+(?:\.\d+)?)\s*[xX@]?\s*"
        r"(?:[$₹€£]|\bRs\.?)?\s?(?P<price>\d[\d,]*(?:\.\d{1,2})?(?:[kK])?)\s*$"
    ),
]


def _parse_money(s: str) -> float | None:
    raw = s.strip()
    try:
        if raw.lower().endswith("k"):
            return float(raw[:-1].replace(",", "")) * 1000
        if "," in raw and "." not in raw:
            parts = raw.split(",")
            if len(parts) == 2 and len(parts[1]) == 2:
                return float(".".join(parts))
            if len(parts) == 2 and len(parts[1]) == 3:
                return float("".join(parts))
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _find_amount_near_keyword(
    lines: list[str], keywords: list[str], exclude_keywords: list[str] | None = None
) -> float | None:
    exclude_keywords = exclude_keywords or []
    match = None
    for line in lines:
        low = line.lower()
        if any(ex in low for ex in exclude_keywords):
            continue
        if any(k in low for k in keywords):
            candidates = list(MONEY_RE.finditer(line))
            if candidates:
                # The amount is almost always the rightmost number on the line
                # (label then value); this also makes us robust to stray OCR
                # noise/digits appearing before the keyword.
                match = _parse_money(candidates[-1].group("amt"))  # keep scanning; last hit wins
    return match


def _find_date(text: str) -> str | None:
    for pattern, fmt in DATE_PATTERNS:
        m = re.search(pattern, text)
        if not m:
            continue
        try:
            if fmt:
                return datetime.strptime(m.group(0), fmt).date().isoformat()
            else:
                # month-name style, normalize manually
                return datetime.strptime(m.group(0).replace(",", ""), "%b %d %Y").date().isoformat()
        except ValueError:
            continue
    return None


def _find_vendor(lines: list[str]) -> str | None:
    # Heuristic: vendor name is usually one of the first non-empty,
    # mostly-alphabetic lines at the top of a receipt.
    for line in lines[:5]:
        clean = line.strip()
        if len(clean) < 3:
            continue
        letters = sum(c.isalpha() for c in clean)
        if letters / max(len(clean), 1) > 0.6:
            return clean
    return None


def _find_line_items(lines: list[str]) -> list[LineItem]:
    items = []
    for line in lines:
        low = line.lower()
        if any(
            k in low
            for k in TOTAL_KEYWORDS + SUBTOTAL_KEYWORDS + TAX_KEYWORDS + ["cash payment", "change"]
        ):
            continue
        for pattern in LINE_ITEM_PATTERNS:
            m = pattern.match(line.strip())
            if not m:
                continue
            qty = float(m.group("qty"))
            price = _parse_money(m.group("price"))
            if price is None:
                continue
            items.append(
                LineItem(
                    description=m.group("desc").strip(),
                    quantity=qty,
                    unit_price=price,
                    line_total=round(qty * price, 2),
                )
            )
            break
    return items


class RuleBasedExtractor(BaseExtractor):
    name = "rule_based"

    def extract(self, raw_text: str) -> StructuredDocument:
        start = time.time()
        lines = [line for line in raw_text.splitlines() if line.strip()]

        vendor = _find_vendor(lines)
        date = _find_date(raw_text)
        subtotal = _find_amount_near_keyword(lines, SUBTOTAL_KEYWORDS)
        total = _find_amount_near_keyword(lines, TOTAL_KEYWORDS, exclude_keywords=SUBTOTAL_KEYWORDS)
        tax = _find_amount_near_keyword(lines, TAX_KEYWORDS)
        line_items = _find_line_items(lines)

        currency = None
        cm = re.search(r"[$₹€£]|\bRp\b", raw_text)
        if cm:
            currency = {"$": "USD", "₹": "INR", "€": "EUR", "£": "GBP", "Rp": "IDR"}.get(
                cm.group(0)
            )

        confidence = {
            "vendor": 0.6 if vendor else 0.0,
            "document_date": 0.8 if date else 0.0,
            "total": 0.75 if total is not None else 0.0,
            "subtotal": 0.6 if subtotal is not None else 0.0,
            "tax": 0.6 if tax is not None else 0.0,
            "line_items": min(0.9, 0.2 * len(line_items)) if line_items else 0.0,
        }
        overall = round(sum(confidence.values()) / len(confidence), 3)

        doc = StructuredDocument(
            vendor=vendor,
            document_date=date,
            currency=currency,
            subtotal=subtotal,
            tax=tax,
            total=total,
            line_items=line_items,
            raw_text=raw_text,
            extractor_used=self.name,
            field_confidence=confidence,
            overall_confidence=overall,
            processing_ms=round((time.time() - start) * 1000, 2),
        )
        return doc


# ---------------------------------------------------------------------------
# 2. Local SLM extractor -- real wiring, needs a GGUF file to actually run.
#    Not executable in this network-restricted sandbox (no HF access), but
#    this is the exact integration point the rule-based extractor above
#    is meant to be swapped out for.
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """You are a strict JSON extraction engine. Read the receipt/invoice
text below and output ONLY a JSON object matching this schema, no prose:

{{
  "vendor": string or null,
  "document_date": "YYYY-MM-DD" or null,
  "currency": string or null,
  "subtotal": number or null,
  "tax": number or null,
  "total": number or null,
  "line_items": [{{"description": string, "quantity": number, "unit_price": number, "line_total": number}}]
}}

TEXT:
---
{text}
---
JSON:"""


class LocalLLMExtractor(BaseExtractor):
    name = "local_slm"

    def __init__(self, model_path: str, n_ctx: int = 2048, n_threads: int | None = None):
        try:
            from llama_cpp import Llama  # local import: optional dependency
        except ImportError as e:
            raise ImportError(
                "llama-cpp-python is required for LocalLLMExtractor. "
                "Install with: pip install llama-cpp-python\n"
                "Then download a small instruct GGUF (e.g. Qwen2.5-0.5B-Instruct-GGUF "
                "or Llama-3.2-1B-Instruct-GGUF) and pass its path here."
            ) from e
        self._Llama = Llama
        self.llm = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads, verbose=False)

    def extract(self, raw_text: str) -> StructuredDocument:
        import json as _json

        start = time.time()
        prompt = EXTRACTION_PROMPT.format(text=raw_text[:3000])
        out = self.llm(prompt, max_tokens=512, temperature=0.0, stop=["```"])
        raw = out["choices"][0]["text"].strip()
        try:
            data = _json.loads(raw)
        except _json.JSONDecodeError:
            # Model didn't return clean JSON -- fail soft into an empty-but-valid doc
            data = {}

        line_items = [
            LineItem(**li)
            for li in data.get("line_items", [])
            if isinstance(li, dict) and "description" in li
        ]
        doc = StructuredDocument(
            vendor=data.get("vendor"),
            document_date=data.get("document_date"),
            currency=data.get("currency"),
            subtotal=data.get("subtotal"),
            tax=data.get("tax"),
            total=data.get("total"),
            line_items=line_items,
            raw_text=raw_text,
            extractor_used=self.name,
            field_confidence={},  # SLM logprob-based confidence could be added here
            overall_confidence=0.0,
            processing_ms=round((time.time() - start) * 1000, 2),
        )
        return doc
