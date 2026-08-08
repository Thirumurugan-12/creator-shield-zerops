from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

from sqlalchemy import select

from ..db.session import SessionLocal
from ..models.entities import ProcessingJob
from ..repositories.proofs import add_event, get_proof
from .storage import StorageService

storage = StorageService()


def media_binary(name: str) -> str:
    """Resolve FFmpeg tools in Docker or provision static tools on Zerops."""
    system_binary = shutil.which(name)
    if system_binary:
        return system_binary
    try:
        from static_ffmpeg import run

        download_dir = os.getenv("CREATORSHIELD_FFMPEG_DIR", "/tmp/creatorshield-ffmpeg")
        ffmpeg, ffprobe = run.get_or_fetch_platform_executables_else_raise(download_dir=download_dir)
        return ffmpeg if name == "ffmpeg" else ffprobe
    except Exception as error:
        raise RuntimeError(f"{name} is unavailable; media processing cannot start") from error


def _run(command: list[str], *, output: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, stdout=subprocess.PIPE if output else subprocess.DEVNULL, stderr=subprocess.PIPE)


def perceptual_hash(image) -> str:
    grayscale = image.convert("L").resize((8, 8))
    pixels = list(grayscale.getdata())
    average = sum(pixels) / len(pixels)
    return "".join("1" if pixel >= average else "0" for pixel in pixels)


def extract_metadata(path: Path) -> dict:
    result = _run([media_binary("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    payload = json.loads(result.stdout)
    video = next((stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"), None)
    if not video:
        raise ValueError("No video stream found")
    frame_rate = None
    if video.get("r_frame_rate") and video["r_frame_rate"] != "0/0":
        frame_rate = float(Fraction(video["r_frame_rate"]))
    return {"duration": float(payload.get("format", {}).get("duration", 0) or 0), "width": video.get("width"), "height": video.get("height"), "codec": video.get("codec_name"), "frame_rate": frame_rate, "audio_present": any(stream.get("codec_type") == "audio" for stream in payload.get("streams", []))}


def extract_keyframes(path: Path, proof_id: str) -> list[dict[str, str | float]]:
    from PIL import Image

    with tempfile.TemporaryDirectory() as directory:
        output_pattern = str(Path(directory) / "frame-%04d.jpg")
        _run([media_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-i", str(path), "-vf", "fps=1", "-q:v", "3", "-y", output_pattern])
        frames: list[dict[str, str | float]] = []
        for index, frame in enumerate(sorted(Path(directory).glob("frame-*.jpg"))):
            with Image.open(frame) as image:
                digest = perceptual_hash(image)
            key = f"keyframes/{proof_id}/frame-{index:04d}.jpg"
            with frame.open("rb") as source:
                storage.save(source, key)
            frames.append({"timestamp": float(index), "hash": digest, "storage_key": key})
        return frames


def create_audio_fingerprint(path: Path, has_audio: bool) -> str | None:
    if not has_audio:
        return None
    result = _run([media_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-i", str(path), "-map", "0:a:0", "-f", "s16le", "-ac", "1", "-ar", "8000", "pipe:1"])
    return hashlib.sha256(result.stdout).hexdigest()


def process_proof(proof_id: str) -> None:
    with SessionLocal() as db:
        proof = get_proof(db, proof_id)
        if not proof:
            return
        job = db.scalar(select(ProcessingJob).where(ProcessingJob.proof_id == proof.id, ProcessingJob.status.in_(["queued", "running"])).order_by(ProcessingJob.id.desc()))
        if not job:
            return
        job.status = "running"
        job.attempts += 1
        proof.status = "processing"
        proof.current_step = "metadata"
        add_event(db, proof, f"Processing job {job.id} started", job)
        db.commit()
    try:
        path = storage.local_path(proof.storage_key)
        metadata = extract_metadata(path)
        with SessionLocal() as db:
            proof = get_proof(db, proof_id)
            job = db.scalar(select(ProcessingJob).where(ProcessingJob.proof_id == proof.id, ProcessingJob.status == "running").order_by(ProcessingJob.id.desc()))
            proof.duration, proof.width, proof.height, proof.codec, proof.frame_rate, proof.audio_present = metadata["duration"], metadata["width"], metadata["height"], metadata["codec"], metadata["frame_rate"], metadata["audio_present"]
            proof.progress, proof.current_step = 28, "metadata"
            add_event(db, proof, "Video metadata extracted with ffprobe", job)
            db.commit()
        frames = extract_keyframes(path, proof_id)
        with SessionLocal() as db:
            proof = get_proof(db, proof_id)
            job = db.scalar(select(ProcessingJob).where(ProcessingJob.proof_id == proof.id, ProcessingJob.status == "running").order_by(ProcessingJob.id.desc()))
            proof.keyframes_json = json.dumps(frames)
            proof.progress, proof.current_step = 58, "keyframes"
            add_event(db, proof, f"{len(frames)} keyframes extracted and perceptually hashed", job)
            db.commit()
        audio_fingerprint = create_audio_fingerprint(path, bool(metadata["audio_present"]))
        with SessionLocal() as db:
            proof = get_proof(db, proof_id)
            job = db.scalar(select(ProcessingJob).where(ProcessingJob.proof_id == proof.id, ProcessingJob.status == "running").order_by(ProcessingJob.id.desc()))
            proof.audio_fingerprint = audio_fingerprint
            proof.progress, proof.current_step = 76, "audio"
            add_event(db, proof, "Audio fingerprint generated" if audio_fingerprint else "No audio stream detected", job)
            proof.transcript_status = "unavailable"
            proof.progress, proof.current_step = 88, "transcript"
            add_event(db, proof, "Transcript provider unavailable in local development", job)
            proof.status, proof.current_step, proof.progress = "secured", "secured", 100
            proof.evidence_completeness = 90 if audio_fingerprint else 82
            job.status = "completed"
            add_event(db, proof, "Creator Proof finalised", job)
            db.commit()
    except Exception as error:
        with SessionLocal() as db:
            proof = get_proof(db, proof_id)
            if proof:
                job = db.scalar(select(ProcessingJob).where(ProcessingJob.proof_id == proof.id, ProcessingJob.status == "running").order_by(ProcessingJob.id.desc()))
                proof.status, proof.current_step = "failed", "failed"
                if job:
                    job.status, job.error_message = "failed", str(error)[:500]
                add_event(db, proof, f"Processing failed: {str(error)[:400]}", job)
                db.commit()
