from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from .db.base import Base
from .db.session import SessionLocal, engine, get_db
from .models.entities import Incident, IncidentEvidence, MediaBlob, ProcessingEvent, ProcessingJob, ProofRecord
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
from .services.reports import build_report_context, generate_report_pdf
from .services.rate_limit import InMemoryRateLimiter
from .services.upload_security import malware_scan_hook, safe_filename, validate_upload_signature

Base.metadata.create_all(bind=engine)
seed_simulated_reports()
storage = StorageService()
queue = ProofQueue()
rate_limiter = InMemoryRateLimiter()
app = FastAPI(title="CreatorShield API", version="1.0.0")
cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "X-Requested-With"])
app.include_router(auth_router)
logger = logging.getLogger(__name__)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


def enforce_rate_limit(key: str, limit: int = 10) -> None:
    if not rate_limiter.allow(key, limit=limit):
        raise HTTPException(429, "Too many requests. Please try again shortly.")


@app.get("/media/{path:path}")
def get_private_media(path: str, expires: int = Query(...), signature: str = Query(...)) -> FileResponse:
    if storage.backend != "local" or not storage.verify_signature(path, expires, signature):
        raise HTTPException(404, "Media not found")
    target = (storage.root / path).resolve()
    if storage.root.resolve() not in target.parents or not target.is_file():
        raise HTTPException(404, "Media not found")
    return FileResponse(target)


@app.get("/health")
@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(select(1))
    return {"status": "ok", "storage_backend": storage.backend}


def mirror_media(db: Session, key: str, payload: bytes) -> None:
    db.merge(MediaBlob(storage_key=key, payload=payload))


def remove_media(key: str) -> None:
    try:
        storage.delete(key)
    except Exception:
        logger.warning("Media cleanup skipped for %s", key, exc_info=True)


@app.delete("/api/incidents/{incident_id}")
def delete_incident(incident_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)) -> dict[str, str]:
    incident = find_incident(db, incident_id, user.id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    remove_media(incident.suspicious_storage_key)
    db.execute(delete(MediaBlob).where(MediaBlob.storage_key == incident.suspicious_storage_key))
    for evidence in incident.evidence:
        remove_media(evidence.storage_key)
        db.execute(delete(MediaBlob).where(MediaBlob.storage_key == evidence.storage_key))
    db.delete(incident)
    db.commit()
    return {"status": "deleted"}


@app.delete("/api/proofs/{proof_id}")
def delete_proof(proof_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)) -> dict[str, str]:
    proof = find_proof(db, proof_id, user.id)
    if not proof:
        raise HTTPException(404, "Proof not found")
    incidents = db.scalars(select(Incident).options(joinedload(Incident.evidence)).where(Incident.proof_id == proof.id)).unique().all()
    for incident in incidents:
        remove_media(incident.suspicious_storage_key)
        db.execute(delete(MediaBlob).where(MediaBlob.storage_key == incident.suspicious_storage_key))
        for evidence in incident.evidence:
            remove_media(evidence.storage_key)
            db.execute(delete(MediaBlob).where(MediaBlob.storage_key == evidence.storage_key))
        db.delete(incident)
    remove_media(proof.storage_key)
    db.execute(delete(MediaBlob).where(MediaBlob.storage_key == proof.storage_key))
    db.execute(delete(ProcessingEvent).where(ProcessingEvent.proof_id == proof.id))
    db.execute(delete(ProcessingJob).where(ProcessingJob.proof_id == proof.id))
    db.delete(proof)
    db.commit()
    return {"status": "deleted"}


def save_upload_with_fallback(file: UploadFile, key: str, payload: bytes) -> tuple[int, str, str]:
    """Save to object storage, retaining a DB-readable copy if the storage API is unavailable."""
    file.file.seek(0)
    try:
        return storage.save(file.file, key)
    except Exception:
        # Zerops Object Storage can transiently reject a PUT while the rest of
        # the request is healthy. The PostgreSQL mirror is the worker's shared
        # read path, so an upload should still be accepted and processed.
        logger.exception("Object storage upload failed for %s; using PostgreSQL media mirror", key)
        return len(payload), key, hashlib.sha256(payload).hexdigest()


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


@app.get("/api/incidents/{incident_id}/report")
def preview_incident_report(incident_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)) -> dict[str, Any]:
    incident = find_incident(db, incident_id, user.id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    proof = db.get(ProofRecord, incident.proof_id)
    if not proof:
        raise HTTPException(404, "Original proof not found")
    return build_report_context(incident, proof)


@app.get("/api/incidents/{incident_id}/report.pdf")
def download_incident_report(incident_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)) -> Response:
    enforce_rate_limit(f"report:{user.id}", limit=20)
    incident = find_incident(db, incident_id, user.id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    proof = db.get(ProofRecord, incident.proof_id)
    if not proof:
        raise HTTPException(404, "Original proof not found")
    content = generate_report_pdf(build_report_context(incident, proof))
    events = json.loads(incident.events_json or "[]")
    events.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": "Evidence report downloaded"})
    incident.events_json = json.dumps(events)
    db.commit()
    return Response(content=content, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{incident.incident_id}-evidence-report.pdf"'})


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
    enforce_rate_limit(f"incident-upload:{user.id}")
    proof = find_proof(db, original_proof_id, user.id)
    if not proof:
        raise HTTPException(404, "Original proof not found")
    allowed_video = {"video/mp4", "video/quicktime", "video/webm", "application/octet-stream"}
    if file.content_type not in allowed_video and not (file.filename or "").lower().endswith((".mp4", ".mov", ".webm")):
        raise HTTPException(400, "Suspicious copy must be an MP4, MOV, or WebM file")
    try:
        video_filename = await validate_upload_signature(file, "video")
        malware_scan_hook(file)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    try:
        metadata = IncidentMetadata(suspicious_username=suspicious_username, claimed_publication_date=claimed_publication_date, suspicious_url=suspicious_url, caption=caption, notes=notes)
    except ValidationError as error:
        raise HTTPException(422, detail=error.errors()) from error
    allowed_evidence = {"image/png", "image/jpeg", "application/pdf"}
    for evidence in evidence_files[:5]:
        suffix = Path(safe_filename(evidence.filename, "evidence")).suffix.lower()
        if evidence.content_type not in allowed_evidence and suffix not in {".png", ".jpg", ".jpeg", ".pdf"}:
            raise HTTPException(400, "Complaint evidence must be PNG, JPG, JPEG, or PDF")
        try:
            await validate_upload_signature(evidence, "evidence")
            malware_scan_hook(evidence)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
    video_suffix = Path(video_filename).suffix.lower() or ".mp4"
    video_key = f"incidents/{uuid.uuid4().hex}/suspicious{video_suffix}"
    try:
        file.file.seek(0)
        video_payload = file.file.read()
        file.file.seek(0)
        size, video_key, digest = save_upload_with_fallback(file, video_key, video_payload)
    except ValueError as error:
        raise HTTPException(413, str(error)) from error
    incident = Incident(incident_id=next_incident_id(db), user_id=user.id, proof_id=proof.id, suspicious_storage_key=video_key, suspicious_filename=video_filename, suspicious_file_size=size, suspicious_sha256=digest, suspicious_username=metadata.suspicious_username, claimed_publication_date=metadata.claimed_publication_date.isoformat(), suspicious_url=metadata.suspicious_url, caption=metadata.caption, notes=metadata.notes, status="queued", stage="queued", events_json=json.dumps([{ "timestamp": datetime.now(timezone.utc).isoformat(), "message": "Suspicious copy secured in private storage" }]))
    db.add(incident)
    mirror_media(db, video_key, video_payload)
    db.flush()
    for evidence in evidence_files[:5]:
        evidence_key = f"incidents/{incident.incident_id}/{uuid.uuid4().hex}-{Path(evidence.filename or 'evidence').name}"
        try:
            evidence.file.seek(0)
            evidence_payload = evidence.file.read()
            evidence.file.seek(0)
            evidence_size, evidence_key, evidence_digest = save_upload_with_fallback(evidence, evidence_key, evidence_payload)
        except ValueError as error:
            raise HTTPException(413, str(error)) from error
        db.add(IncidentEvidence(incident_id=incident.id, storage_key=evidence_key, filename=evidence.filename or "evidence", content_type=evidence.content_type or "application/octet-stream", file_size=evidence_size, sha256=evidence_digest))
        mirror_media(db, evidence_key, evidence_payload)
    db.commit()
    db.refresh(incident)
    if not queue.enqueue_incident(incident.incident_id):
        background_tasks.add_task(compare_incident, incident.incident_id)
    return serialize_incident(incident)


@app.post("/api/proofs/{proof_id}/retry", status_code=202)
def retry_proof(proof_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(get_current_user)) -> dict[str, Any]:
    enforce_rate_limit(f"proof-retry:{user.id}", limit=10)
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
    enforce_rate_limit(f"proof-upload:{user.id}")
    allowed = {"video/mp4", "video/quicktime", "video/webm", "application/octet-stream"}
    if file.content_type not in allowed and not (file.filename or "").lower().endswith((".mp4", ".mov", ".webm")):
        raise HTTPException(400, "Upload an MP4, MOV, or WebM file")
    try:
        safe_original_filename = await validate_upload_signature(file, "video")
        malware_scan_hook(file)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    try:
        metadata = ProofMetadata(title=title, instagram_username=instagram_username, claimed_publication_date=claimed_publication_date, claimed_publication_url=claimed_publication_url)
    except ValidationError as error:
        raise HTTPException(422, detail=error.errors()) from error
    title = metadata.title
    username = metadata.instagram_username
    claimed_publication_date = metadata.claimed_publication_date.isoformat()
    claimed_publication_url = metadata.claimed_publication_url
    suffix = Path(safe_original_filename).suffix.lower() or ".mp4"
    storage_key = f"originals/{uuid.uuid4().hex}{suffix}"
    try:
        file.file.seek(0)
        video_payload = file.file.read()
        file.file.seek(0)
        size, storage_key, sha256 = save_upload_with_fallback(file, storage_key, video_payload)
    except ValueError as error:
        raise HTTPException(413, str(error)) from error
    duplicate = db.scalar(select(ProofRecord).where(ProofRecord.user_id == user.id, ProofRecord.sha256 == sha256))
    if duplicate:
        storage.delete(storage_key)
        raise HTTPException(409, f"This file is already registered as {duplicate.proof_id}")
    proof = ProofRecord(
        proof_id=next_proof_id(db), user_id=user.id, title=title, instagram_username=username,
        claimed_publication_date=claimed_publication_date, claimed_publication_url=claimed_publication_url,
        caption=caption, notes=notes, original_filename=safe_original_filename, storage_key=storage_key,
        file_size=size, sha256=sha256, status="processing", current_step="upload", progress=8, evidence_completeness=10,
    )
    db.add(proof)
    mirror_media(db, storage_key, video_payload)
    db.flush()
    add_event(db, proof, "Upload secured in private storage")
    job = ProcessingJob(proof_id=proof.id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(proof)
    if not queue.enqueue(proof.proof_id):
        background_tasks.add_task(process_proof, proof.proof_id)
    return serialize_proof(proof)
