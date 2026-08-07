from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..models.entities import Incident, IncidentEvidence, ProofRecord
from ..services.storage import StorageService

storage = StorageService()

def next_incident_id(db: Session) -> str:
    count = db.scalar(select(Incident.id).order_by(Incident.id.desc()).limit(1)) or 0
    return f"INC-{datetime.now(timezone.utc).year}-{int(count)+1:04d}"

def find_incident(db: Session, incident_id: str, user_id: str) -> Incident | None:
    return db.scalar(select(Incident).options(joinedload(Incident.evidence)).where(Incident.incident_id == incident_id, Incident.user_id == user_id))

def serialize_incident(incident: Incident) -> dict:
    return {"incident_id": incident.incident_id, "proof_id": incident.proof_id, "suspicious_filename": incident.suspicious_filename, "suspicious_file_size": incident.suspicious_file_size, "suspicious_username": incident.suspicious_username, "claimed_publication_date": incident.claimed_publication_date, "suspicious_url": incident.suspicious_url, "caption": incident.caption, "notes": incident.notes, "status": incident.status, "stage": incident.stage, "created_at": incident.created_at.isoformat() if incident.created_at else None, "suspicious_media_url": storage.signed_url(incident.suspicious_storage_key), "events": json.loads(incident.events_json or "[]"), "visual_similarity": incident.visual_similarity, "audio_similarity": incident.audio_similarity, "transcript_similarity": incident.transcript_similarity, "timeline_confidence": incident.timeline_confidence, "combined_similarity": incident.combined_similarity, "matching_segments": incident.matching_segments, "matching_audio_seconds": incident.matching_audio_seconds, "modifications": json.loads(incident.modifications_json or "[]"), "complaint_extraction": json.loads(incident.complaint_extraction_json or "{}"), "suspicion_score": incident.suspicion_score, "suspicion_band": incident.suspicion_band, "suspicion_indicators": json.loads(incident.suspicion_indicators_json or "[]"), "community_matches": json.loads(incident.community_matches_json or "[]"), "community_summary": json.loads(incident.community_summary_json or "{}"), "evidence": [{"filename": item.filename, "content_type": item.content_type, "file_size": item.file_size, "media_url": storage.signed_url(item.storage_key)} for item in incident.evidence]}

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
