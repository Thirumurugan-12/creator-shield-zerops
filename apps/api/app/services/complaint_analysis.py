from __future__ import annotations

import json
import hashlib
import re
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import select

from ..db.session import SessionLocal
from ..models.entities import Incident, ProofRecord
from .storage import StorageService

storage = StorageService()

LABEL_PATTERNS = {
    "claimant_name": r"(?:claimant|rights holder|copyright owner)\s*(?:name)?\s*[:\-]\s*([^\n]+)",
    "claimant_company": r"(?:company|organization|agency)\s*[:\-]\s*([^\n]+)",
    "complaint_date": r"(?:complaint|notice)\s*date\s*[:\-]\s*([^\n]+)",
    "claimant_publication_date": r"(?:original|claimant)\s*(?:publication|published)\s*date\s*[:\-]\s*([^\n]+)",
    "payment_amount": r"(?:payment|fee|amount|invoice)\s*[:\-]?\s*(\$\s?[\d,]+(?:\.\d{2})?|[₹€£]\s?[\d,]+(?:\.\d{2})?)",
    "requested_action": r"(?:requested action|request|remedy)\s*[:\-]\s*([^\n]+)",
}


def _extract_pdf_text(path: Path) -> tuple[str, str]:
    try:
        from pypdf import PdfReader

        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages).strip()
        return text, "PDF text extracted locally" if text else "PDF contains no extractable text"
    except Exception as error:
        return "", f"PDF extraction unavailable: {str(error)[:160]}"


def extract_evidence_text(path: Path, content_type: str) -> tuple[str, str]:
    if content_type == "application/pdf" or path.suffix.lower() == ".pdf":
        return _extract_pdf_text(path)
    return "", "OCR unavailable for image evidence in local development"


def _first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _date_value(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})", value)
    if not match:
        return None
    raw = match.group(1).replace("/", "-")
    for pattern in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, pattern).date().isoformat()
        except ValueError:
            continue
    return None


def _extract_fields(text: str) -> dict[str, object]:
    emails = sorted(set(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)))
    phones = sorted(set(re.findall(r"(?:\+?\d[\d ()-]{7,}\d)", text)))
    fields: dict[str, object] = {
        "claimant_name": _first(LABEL_PATTERNS["claimant_name"], text),
        "claimant_company": _first(LABEL_PATTERNS["claimant_company"], text),
        "email": emails[0] if emails else None,
        "phone": phones[0] if phones else None,
        "contacts": sorted(set(emails + phones)),
        "payment_id": _first(r"(?:payment|transaction|invoice|reference)\s*(?:id|number|#)?\s*[:\-]\s*([A-Z0-9-]{4,})", text),
        "payment_amount": _first(LABEL_PATTERNS["payment_amount"], text),
        "complaint_date": _date_value(_first(LABEL_PATTERNS["complaint_date"], text)),
        "claimant_publication_date": _date_value(_first(LABEL_PATTERNS["claimant_publication_date"], text)),
        "requested_action": _first(LABEL_PATTERNS["requested_action"], text),
        "urls": sorted(set(re.findall(r"https?://[^\s)>]+", text, re.IGNORECASE))),
        "message_fingerprint": hashlib.sha256(re.sub(r"\s+", " ", text.lower()).strip().encode()).hexdigest() if text else None,
    }
    return fields


def _indicator(rule: str, points: int, triggered: bool, explanation: str) -> dict[str, object]:
    return {"rule": rule, "points": points, "triggered": triggered, "explanation": explanation}


def _band(score: int) -> str:
    if score < 30:
        return "Low suspicion"
    if score < 60:
        return "Needs review"
    if score < 80:
        return "High suspicion"
    return "Critical indicators"


def analyze_incident(incident_id: str) -> None:
    with SessionLocal() as db:
        incident = db.scalar(select(Incident).where(Incident.incident_id == incident_id))
        if not incident:
            return
        proof = db.get(ProofRecord, incident.proof_id)
        evidence = list(incident.evidence)
        if not proof:
            return
        extracted: dict[str, object] = {"status": "completed", "provider": "local", "files": [], "fields": {}}
        all_text: list[str] = []
        merged_fields: dict[str, object] = {}
        for item in evidence:
            text, status = extract_evidence_text(storage.local_path(item.storage_key), item.content_type)
            fields = _extract_fields(text)
            all_text.append(text)
            merged_fields.update({key: value for key, value in fields.items() if value})
            extracted["files"].append({"filename": item.filename, "status": status, "text_available": bool(text)})
        extracted["fields"] = merged_fields
        if not evidence:
            extracted["status"] = "no_evidence"
        elif not all_text or not any(all_text):
            extracted["status"] = "unavailable"
        text = "\n".join(all_text).lower()
        claimant_date = merged_fields.get("claimant_publication_date")
        registered_before_claim = False
        if claimant_date and proof.created_at:
            registered_before_claim = proof.created_at.date() <= date.fromisoformat(str(claimant_date))
        similarity_match = incident.combined_similarity is not None and incident.combined_similarity > 85
        payment_demand = bool(re.search(r"(?:pay|payment|fee|invoice|transfer|send)\D{0,30}(?:\$|₹|€|£|\d)", text))
        withdrawal_request = bool(re.search(r"(?:withdraw|remove|take down|cancel)\D{0,30}(?:complaint|notice|claim|report)", text))
        urgent_threat = bool(re.search(r"(?:urgent|immediately|deadline|legal action|strike|lawsuit|court|within \d+ days)", text))
        avoid_support = bool(re.search(r"(?:do not|don't|avoid)\D{0,20}(?:instagram|platform|support|official)", text))
        private_request = bool(re.search(r"(?:whatsapp|telegram|otp|one[- ]time password|password|private email|contact me directly)", text))
        guaranteed_restore = bool(re.search(r"(?:guarantee|guaranteed|restore|reinstate|unblock)\D{0,30}(?:account|access|profile|channel)", text))
        source_missing = not bool(proof.claimed_publication_url.strip())
        indicators = [
            _indicator("Creator registration predates claimant publication", 25, registered_before_claim, "Proof registration date is earlier than the extracted claimant publication date."),
            _indicator("Content similarity above 85%", 25, similarity_match, "The completed technical comparison is above the configured threshold."),
            _indicator("Payment demand", 30, payment_demand, "Complaint text contains payment or transfer language."),
            _indicator("Claimant appears in multiple reports", 15, False, "Community correlation is deferred to Phase 11."),
            _indicator("Claimed original source missing", 10, source_missing, "The Creator Proof has no claimed publication URL."),
            _indicator("Threatening or urgent language", 10, urgent_threat, "Complaint text contains urgency or escalation language."),
            _indicator("Request to avoid official support", 10, avoid_support, "Complaint text asks the creator to avoid an official channel."),
            _indicator("Private communication or credential request", 10, private_request, "Complaint text references private channels, OTPs, or passwords."),
            _indicator("Guaranteed account restoration claim", 10, guaranteed_restore, "Complaint text suggests guaranteed restoration or reinstatement."),
            _indicator("Withdrawal-of-complaint request", 0, withdrawal_request, "Complaint text asks for a complaint or notice to be withdrawn."),
        ]
        score = min(100, sum(int(item["points"]) for item in indicators if item["triggered"]))
        now = datetime.now(timezone.utc).isoformat()
        events = json.loads(incident.events_json or "[]")
        events.append({"timestamp": now, "message": f"Complaint extraction completed: {extracted['status']}"})
        events.append({"timestamp": now, "message": f"Transparent suspicion score calculated: {score}/100 · {_band(score)}"})
        incident.complaint_extraction_json = json.dumps(extracted)
        incident.suspicion_score = score
        incident.suspicion_band = _band(score)
        incident.suspicion_indicators_json = json.dumps(indicators)
        incident.events_json = json.dumps(events)
        db.commit()
    from .community import analyze_community_incident
    analyze_community_incident(incident_id)
