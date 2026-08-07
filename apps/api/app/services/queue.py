from __future__ import annotations

import os


class ProofQueue:
    """Redis/Valkey-backed queue with a safe local fallback when Redis is unavailable."""

    key = "creatorshield:proof-processing"
    incident_key = "creatorshield:incident-processing"

    def __init__(self) -> None:
        self.url = os.getenv("REDIS_URL", "")

    def enqueue(self, proof_id: str) -> bool:
        if not self.url:
            return False
        try:
            import redis

            redis.Redis.from_url(self.url, decode_responses=True).lpush(self.key, proof_id)
            return True
        except Exception:
            return False

    def dequeue(self) -> str | None:
        if not self.url:
            return None
        import redis

        result = redis.Redis.from_url(self.url, decode_responses=True).brpop(self.key, timeout=5)
        return result[1] if result else None

    def enqueue_incident(self, incident_id: str) -> bool:
        if not self.url:
            return False
        try:
            import redis
            redis.Redis.from_url(self.url, decode_responses=True).lpush(self.incident_key, incident_id)
            return True
        except Exception:
            return False

    def dequeue_incident(self) -> str | None:
        if not self.url:
            return None
        import redis
        result = redis.Redis.from_url(self.url, decode_responses=True).brpop(self.incident_key, timeout=1)
        return result[1] if result else None
