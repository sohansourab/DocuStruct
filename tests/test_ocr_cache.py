from __future__ import annotations

import hashlib
import json

from ingest import ocr_ingest


def test_unversioned_cache_is_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr(ocr_ingest, "CACHE_DIR", tmp_path)
    file_path = tmp_path / "receipt.bin"
    file_path.write_bytes(b"sample-bytes")
    file_hash = hashlib.sha256(b"sample-bytes").hexdigest()
    (tmp_path / f"{file_hash}.json").write_text(json.dumps({"text": "stale", "status": "ok"}))

    calls = []

    def fake_run_tesseract(path):
        calls.append(path)
        return "fresh text"

    monkeypatch.setattr(ocr_ingest, "_run_tesseract", fake_run_tesseract)

    result = ocr_ingest.ocr_image(str(file_path), max_retries=0, timeout_seconds=1)

    assert calls == [str(file_path)]
    assert result["text"] == "fresh text"
    assert result["status"] == "ok"
