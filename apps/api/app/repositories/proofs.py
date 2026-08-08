from __future__ import annotations

from datetime import datetime, timezone
import json

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..models.entities import ProcessingEvent, ProcessingJob, ProofRecord, User
from ..services.storage import StorageService

storage = StorageService()


def get_or_create_demo_user(db: Session, username: str) -> User:
    user = db.scalar(select(User).where(User.email == "demo@creatorshield.local"))
    if user:
        user.display_name = "Thiru"
        user.instagram_username = username
        return user
    user = User(id="demo-creator", display_name="Thiru", instagram_username=username, email="demo@creatorshield.local")
    db.add(user)
    db.flush()
    return user


def next_proof_id(db: Session) -> str:
    count = db.scalar(select(ProofRecord.id).order_by(ProofRecord.id.desc()).limit(1)) or 0
    return f"CS-{datetime.now(timezone.utc).year}-{int(count) + 1:04d}"


def add_event(db: Session, proof: ProofRecord, message: str, job: ProcessingJob | None = None) -> ProcessingEvent:
    event = ProcessingEvent(proof_id=proof.id, job_id=job.id if job else None, message=message)
    db.add(event)
    db.flush()
    return event


def serialize_proof(proof: ProofRecord) -> dict:
    return {
        "proof_id": proof.proof_id, "title": proof.title, "instagram_username": proof.instagram_username,
        "claimed_publication_date": proof.claimed_publication_date, "claimed_publication_url": proof.claimed_publication_url,
        "caption": proof.caption, "notes": proof.notes, "original_filename": proof.original_filename,
        "file_size": proof.file_size, "sha256": proof.sha256, "status": proof.status, "current_step": proof.current_step,
        "progress": proof.progress, "evidence_completeness": proof.evidence_completeness, "created_at": proof.created_at.isoformat() if proof.created_at else None,
        "duration": proof.duration, "width": proof.width, "height": proof.height, "codec": proof.codec, "frame_rate": proof.frame_rate,
        "audio_present": proof.audio_present, "audio_fingerprint": proof.audio_fingerprint,
        "keyframes": [{**frame, "storage_url": storage.signed_url(frame["storage_key"])} for frame in json.loads(proof.keyframes_json or "[]")],
        "transcript": proof.transcript, "transcript_status": proof.transcript_status,
        "media_url": storage.signed_url(proof.storage_key),
        "events": [{"timestamp": event.created_at.isoformat() if event.created_at else None, "message": event.message} for event in proof.events],
    }


def list_proofs(db: Session, search: str | None, status: str | None, user_id: str, page: int = 1, page_size: int = 50) -> list[dict]:
    query = select(ProofRecord).options(joinedload(ProofRecord.events)).order_by(ProofRecord.created_at.desc())
    query = query.where(ProofRecord.user_id == user_id)
    if search:
        query = query.where(ProofRecord.title.ilike(f"%{search}%") | ProofRecord.proof_id.ilike(f"%{search}%"))
    if status and status != "all":
        query = query.where(ProofRecord.status == status)
    query = query.offset((page - 1) * page_size).limit(page_size)
    return [serialize_proof(proof) for proof in db.scalars(query).unique().all()]


def get_proof(db: Session, proof_id: str, user_id: str | None = None) -> ProofRecord | None:
    query = select(ProofRecord).options(joinedload(ProofRecord.events)).where(ProofRecord.proof_id == proof_id)
    if user_id:
        query = query.where(ProofRecord.user_id == user_id)
    return db.scalar(query)
