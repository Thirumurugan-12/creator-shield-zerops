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

        # static-ffmpeg extracts its archive into the parent of the
        # requested platform directory. Keep the final ``linux`` segment
        # so the extracted binaries land at the paths returned by it.
        download_dir = os.getenv(
            "CREATORSHIELD_FFMPEG_DIR",
            "/var/www/apps/api/vendor/ffmpeg/linux",
        )
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


def _extract_metadata_pyav(path: Path) -> dict:
    import av

    container = av.open(str(path))
    video = next((stream for stream in container.streams if stream.type == "video"), None)
    if video is None:
        raise ValueError("No video stream found")
    duration = float(video.duration * video.time_base) if video.duration and video.time_base else float(container.duration or 0) / 1_000_000
    frame_rate = float(video.average_rate) if video.average_rate else None
    return {
        "duration": duration,
        "width": video.codec_context.width,
        "height": video.codec_context.height,
        "codec": video.codec_context.name,
        "frame_rate": frame_rate,
        "audio_present": any(stream.type == "audio" for stream in container.streams),
    }


def extract_metadata(path: Path) -> dict:
    try:
        result = _run([media_binary("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    except Exception:
        return _extract_metadata_pyav(path)
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
        try:
            _run([media_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-i", str(path), "-vf", "fps=1", "-q:v", "3", "-y", output_pattern])
        except Exception:
            import av

            container = av.open(str(path))
            video = next((stream for stream in container.streams if stream.type == "video"), None)
            if video is None:
                raise ValueError("No video stream found")
            next_timestamp = 0.0
            for frame in container.decode(video=0):
                timestamp = float(frame.time or 0.0)
                if timestamp + 0.001 >= next_timestamp:
                    frame.to_image().save(Path(directory) / f"frame-{len(list(Path(directory).glob('frame-*.jpg'))):04d}.jpg", quality=85)
                    next_timestamp += 1.0
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
    try:
        result = _run([media_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-i", str(path), "-map", "0:a:0", "-f", "s16le", "-ac", "1", "-ar", "8000", "pipe:1"])
        return hashlib.sha256(result.stdout).hexdigest()
    except Exception:
        import av

        container = av.open(str(path))
        audio = next((stream for stream in container.streams if stream.type == "audio"), None)
        if audio is None:
            return None
        digest = hashlib.sha256()
        for frame in container.decode(audio=0):
            digest.update(frame.to_ndarray().tobytes())
        return digest.hexdigest()


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
        with storage.materialize(proof.storage_key) as path:
            metadata = extract_metadata(path)
            with SessionLocal() as db:
                proof = get_proof(db, proof_id)
                job = db.scalar(select(ProcessingJob).where(ProcessingJob.proof_id == proof.id, ProcessingJob.status == "running").order_by(ProcessingJob.id.desc()))
                proof.duration, proof.width, proof.height, proof.codec, proof.frame_rate, proof.audio_present = metadata["duration"], metadata["width"], metadata["height"], metadata["codec"], metadata["frame_rate"], metadata["audio_present"]
                proof.progress, proof.current_step = 28, "metadata"
                add_event(db, proof, "Video metadata extracted", job)
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
