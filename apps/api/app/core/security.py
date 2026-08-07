from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time

SESSION_COOKIE = "creatorshield_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7
SECRET = os.getenv("SESSION_SECRET", "creatorshield-local-session-secret").encode()


def create_session(user_id: str) -> str:
    expires = int(time.time()) + SESSION_MAX_AGE
    payload = f"{user_id}.{expires}"
    encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    signature = hmac.new(SECRET, encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def read_session(token: str | None) -> str | None:
    if not token or "." not in token:
        return None
    encoded, signature = token.rsplit(".", 1)
    expected = hmac.new(SECRET, encoded.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        padded = encoded + "=" * (-len(encoded) % 4)
        user_id, expires = base64.urlsafe_b64decode(padded).decode().rsplit(".", 1)
        if int(expires) < int(time.time()):
            return None
        return user_id
    except (ValueError, UnicodeDecodeError):
        return None
