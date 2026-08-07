from __future__ import annotations

import io
import json
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models.entities import Incident, ProofRecord

DISCLAIMER = "This report presents technical evidence only. It does not determine copyright ownership, establish unlawful conduct, or provide legal advice."


def _value(value: object) -> str:
    return str(value) if value not in (None, "", []) else "Unavailable"


def _percent(value: object) -> str:
    return "Unavailable" if value is None else f"{value}%"


def build_report_context(incident: Incident, proof: ProofRecord) -> dict[str, object]:
    extraction = json.loads(incident.complaint_extraction_json or "{}")
    fields = extraction.get("fields", {})
    indicators = json.loads(incident.suspicion_indicators_json or "[]")
    matches = json.loads(incident.community_matches_json or "[]")
    community = json.loads(incident.community_summary_json or "{}")
    keyframes = json.loads(proof.keyframes_json or "[]")
    missing = []
    if not incident.evidence:
        missing.append("No complaint evidence file was uploaded.")
    if not fields:
        missing.append("No complaint fields were extracted; image OCR or text extraction may be unavailable.")
    if incident.transcript_similarity is None:
        missing.append("Transcript comparison is unavailable in the current local configuration.")
    if not matches:
        missing.append("No matching simulated community identifiers were found.")
    if not keyframes:
        missing.append("No original keyframes are available in the Creator Proof record.")
    return {
        "status": "generated",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "incident_id": incident.incident_id,
        "proof": {"proof_id": proof.proof_id, "title": proof.title, "creator": proof.instagram_username, "publication_date": proof.claimed_publication_date, "publication_url": proof.claimed_publication_url, "filename": proof.original_filename, "sha256": proof.sha256, "duration": proof.duration, "width": proof.width, "height": proof.height, "codec": proof.codec, "keyframes": keyframes},
        "suspicious": {"filename": incident.suspicious_filename, "username": incident.suspicious_username, "publication_date": incident.claimed_publication_date, "url": incident.suspicious_url, "sha256": incident.suspicious_sha256, "file_size": incident.suspicious_file_size},
        "comparison": {"visual": incident.visual_similarity, "audio": incident.audio_similarity, "transcript": incident.transcript_similarity, "timeline": incident.timeline_confidence, "combined": incident.combined_similarity, "matching_segments": incident.matching_segments, "matching_audio_seconds": incident.matching_audio_seconds, "modifications": json.loads(incident.modifications_json or "[]")},
        "complaint": {"status": extraction.get("status", "unavailable"), "provider": extraction.get("provider", "local"), "fields": fields, "files": extraction.get("files", [])},
        "indicators": indicators,
        "community": {"summary": community, "matches": matches},
        "evidence_files": [{"filename": item.filename, "type": item.content_type, "size": item.file_size, "sha256": item.sha256 or "Unavailable"} for item in incident.evidence],
        "missing": missing,
        "disclaimer": DISCLAIMER,
    }


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24, leading=29, alignment=TA_CENTER, textColor=colors.HexColor("#172033"), spaceAfter=10))
    styles.add(ParagraphStyle(name="ReportSubtitle", parent=styles["Normal"], fontSize=10, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#526071"), spaceAfter=18))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=colors.HexColor("#172033"), spaceBefore=12, spaceAfter=7))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=8.5, leading=12, textColor=colors.HexColor("#39465a")))
    styles.add(ParagraphStyle(name="Muted", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#526071")))
    styles.add(ParagraphStyle(name="Disclaimer", parent=styles["Normal"], fontSize=8.5, leading=12, textColor=colors.HexColor("#526071"), borderColor=colors.HexColor("#D8DEE8"), borderWidth=0.5, borderPadding=8))
    return styles


def _paragraph(value: object, style) -> Paragraph:
    return Paragraph(_value(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)


def _table(rows: list[list[object]], styles, widths: list[float] | None = None) -> Table:
    formatted = [[_paragraph(cell, styles["Small"]) for cell in row] for row in rows]
    table = Table(formatted, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#172033")), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8DEE8")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return table


def generate_report_pdf(context: dict[str, object]) -> bytes:
    styles = _styles()
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=0.65 * inch, leftMargin=0.65 * inch, topMargin=0.6 * inch, bottomMargin=0.6 * inch, title=f"CreatorShield Evidence Report - {context['incident_id']}")
    story = [_paragraph("CreatorShield", styles["ReportTitle"]), _paragraph("Technical Evidence Report", styles["ReportSubtitle"]), _paragraph(f"Incident {_value(context['incident_id'])} | Generated {_value(context['generated_at'])}", styles["Muted"]), Spacer(1, 18), HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D8DEE8")), Spacer(1, 12), _paragraph("Executive summary", styles["Section"]), _paragraph("This report organizes the uploaded incident evidence, Creator Proof metadata, technical comparison results, complaint extraction, and simulated community signals. It does not make a legal ownership or misconduct determination.", styles["Normal"])]
    proof = context["proof"]
    suspicious = context["suspicious"]
    story += [_paragraph("Creator Proof and original metadata", styles["Section"]), _table([["Field", "Value"], ["Proof ID", proof["proof_id"]], ["Title", proof["title"]], ["Creator account", proof["creator"]], ["Claimed publication date", proof["publication_date"]], ["Claimed publication URL", proof["publication_url"]], ["Original file", proof["filename"]], ["SHA-256", proof["sha256"]], ["Video metadata", f"{_value(proof['width'])} x {_value(proof['height'])}, {_value(proof['duration'])} seconds, codec {_value(proof['codec'])}"]], styles, [1.7 * inch, 5.6 * inch])]
    story += [_paragraph("Suspicious content metadata", styles["Section"]), _table([["Field", "Value"], ["Filename", suspicious["filename"]], ["Account", suspicious["username"]], ["Claimed publication date", suspicious["publication_date"]], ["URL", suspicious["url"]], ["SHA-256", suspicious["sha256"]], ["File size", f"{_value(suspicious['file_size'])} bytes"]], styles, [1.7 * inch, 5.6 * inch])]
    comparison = context["comparison"]
    story.append(KeepTogether([_paragraph("Timeline and technical comparison", styles["Section"]), _table([["Signal", "Result"], ["Visual similarity", _percent(comparison["visual"])], ["Audio similarity", _percent(comparison["audio"])], ["Transcript similarity", _percent(comparison["transcript"])], ["Timeline confidence", _percent(comparison["timeline"])], ["Combined similarity", _percent(comparison["combined"])], ["Matching segments", comparison["matching_segments"]], ["Matching audio duration", f"{_value(comparison['matching_audio_seconds'])} seconds"], ["Modification indicators", "; ".join(comparison["modifications"]) if comparison["modifications"] else "None recorded"]], styles, [2.2 * inch, 5.1 * inch])]))
    story += [_paragraph("Matching keyframe evidence", styles["Section"])]
    keyframes = proof["keyframes"]
    if keyframes:
        story.append(_table([["Timestamp", "Hash"]] + [[frame.get("timestamp", "Unavailable"), frame.get("hash", "Unavailable")] for frame in keyframes], styles, [2.2 * inch, 5.1 * inch]))
    else:
        story.append(_paragraph("No matching keyframe evidence is available in this report.", styles["Muted"]))
    complaint = context["complaint"]
    story += [_paragraph("Complaint extraction", styles["Section"]), _paragraph(f"Extraction status: {_value(complaint['status'])}. Provider: {_value(complaint['provider'])}. Extraction is shown separately from interpretation.", styles["Muted"])]
    complaint_rows = [["Extracted field", "Value"]] + [[key.replace("_", " "), value if not isinstance(value, list) else ", ".join(str(item) for item in value)] for key, value in complaint["fields"].items()]
    if len(complaint_rows) > 1:
        story.append(_table(complaint_rows, styles, [2.2 * inch, 5.1 * inch]))
    else:
        story.append(_paragraph("No complaint fields were extracted.", styles["Muted"]))
    story += [_paragraph("Suspicion indicators", styles["Section"]), _table([["Rule", "Triggered", "Points", "Explanation"]] + [[item["rule"], "Yes" if item["triggered"] else "No", item["points"], item["explanation"]] for item in context["indicators"]], styles, [1.7 * inch, 0.9 * inch, 0.7 * inch, 4.0 * inch])]
    community = context["community"]
    story += [_paragraph("Simulated community intelligence", styles["Section"]), _paragraph("The following section contains seeded development data only. It is not a verified real-world finding.", styles["Muted"]), _table([["Summary", "Value"], ["Related simulated reports", community["summary"].get("related_report_count", 0)], ["Payment-demand occurrences", community["summary"].get("payment_demand_occurrences", 0)], ["Creator restrictions", community["summary"].get("creator_restrictions", 0)], ["First recorded date", community["summary"].get("first_recorded_date", "Unavailable")]], styles, [2.5 * inch, 4.8 * inch])]
    if community["matches"]:
        story.append(Spacer(1, 8))
        story.append(_table([["Identifier", "Matched value", "Simulated report"]] + [[item["identifier"], item["matched_value"], item["report_id"]] for item in community["matches"]], styles, [2.0 * inch, 3.8 * inch, 1.5 * inch]))
    story += [_paragraph("Evidence inventory and limitations", styles["Section"])]
    evidence_files = context["evidence_files"]
    story.append(_table([["Filename", "Type", "Size", "SHA-256"]] + [[item["filename"], item["type"], item["size"], item["sha256"]] for item in evidence_files], styles, [2.2 * inch, 1.4 * inch, 0.8 * inch, 2.9 * inch]) if evidence_files else _paragraph("No complaint evidence files were uploaded.", styles["Muted"]))
    story.append(Spacer(1, 8))
    story.append(_paragraph("Missing-information warnings", styles["Section"]))
    story.append(_paragraph("; ".join(context["missing"]) if context["missing"] else "No configured evidence gaps were detected.", styles["Muted"]))
    story += [Spacer(1, 18), _paragraph(context["disclaimer"], styles["Disclaimer"])]

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#687588"))
        canvas.drawString(0.65 * inch, 0.35 * inch, "CreatorShield | Technical evidence only")
        canvas.drawRightString(7.85 * inch, 0.35 * inch, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
