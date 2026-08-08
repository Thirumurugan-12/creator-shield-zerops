from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from sqlalchemy import select

from ..db.session import SessionLocal
from ..models.entities import Incident, ProofRecord
from ..repositories.incidents import find_incident
from ..repositories.proofs import get_proof
from .processing import create_audio_fingerprint, extract_metadata, media_binary
from .storage import StorageService

storage = StorageService()


def _hash_distance(left: str, right: str) -> int:
    return sum(a != b for a, b in zip(left, right))


def _perceptual_hash(image) -> str:
    grayscale = image.convert("L").resize((8, 8))
    pixels = list(grayscale.getdata())
    average = sum(pixels) / len(pixels)
    return "".join("1" if pixel >= average else "0" for pixel in pixels)

def _frame_hashes(path: Path, mirrored: bool = False) -> list[Any]:
    from PIL import Image, ImageOps
    with tempfile.TemporaryDirectory() as directory:
        pattern = str(Path(directory) / "frame-%04d.jpg")
        subprocess.run([media_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-i", str(path), "-vf", "fps=1", "-q:v", "3", "-y", pattern], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        hashes=[]
        for frame in sorted(Path(directory).glob("frame-*.jpg")):
            with Image.open(frame) as image:
                hashes.append(_perceptual_hash(ImageOps.mirror(image) if mirrored else image))
        return hashes

def _visual_score(original: list[str], suspicious: list[str]) -> tuple[float, int]:
    if not original or not suspicious:
        return 0.0, 0
    distances=[min(_hash_distance(item, candidate) for candidate in original) for item in suspicious]
    matches=sum(distance <= 12 for distance in distances)
    score=sum(max(0.0, 100.0-(distance/64.0*100.0)) for distance in distances)/len(distances)
    return round(score,2), matches

def compare_incident(incident_id: str) -> None:
    with SessionLocal() as db:
        incident = db.scalar(select(Incident).where(Incident.incident_id == incident_id))
        if not incident:
            return
        original = db.get(ProofRecord, incident.proof_id)
        if not original:
            return
        incident.status, incident.stage = "analysing", "analysing_media"
        events=json.loads(incident.events_json or "[]")
        events.append({"timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),"message":"Media comparison started"})
        incident.events_json=json.dumps(events)
        db.commit()
    try:
        original_path=storage.local_path(original.storage_key)
        suspicious_path=storage.local_path(incident.suspicious_storage_key)
        original_metadata=extract_metadata(original_path)
        suspicious_metadata=extract_metadata(suspicious_path)
        original_hashes=_frame_hashes(original_path)
        suspicious_hashes=_frame_hashes(suspicious_path)
        mirrored_hashes=_frame_hashes(suspicious_path, mirrored=True)
        visual, matches=_visual_score(original_hashes, suspicious_hashes)
        mirrored_score, mirrored_matches=_visual_score(original_hashes, mirrored_hashes)
        audio_original=create_audio_fingerprint(original_path, bool(original_metadata["audio_present"]))
        audio_suspicious=create_audio_fingerprint(suspicious_path, bool(suspicious_metadata["audio_present"]))
        audio=100.0 if audio_original and audio_original == audio_suspicious else 0.0
        timeline=max(0.0, 100.0-abs(original_metadata["duration"]-suspicious_metadata["duration"])/max(original_metadata["duration"],1.0)*100.0)
        available_weight=0.45+0.30+0.05
        combined=(visual*0.45+audio*0.30+timeline*0.05)/available_weight
        modifications=[]
        if mirrored_score>visual+5 and mirrored_matches>0: modifications.append("Mirrored video likely")
        if abs(original_metadata["duration"]-suspicious_metadata["duration"])>2: modifications.append("Trimmed beginning or ending possible")
        if visual>70 and original.sha256 != incident.suspicious_sha256: modifications.append("Re-encoding or visual modification possible")
        if 0<matches<len(suspicious_hashes): modifications.append("Partial content reuse possible")
        with SessionLocal() as db:
            incident=db.scalar(select(Incident).where(Incident.incident_id==incident_id))
            incident.visual_similarity=visual;incident.audio_similarity=audio;incident.transcript_similarity=None;incident.timeline_confidence=round(timeline,2);incident.combined_similarity=round(combined,2);incident.matching_segments=matches;incident.matching_audio_seconds=min(original_metadata["duration"],suspicious_metadata["duration"]) if audio>=85 else 0;incident.modifications_json=json.dumps(modifications);incident.status="completed";incident.stage="completed"
            events=json.loads(incident.events_json or "[]");events.extend([{"timestamp":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),"message":f"Visual comparison completed: {visual:.1f}% similarity"},{"timestamp":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),"message":"Audio comparison completed"},{"timestamp":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),"message":"Transcript comparison unavailable in local development"}]);incident.events_json=json.dumps(events);db.commit()
        from .complaint_analysis import analyze_incident
        analyze_incident(incident_id)
    except Exception as error:
        with SessionLocal() as db:
            incident=db.scalar(select(Incident).where(Incident.incident_id==incident_id))
            if incident:
                incident.status="failed";incident.stage="failed";events=json.loads(incident.events_json or "[]");events.append({"timestamp":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),"message":f"Comparison failed: {str(error)[:400]}"});incident.events_json=json.dumps(events);db.commit()
