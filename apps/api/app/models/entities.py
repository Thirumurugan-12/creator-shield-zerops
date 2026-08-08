from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float, LargeBinary, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120))
    instagram_username: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    proofs: Mapped[list["ProofRecord"]] = relationship(back_populates="user")


class ProofRecord(Base):
    __tablename__ = "proofs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proof_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    instagram_username: Mapped[str] = mapped_column(String(120))
    claimed_publication_date: Mapped[str] = mapped_column(String(32))
    claimed_publication_url: Mapped[str] = mapped_column(String(500), default="")
    caption: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="processing", index=True)
    current_step: Mapped[str] = mapped_column(String(64), default="upload")
    progress: Mapped[int] = mapped_column(Integer, default=8)
    evidence_completeness: Mapped[int] = mapped_column(Integer, default=10)
    duration: Mapped[float | None] = mapped_column(nullable=True)
    width: Mapped[int | None] = mapped_column(nullable=True)
    height: Mapped[int | None] = mapped_column(nullable=True)
    codec: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frame_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    audio_present: Mapped[bool | None] = mapped_column(nullable=True)
    audio_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    keyframes_json: Mapped[str] = mapped_column(Text, default="[]")
    transcript_status: Mapped[str] = mapped_column(String(32), default="unavailable")
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    user: Mapped[User] = relationship(back_populates="proofs")
    events: Mapped[list["ProcessingEvent"]] = relationship(back_populates="proof", cascade="all, delete-orphan")
    jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="proof", cascade="all, delete-orphan")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proof_id: Mapped[int] = mapped_column(ForeignKey("proofs.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    proof: Mapped[ProofRecord] = relationship(back_populates="jobs")


class MediaBlob(Base):
    """Durable fallback mirror for media when private object storage lags."""

    __tablename__ = "media_blobs"

    storage_key: Mapped[str] = mapped_column(String(500), primary_key=True)
    payload: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessingEvent(Base):
    __tablename__ = "processing_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proof_id: Mapped[int] = mapped_column(ForeignKey("proofs.id"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("processing_jobs.id"), nullable=True, index=True)
    message: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    proof: Mapped[ProofRecord] = relationship(back_populates="events")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    proof_id: Mapped[int] = mapped_column(ForeignKey("proofs.id"), index=True)
    suspicious_storage_key: Mapped[str] = mapped_column(String(500))
    suspicious_filename: Mapped[str] = mapped_column(String(255))
    suspicious_file_size: Mapped[int] = mapped_column(Integer)
    suspicious_sha256: Mapped[str] = mapped_column(String(64))
    suspicious_username: Mapped[str] = mapped_column(String(120))
    claimed_publication_date: Mapped[str] = mapped_column(String(32))
    suspicious_url: Mapped[str] = mapped_column(String(500), default="")
    caption: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    stage: Mapped[str] = mapped_column(String(64), default="queued")
    events_json: Mapped[str] = mapped_column(Text, default="[]")
    visual_similarity: Mapped[float | None] = mapped_column(nullable=True)
    audio_similarity: Mapped[float | None] = mapped_column(nullable=True)
    transcript_similarity: Mapped[float | None] = mapped_column(nullable=True)
    timeline_confidence: Mapped[float | None] = mapped_column(nullable=True)
    combined_similarity: Mapped[float | None] = mapped_column(nullable=True)
    matching_segments: Mapped[int | None] = mapped_column(nullable=True)
    matching_audio_seconds: Mapped[float | None] = mapped_column(nullable=True)
    modifications_json: Mapped[str] = mapped_column(Text, default="[]")
    complaint_extraction_json: Mapped[str] = mapped_column(Text, default="{}")
    suspicion_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    suspicion_band: Mapped[str | None] = mapped_column(String(32), nullable=True)
    suspicion_indicators_json: Mapped[str] = mapped_column(Text, default="[]")
    community_matches_json: Mapped[str] = mapped_column(Text, default="[]")
    community_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    evidence: Mapped[list["IncidentEvidence"]] = relationship(back_populates="incident", cascade="all, delete-orphan")


class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    storage_key: Mapped[str] = mapped_column(String(500))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    file_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    incident: Mapped[Incident] = relationship(back_populates="evidence")


class SimulatedReport(Base):
    __tablename__ = "simulated_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    claimant_email: Mapped[str] = mapped_column(String(255), default="", index=True)
    claimant_phone: Mapped[str] = mapped_column(String(64), default="", index=True)
    claimant_username: Mapped[str] = mapped_column(String(120), default="", index=True)
    claimant_domain: Mapped[str] = mapped_column(String(255), default="", index=True)
    payment_identifier: Mapped[str] = mapped_column(String(120), default="", index=True)
    message_fingerprint: Mapped[str] = mapped_column(String(64), default="", index=True)
    attachment_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    repeated_wording: Mapped[str] = mapped_column(Text, default="")
    payment_demand_count: Mapped[int] = mapped_column(Integer, default=0)
    creator_restriction_count: Mapped[int] = mapped_column(Integer, default=0)
    first_recorded_date: Mapped[str] = mapped_column(String(32))
