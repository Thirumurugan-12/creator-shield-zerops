from __future__ import annotations

import re
from pathlib import Path

from fastapi import UploadFile


VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}
EVIDENCE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}


def safe_filename(filename: str | None, fallback: str) -> str:
    name = Path(filename or fallback).name
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("._")
    return name[:255] or fallback


async def validate_upload_signature(upload: UploadFile, kind: str) -> str:
    filename = safe_filename(upload.filename, "upload")
    suffix = Path(filename).suffix.lower()
    allowed_suffixes = VIDEO_EXTENSIONS if kind == "video" else EVIDENCE_EXTENSIONS
    if suffix not in allowed_suffixes:
        raise ValueError("Unsupported upload extension")
    header = await upload.read(16)
    await upload.seek(0)
    if kind == "video":
        valid = len(header) >= 8 and (header[4:8] == b"ftyp" or header[:4] == b"\x1a\x45\xdf\xa3")
    elif suffix == ".pdf":
        valid = header.startswith(b"%PDF-")
    elif suffix == ".png":
        valid = header.startswith(b"\x89PNG\r\n\x1a\n")
    else:
        valid = header.startswith(b"\xff\xd8\xff")
    if not valid:
        raise ValueError("File content does not match its declared type")
    return filename


def malware_scan_hook(upload: UploadFile) -> str:
    """Integration point for a scanner; local development records a safe no-op."""
    return "not_configured"
