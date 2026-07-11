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
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path

import numpy as np
import pytesseract
from PIL import Image, ImageFilter, ImageOps

CACHE_DIR = Path(__file__).resolve().parent.parent / "storage" / "ocr_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_VERSION = "2026-07-09-preprocess-v2"


class OCRTimeout(Exception):
    pass


# One shared worker pool for the soft-timeout mechanism below. Using a thread
# (via ThreadPoolExecutor.result(timeout=...)) instead of signal.SIGALRM means
# this works from *any* calling thread and on *any* OS -- SIGALRM only fires
# in the main thread of the main interpreter, which breaks the moment this
# pipeline is called from a Streamlit ScriptRunner thread, a web framework
# worker thread, or Windows (which has no SIGALRM at all).
_OCR_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr-worker")


def _run_tesseract(path: str) -> str:
    img: Image.Image = Image.open(path)
    img = _preprocess(img)
    # PSM 6 = "assume a single uniform block of text", which is a much
    # better fit for receipts/invoices than Tesseract's default automatic
    # page segmentation (which can jumble multi-column text).
    return pytesseract.image_to_string(img, config="--psm 6")


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_path(file_hash: str) -> Path:
    return CACHE_DIR / f"{CACHE_VERSION}-{file_hash}.json"


def _upscale_if_small(img: Image.Image, target_min_dim: int = 1600) -> Image.Image:
    """Low-res phone photos hurt Tesseract's character segmentation. Upscale with
    high-quality (LANCZOS) resampling if the image's largest dimension is small."""
    if max(img.size) < target_min_dim:
        factor = target_min_dim / max(img.size)
        new_size = (int(img.width * factor), int(img.height * factor))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    return img


def _deskew(img: Image.Image, max_angle: float = 15.0, angle_step: float = 0.5) -> Image.Image:
    """Correct small rotational skew (a receipt photographed at a slight angle)
    using the classic projection-profile method: the correctly-rotated angle
    maximizes the variance of row-wise pixel sums, since horizontally-aligned
    text lines create sharp peaks/troughs. Pure numpy, no ML model involved.
    Runs on a small downscaled copy for speed, then applies the found angle to
    the full-resolution image.
    """
    small = img.convert("L")
    scale = min(1.0, 700 / max(small.size))
    if scale < 1.0:
        small = small.resize((max(1, int(small.width * scale)), max(1, int(small.height * scale))))
    arr = np.array(small, dtype=np.float32)
    thresh = arr.mean() - 0.5 * arr.std()
    binary = (arr < thresh).astype(np.uint8) * 255
    binary_img = Image.fromarray(binary)

    best_angle, best_score = 0.0, -1.0
    angle = -max_angle
    while angle <= max_angle:
        rotated = np.array(binary_img.rotate(angle, expand=False, fillcolor=0))
        score = float(rotated.sum(axis=1).var())
        if score > best_score:
            best_score, best_angle = score, angle
        angle += angle_step

    if abs(best_angle) > 0.1:
        return img.rotate(best_angle, expand=True, fillcolor="white", resample=Image.Resampling.BICUBIC)
    return img


def _binarize(img: Image.Image) -> Image.Image:
    """Otsu global thresholding: finds the split point that minimizes combined
    intra-class pixel-intensity variance, turning a photo (with uneven lighting,
    background texture bleed-through, etc.) into clean black text on white --
    which is what Tesseract is tuned for. Implemented directly with numpy so no
    extra CV dependency (e.g. opencv) is required."""
    arr = np.array(img.convert("L"))
    hist, _ = np.histogram(arr, bins=256, range=(0, 256))
    total = arr.size
    sum_total = np.dot(np.arange(256), hist)
    sum_b, w_b, max_var, threshold = 0.0, 0.0, 0.0, 127
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        var_between = w_b * w_f * (m_b - m_f) ** 2
        if var_between > max_var:
            max_var, threshold = var_between, t
    binary = (arr > threshold).astype(np.uint8) * 255
    return Image.fromarray(binary)


def _preprocess(img: Image.Image) -> Image.Image:
    """CPU-only normalization pipeline to help OCR accuracy on real-world phone
    photos (angled, uneven lighting, textured backgrounds): fix EXIF rotation,
    upscale if low-res, deskew, denoise, then binarize. No ML model involved."""
    img = ImageOps.exif_transpose(img)  # phone photos often carry rotation in EXIF only
    img = img.convert("L")
    img = _upscale_if_small(img)
    img = _deskew(img)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.MedianFilter(size=3))  # smooths background texture noise
    img = img.filter(ImageFilter.SHARPEN)
    img = _binarize(img)
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
            # Soft timeout guard -- runs the OCR call on a worker thread and
            # bounds how long we wait for it. Works regardless of which
            # thread/OS called ocr_image (unlike signal.SIGALRM).
            future = _OCR_EXECUTOR.submit(_run_tesseract, path)
            try:
                text = future.result(timeout=timeout_seconds)
            except FutureTimeoutError as e:
                raise OCRTimeout("OCR exceeded soft timeout") from e

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

    # Only cache genuine successes. Caching "failed"/"partial" results forever
    # means a transient error (or a bug that's since been fixed, e.g. code
    # calling this from a new thread context) gets replayed on every future
    # call for that file instead of getting a fresh attempt.
    if status == "ok":
        cache_file.write_text(json.dumps(result))
    return result
