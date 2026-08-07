from __future__ import annotations

import threading
import time


class InMemoryRateLimiter:
    """Small local guard; production deployments should use Valkey for shared limits."""

    def __init__(self) -> None:
        self._events: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int = 10, window_seconds: int = 60) -> bool:
        now = time.monotonic()
        with self._lock:
            recent = [stamp for stamp in self._events.get(key, []) if now - stamp < window_seconds]
            if len(recent) >= limit:
                self._events[key] = recent
                return False
            recent.append(now)
            self._events[key] = recent
            return True
