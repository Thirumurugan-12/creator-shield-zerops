from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select

from ..db.session import SessionLocal
from ..models.entities import Incident, SimulatedReport


SEED_REPORTS = [
    {"claimant_email": "rightsdesk@simulated.example", "claimant_phone": "+1 555 010 2048", "claimant_username": "simulated_rights_desk", "claimant_domain": "simulated-rights.example", "payment_identifier": "SIM-PAY-2025", "repeated_wording": "pay within 48 hours to avoid account restriction", "payment_demand_count": 7, "creator_restriction_count": 3, "first_recorded_date": "2025-02-14"},
    {"claimant_email": "notice@demo-claimant.example", "claimant_phone": "+1 555 010 3011", "claimant_username": "demo_claimant_team", "claimant_domain": "demo-claimant.example", "payment_identifier": "DEMO-INVOICE-44", "repeated_wording": "contact me directly and do not use platform support", "payment_demand_count": 4, "creator_restriction_count": 1, "first_recorded_date": "2025-06-03"},
]


def _fingerprint(value: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", value.lower()).strip().encode()).hexdigest()


def seed_simulated_reports() -> None:
    with SessionLocal() as db:
        if db.scalar(select(SimulatedReport.id).limit(1)):
            return
        for item in SEED_REPORTS:
            db.add(SimulatedReport(**item, message_fingerprint=_fingerprint(item["repeated_wording"])))
        db.commit()


def _band(score: int) -> str:
    if score < 30:
        return "Low suspicion"
    if score < 60:
        return "Needs review"
    if score < 80:
        return "High suspicion"
    return "Critical indicators"


def analyze_community_incident(incident_id: str) -> None:
    with SessionLocal() as db:
        incident = db.scalar(select(Incident).where(Incident.incident_id == incident_id))
        if not incident:
            return
        extraction = json.loads(incident.complaint_extraction_json or "{}")
        fields = extraction.get("fields", {})
        text = " ".join(str(value) for value in [incident.caption, incident.notes, fields.get("requested_action", "")]).lower()
        domains = {urlparse(url).netloc.lower() for url in fields.get("urls", []) if isinstance(url, str)}
        values = {"claimant email": str(fields.get("email", "")).lower(), "phone": re.sub(r"\D", "", str(fields.get("phone", ""))), "username": incident.suspicious_username.lower().lstrip("@"), "domain": next(iter(domains), ""), "payment identifier": str(fields.get("payment_id", "")).lower()}
        values["message fingerprint"] = str(fields.get("message_fingerprint", "")).lower()
        evidence_hashes = {item.sha256.lower() for item in incident.evidence if item.sha256}
        matches: list[dict[str, object]] = []
        for report in db.scalars(select(SimulatedReport)).all():
            checks = [("claimant email", report.claimant_email.lower(), values["claimant email"]), ("phone", re.sub(r"\D", "", report.claimant_phone), values["phone"]), ("username", report.claimant_username.lower(), values["username"]), ("domain", report.claimant_domain.lower(), values["domain"]), ("payment identifier", report.payment_identifier.lower(), values["payment identifier"])]
            checks.extend([("message fingerprint", report.message_fingerprint.lower(), values["message fingerprint"]), ("attachment hash", report.attachment_hash.lower(), next(iter(evidence_hashes), ""))])
            for identifier, expected, actual in checks:
                if expected and actual and expected == actual:
                    matches.append({"report_id": report.id, "identifier": identifier, "matched_value": actual, "repeated_wording": report.repeated_wording})
            if report.repeated_wording and report.repeated_wording.lower() in text:
                matches.append({"report_id": report.id, "identifier": "repeated wording", "matched_value": report.repeated_wording, "repeated_wording": report.repeated_wording})
        unique_matches = {(item["report_id"], item["identifier"]): item for item in matches}
        matches = list(unique_matches.values())
        report_ids = {int(item["report_id"]) for item in matches}
        reports = db.scalars(select(SimulatedReport).where(SimulatedReport.id.in_(report_ids))).all() if report_ids else []
        summary = {"label": "Simulated community intelligence", "related_report_count": len(report_ids), "payment_demand_occurrences": sum(item.payment_demand_count for item in reports), "creator_restrictions": sum(item.creator_restriction_count for item in reports), "first_recorded_date": min((item.first_recorded_date for item in reports), default=None), "simulated": True}
        indicators = json.loads(incident.suspicion_indicators_json or "[]")
        related = next((item for item in indicators if item.get("rule") == "Claimant appears in multiple reports"), None)
        if related:
            related["triggered"] = bool(report_ids)
            related["explanation"] = "A matching identifier links this intake to simulated seeded reports; this is not a verified real-world finding."
        score = min(100, sum(int(item.get("points", 0)) for item in indicators if item.get("triggered")))
        incident.community_matches_json = json.dumps(matches)
        incident.community_summary_json = json.dumps(summary)
        incident.suspicion_indicators_json = json.dumps(indicators)
        incident.suspicion_score = score
        incident.suspicion_band = _band(score)
        events = json.loads(incident.events_json or "[]")
        events.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": f"Simulated community intelligence checked: {len(report_ids)} related report(s)"})
        incident.events_json = json.dumps(events)
        db.commit()
