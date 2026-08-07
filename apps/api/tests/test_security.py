import asyncio
from io import BytesIO

import pytest
from starlette.datastructures import UploadFile

from apps.api.app.services.rate_limit import InMemoryRateLimiter
from apps.api.app.services.storage import StorageService
from apps.api.app.services.upload_security import safe_filename, validate_upload_signature


def test_safe_filename_removes_path_components_and_unsafe_characters() -> None:
    assert safe_filename("../../notice file?.pdf", "evidence") == "notice_file_.pdf"


def test_upload_signature_requires_matching_content() -> None:
    valid = UploadFile(filename="clip.mp4", file=BytesIO(b"\x00\x00\x00\x18ftypisom"))
    invalid = UploadFile(filename="clip.mp4", file=BytesIO(b"not a video"))
    assert asyncio.run(validate_upload_signature(valid, "video")) == "clip.mp4"
    with pytest.raises(ValueError, match="content"):
        asyncio.run(validate_upload_signature(invalid, "video"))


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter()
    assert limiter.allow("creator", limit=2)
    assert limiter.allow("creator", limit=2)
    assert not limiter.allow("creator", limit=2)


def test_storage_rejects_path_traversal() -> None:
    storage = StorageService()
    with pytest.raises(ValueError, match="storage key"):
        storage.local_path("../outside.txt")
