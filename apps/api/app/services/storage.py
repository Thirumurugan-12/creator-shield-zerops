from __future__ import annotations

import os
import hashlib
import hmac
import time
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator


class StorageService:
    """Private storage adapter. Local storage is used by default; S3-compatible storage is supported by configuration."""

    def __init__(self) -> None:
        self.backend = os.getenv("STORAGE_BACKEND", "local")
        self.root = Path(os.getenv("STORAGE_PATH", "/tmp/creatorshield/uploads"))
        self.root.mkdir(parents=True, exist_ok=True)
        self.secret = os.getenv("MEDIA_SIGNING_SECRET", "creatorshield-local-dev-secret").encode()

    def signed_url(self, key: str, ttl_seconds: int = 3600) -> str:
        self._validate_key(key)
        expires = int(time.time()) + ttl_seconds
        if self.backend == "s3":
            import boto3

            client = boto3.client("s3", endpoint_url=os.getenv("S3_ENDPOINT_URL") or None)
            return client.generate_presigned_url("get_object", Params={"Bucket": os.environ["S3_BUCKET"], "Key": key}, ExpiresIn=ttl_seconds)
        signature = self._signature(key, expires)
        return f"/media/{key}?expires={expires}&signature={signature}"

    def verify_signature(self, key: str, expires: int, signature: str) -> bool:
        try:
            self._validate_key(key)
        except ValueError:
            return False
        return expires >= int(time.time()) and hmac.compare_digest(signature, self._signature(key, expires))

    def _signature(self, key: str, expires: int) -> str:
        return hmac.new(self.secret, f"{key}:{expires}".encode(), hashlib.sha256).hexdigest()

    def save(self, source: BinaryIO, key: str) -> tuple[int, str, str]:
        self._validate_key(key)
        if self.backend == "s3":
            return self._save_s3(source, key)
        target = self.root / key
        target.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        with target.open("wb") as output:
            while chunk := source.read(1024 * 1024):
                total += len(chunk)
                if total > 100 * 1024 * 1024:
                    target.unlink(missing_ok=True)
                    raise ValueError("Maximum upload size is 100 MB")
                output.write(chunk)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        return total, key, digest

    def delete(self, key: str) -> None:
        self._validate_key(key)
        if self.backend == "s3":
            import boto3

            client = boto3.client("s3", endpoint_url=os.getenv("S3_ENDPOINT_URL") or None)
            client.delete_object(Bucket=os.environ["S3_BUCKET"], Key=key)
            return
        target = (self.root / key).resolve()
        if self.root.resolve() in target.parents:
            target.unlink(missing_ok=True)

    def local_path(self, key: str) -> Path:
        self._validate_key(key)
        target = (self.root / key).resolve()
        if self.root.resolve() not in target.parents:
            raise ValueError("Invalid storage key")
        return target

    @contextmanager
    def materialize(self, key: str) -> Iterator[Path]:
        """Yield a local path for media, downloading S3 objects when required."""
        if self.backend != "s3":
            yield self.local_path(key)
            return
        import boto3

        self._validate_key(key)
        with tempfile.NamedTemporaryFile(suffix=Path(key).suffix) as temporary:
            client = boto3.client("s3", endpoint_url=os.getenv("S3_ENDPOINT_URL") or None)
            client.download_fileobj(os.environ["S3_BUCKET"], key, temporary)
            temporary.flush()
            yield Path(temporary.name)

    def _validate_key(self, key: str) -> None:
        candidate = Path(key)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("Invalid storage key")

    def _save_s3(self, source: BinaryIO, key: str) -> tuple[int, str, str]:
        import boto3

        with tempfile.NamedTemporaryFile() as temporary:
            total = 0
            digest = hashlib.sha256()
            while chunk := source.read(1024 * 1024):
                total += len(chunk)
                if total > 100 * 1024 * 1024:
                    raise ValueError("Maximum upload size is 100 MB")
                temporary.write(chunk)
                digest.update(chunk)
            temporary.flush()
            client = boto3.client("s3", endpoint_url=os.getenv("S3_ENDPOINT_URL") or None)
            client.upload_file(temporary.name, os.environ["S3_BUCKET"], key, ExtraArgs={"ServerSideEncryption": "AES256"})
        return total, key, digest.hexdigest()
