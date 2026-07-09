"""
ocr_ingest.py
-------------
Fully local ingestion layer using Tesseract (via pytesseract).

Hackathon rule addressed: "The system must demonstrate graceful failure and
caching when input processing latency occurs." We implement:
  - an on-disk cache keyed by file hash, so re-processing the same file is instant
  - a retry-with-backoff wrapper around the OCR call
  - a soft timeout so a stuck OCR job degrades to a partial/failed result
    instead of hanging the whole pipeline
"""

import hashlib
import json
import os
import time
import signal
from pathlib import Path
from typing import Optional

import pytesseract
from PIL import Image, ImageOps, ImageFilter

CACHE_DIR = Path(__file__).resolve().parent.parent / "storage" / "ocr_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class OCRTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise OCRTimeout("OCR exceeded soft timeout")


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_path(file_hash: str) -> Path:
    return CACHE_DIR / f"{file_hash}.json"


def _preprocess(img: Image.Image) -> Image.Image:
    """Cheap, CPU-only normalization to help OCR accuracy: grayscale, autocontrast,
    light sharpen. No ML model involved -- classic image processing only."""
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def ocr_image(
    path: str,
    max_retries: int = 2,
    timeout_seconds: int = 15,
    use_cache: bool = True,
) -> dict:
    """
    Returns:
        {
          "text": str,
          "status": "ok" | "partial" | "failed",
          "from_cache": bool,
          "processing_ms": float,
          "attempts": int,
        }
    """
    file_hash = _file_hash(path)
    cache_file = _cache_path(file_hash)

    if use_cache and cache_file.exists():
        cached = json.loads(cache_file.read_text())
        cached["from_cache"] = True
        return cached

    start = time.time()
    last_error = None
    text = ""
    status = "failed"
    attempts = 0

    for attempt in range(1, max_retries + 2):  # first try + retries
        attempts = attempt
        try:
            # Soft timeout guard (POSIX only, fine for this sandbox/most Linux hosts)
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout_seconds)
            try:
                img = Image.open(path)
                img = _preprocess(img)
                # PSM 6 = "assume a single uniform block of text", which is a much
                # better fit for receipts/invoices than Tesseract's default
                # automatic page segmentation (which can jumble multi-column text).
                text = pytesseract.image_to_string(img, config="--psm 6")
            finally:
                signal.alarm(0)

            if text.strip():
                status = "ok"
                break
            else:
                status = "partial"  # ran, but nothing recognized
                # don't retry pointlessly on genuinely blank output after 1 try
                if attempt >= 1:
                    break
        except OCRTimeout as e:
            last_error = str(e)
            status = "partial"
            time.sleep(0.3 * attempt)  # backoff
        except Exception as e:  # noqa: BLE001 - hackathon-scope broad catch, logged below
            last_error = str(e)
            status = "failed"
            time.sleep(0.3 * attempt)

    result = {
        "text": text,
        "status": status,
        "from_cache": False,
        "processing_ms": round((time.time() - start) * 1000, 2),
        "attempts": attempts,
        "error": last_error,
    }

    # Cache even partial/failed results briefly so repeated hammering on a bad
    # file doesn't re-burn CPU -- a real system would TTL/evict this.
    cache_file.write_text(json.dumps(result))
    return result
