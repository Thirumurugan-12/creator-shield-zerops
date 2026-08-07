from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .db.base import Base
from .db.session import SessionLocal, engine, get_db
from .models.entities import Incident, IncidentEvidence, ProcessingJob, ProofRecord
from .repositories.proofs import add_event, get_or_create_demo_user, get_proof as find_proof, list_proofs as query_proofs, next_proof_id, serialize_proof
from .services.queue import ProofQueue
from .services.storage import StorageService
from .services.processing import process_proof
from .api.routes.auth import get_current_user, router as auth_router
from .schemas.proofs import ProofMetadata
from .schemas.incidents import IncidentMetadata
from pydantic import ValidationError
from .repositories.incidents import find_incident, next_incident_id, serialize_incident
from .services.comparison import compare_incident
from .services.community import seed_simulated_reports

Base.metadata.create_all(bind=engine)
seed_simulated_reports()
storage = StorageService()
queue = ProofQueue()
app = FastAPI(title="CreatorShield API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)


@app.get("/media/{path:path}")
def get_private_media(path: str, expires: int = Query(...), signature: str = Query(...)) -> FileResponse:
    if storage.backend != "local" or not storage.verify_signature(path, expires, signature):
        raise HTTPException(404, "Media not found")
    target = (storage.root / path).resolve()
    if storage.root.resolve() not in target.parents or not target.is_file():
        raise HTTPException(404, "Media not found")
    return FileResponse(target)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(select(1))
    return {"status": "ok"}


@app.get("/api/proofs")
def list_proofs(search: str | None = None, status: str | None = None, page: int = 1, page_size: int = 50, db: Session = Depends(get_db), user=Depends(get_current_user)) -> list[dict[str, Any]]:
    return query_proofs(db, search, status, user.id, page=max(page, 1), page_size=min(max(page_size, 1), 100))


@app.get("/api/proofs/{proof_id}")
def get_proof(proof_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)) -> dict[str, Any]:
    proof = find_proof(db, proof_id, user.id)
    if not proof:
        raise HTTPException(404, "Proof not found")
    return serialize_proof(proof)


@app.get("/api/proofs/{proof_id}/events")
def get_events(proof_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)) -> list[dict[str, str]]:
    proof = find_proof(db, proof_id, user.id)
    if not proof:
        raise HTTPException(404, "Proof not found")
    return [{"timestamp": event.created_at.isoformat() if event.created_at else "", "message": event.message} for event in proof.events]


@app.get("/api/incidents")
def list_incidents(db: Session = Depends(get_db), user=Depends(get_current_user)) -> list[dict[str, Any]]:
    incidents = db.scalars(select(Incident).options(joinedload(Incident.evidence)).where(Incident.user_id == user.id).order_by(Incident.created_at.desc())).unique().all()
    return [serialize_incident(incident) for incident in incidents]


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)) -> dict[str, Any]:
    incident = find_incident(db, incident_id, user.id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return serialize_incident(incident)


@app.post("/api/incidents", status_code=202)
async def create_incident(
    background_tasks: BackgroundTasks,
    original_proof_id: str = Form(...),
    file: UploadFile = File(...),
    suspicious_username: str = Form(...),
    claimed_publication_date: str = Form(...),
    suspicious_url: str = Form(""),
    caption: str = Form(""),
    notes: str = Form(""),
    evidence_files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    proof = find_proof(db, original_proof_id, user.id)
    if not proof:
        raise HTTPException(404, "Original proof not found")
    allowed_video = {"video/mp4", "video/quicktime", "video/webm", "application/octet-stream"}
    if file.content_type not in allowed_video and not (file.filename or "").lower().endswith((".mp4", ".mov", ".webm")):
        raise HTTPException(400, "Suspicious copy must be an MP4, MOV, or WebM file")
    try:
        metadata = IncidentMetadata(suspicious_username=suspicious_username, claimed_publication_date=claimed_publication_date, suspicious_url=suspicious_url, caption=caption, notes=notes)
    except ValidationError as error:
        raise HTTPException(422, detail=error.errors()) from error
    allowed_evidence = {"image/png", "image/jpeg", "application/pdf"}
    for evidence in evidence_files[:5]:
        suffix = Path(evidence.filename or "").suffix.lower()
        if evidence.content_type not in allowed_evidence and suffix not in {".png", ".jpg", ".jpeg", ".pdf"}:
            raise HTTPException(400, "Complaint evidence must be PNG, JPG, JPEG, or PDF")
    video_suffix = Path(file.filename or "suspicious.mp4").suffix.lower() or ".mp4"
    video_key = f"incidents/{uuid.uuid4().hex}/suspicious{video_suffix}"
    try:
        size, video_key, digest = storage.save(file.file, video_key)
    except ValueError as error:
        raise HTTPException(413, str(error)) from error
    incident = Incident(incident_id=next_incident_id(db), user_id=user.id, proof_id=proof.id, suspicious_storage_key=video_key, suspicious_filename=file.filename or "suspicious.mp4", suspicious_file_size=size, suspicious_sha256=digest, suspicious_username=metadata.suspicious_username, claimed_publication_date=metadata.claimed_publication_date.isoformat(), suspicious_url=metadata.suspicious_url, caption=metadata.caption, notes=metadata.notes, status="queued", stage="queued", events_json=json.dumps([{ "timestamp": datetime.now(timezone.utc).isoformat(), "message": "Suspicious copy secured in private storage" }]))
    db.add(incident)
    db.flush()
    for evidence in evidence_files[:5]:
        evidence_key = f"incidents/{incident.incident_id}/{uuid.uuid4().hex}-{Path(evidence.filename or 'evidence').name}"
        try:
            evidence_size, evidence_key, evidence_digest = storage.save(evidence.file, evidence_key)
        except ValueError as error:
            raise HTTPException(413, str(error)) from error
        db.add(IncidentEvidence(incident_id=incident.id, storage_key=evidence_key, filename=evidence.filename or "evidence", content_type=evidence.content_type or "application/octet-stream", file_size=evidence_size, sha256=evidence_digest))
    db.commit()
    db.refresh(incident)
    if not queue.enqueue_incident(incident.incident_id):
        background_tasks.add_task(compare_incident, incident.incident_id)
    return serialize_incident(incident)


@app.post("/api/proofs/{proof_id}/retry", status_code=202)
def retry_proof(proof_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(get_current_user)) -> dict[str, Any]:
    proof = find_proof(db, proof_id, user.id)
    if not proof:
        raise HTTPException(404, "Proof not found")
    if proof.status != "failed":
        raise HTTPException(409, "Only failed proofs can be retried")
    proof.status, proof.current_step, proof.progress = "processing", "queued", 8
    job = ProcessingJob(proof_id=proof.id, status="queued")
    db.add(job)
    add_event(db, proof, "Processing retry queued")
    db.commit()
    if not queue.enqueue(proof.proof_id):
        background_tasks.add_task(process_proof, proof.proof_id)
    return serialize_proof(proof)


@app.post("/api/proofs", status_code=202)
async def create_proof(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    instagram_username: str = Form(...),
    claimed_publication_date: str = Form(...),
    claimed_publication_url: str = Form(""),
    caption: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    allowed = {"video/mp4", "video/quicktime", "video/webm", "application/octet-stream"}
    if file.content_type not in allowed and not (file.filename or "").lower().endswith((".mp4", ".mov", ".webm")):
        raise HTTPException(400, "Upload an MP4, MOV, or WebM file")
    try:
        metadata = ProofMetadata(title=title, instagram_username=instagram_username, claimed_publication_date=claimed_publication_date, claimed_publication_url=claimed_publication_url)
    except ValidationError as error:
        raise HTTPException(422, detail=error.errors()) from error
    title = metadata.title
    username = metadata.instagram_username
    claimed_publication_date = metadata.claimed_publication_date.isoformat()
    claimed_publication_url = metadata.claimed_publication_url
    suffix = Path(file.filename or "reel.mp4").suffix.lower() or ".mp4"
    storage_key = f"originals/{uuid.uuid4().hex}{suffix}"
    try:
        size, storage_key, sha256 = storage.save(file.file, storage_key)
    except ValueError as error:
        raise HTTPException(413, str(error)) from error
    duplicate = db.scalar(select(ProofRecord).where(ProofRecord.user_id == user.id, ProofRecord.sha256 == sha256))
    if duplicate:
        storage.delete(storage_key)
        raise HTTPException(409, f"This file is already registered as {duplicate.proof_id}")
    proof = ProofRecord(
        proof_id=next_proof_id(db), user_id=user.id, title=title, instagram_username=username,
        claimed_publication_date=claimed_publication_date, claimed_publication_url=claimed_publication_url,
        caption=caption, notes=notes, original_filename=file.filename or "reel.mp4", storage_key=storage_key,
        file_size=size, sha256=sha256, status="processing", current_step="upload", progress=8, evidence_completeness=10,
    )
    db.add(proof)
    db.flush()
    add_event(db, proof, "Upload secured in private storage")
    job = ProcessingJob(proof_id=proof.id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(proof)
    if not queue.enqueue(proof.proof_id):
        background_tasks.add_task(process_proof, proof.proof_id)
    return serialize_proof(proof)
