from __future__ import annotations

from dataclasses import dataclass

from .dashboard_models import PhotoAnalysis, Severity, SubmittedPhoto


@dataclass(frozen=True)
class _FindingTemplate:
    severity: Severity
    finding: str
    nesc: str
    action: str
    violation_type_id: str | None
    violation_code: str | None
    violation_family: str | None
    dashboard_title: str
    regulations: tuple[str, ...]
    evidence_required: str
    specifications: dict[str, str | int | float | None]


_KEYWORD_FINDINGS: list[tuple[tuple[str, ...], _FindingTemplate]] = [
    (
        ("lean", "tilt", "bent", "split", "broken", "collapse", "rot", "decay", "crack"),
        _FindingTemplate(
            Severity.CRITICAL,
            "Possible structural instability visible in the submitted field photos.",
            "NESC 261",
            "Escalate for engineering review and restrict climbing until the pole is cleared.",
            "vt-pole-condition",
            "pole_condition",
            "structure",
            "Pole structural condition",
            ("NESC Rule 261", "ANSI O5.1", "OSHA 29 CFR 1910.269"),
            "Photos, pole class/material, lean measurement, age/install date, treatment/inspection history.",
            {"measurement_kind": "condition", "confirm": "lean degrees, decay depth, remaining strength"},
        ),
    ),
    (
        ("vegetation", "tree", "branch", "limb", "contact"),
        _FindingTemplate(
            Severity.HIGH,
            "Vegetation appears to be encroaching on the utility space or conductor clearance zone.",
            "NESC 218",
            "Schedule vegetation clearance and verify conductor separation in the field.",
            "vt-vegetation-contact",
            "vegetation_contact",
            "vegetation",
            "Vegetation contact or encroachment",
            ("NESC Rule 218", "MIOSHA Part 86", "MPSC R 460.3504"),
            "Photos, estimated clearance/contact, species or growth pattern if known, conductor type/voltage.",
            {"measurement_kind": "clearance", "unit": "ft", "confirm": "side/above/below clearance"},
        ),
    ),
    (
        ("guy", "anchor", "wire", "corrosion"),
        _FindingTemplate(
            Severity.HIGH,
            "Guying or anchoring condition may need follow-up based on the submitted photo set.",
            "NESC 261",
            "Inspect guy tension, anchor condition, and corrosion before closing the report.",
            "vt-guying-anchor",
            "guying_anchor",
            "structural_support",
            "Guying and anchor condition",
            ("NESC Rule 261", "ASTM A475"),
            "Photos of anchor/guy assembly, tension observation, location context, pedestrian/traffic exposure.",
            {"measurement_kind": "condition", "confirm": "guy tension, corrosion, anchor exposure"},
        ),
    ),
    (
        ("ground", "bond", "neutral", "riser"),
        _FindingTemplate(
            Severity.MEDIUM,
            "Grounding, bonding, or riser equipment is present and should be checked for compliance.",
            "NESC 092",
            "Verify bond continuity, grounding condition, and attachment integrity.",
            "vt-grounding-bonding",
            "grounding_bonding",
            "grounding",
            "Grounding and bonding",
            ("NESC Section 9", "OSHA 29 CFR 1910.269(n)"),
            "Photos of grounding conductor/bonds, equipment present, continuity test if available.",
            {"measurement_kind": "continuity", "confirm": "bond path, ground conductor condition"},
        ),
    ),
    (
        ("id", "tag", "marking", "label"),
        _FindingTemplate(
            Severity.LOW,
            "Pole identification or marking appears to be the primary inspection concern.",
            "Local utility standard",
            "Re-tag or re-stencil during the next maintenance cycle.",
            None,
            None,
            "identification",
            "Pole identification or marking",
            ("MPSC R 460.601",),
            "Photo of tag or stencil, pole location, and replacement identifier if known.",
            {"measurement_kind": "condition", "confirm": "asset identifier legibility"},
        ),
    ),
]

_DEFAULT_FINDINGS = [
    _FindingTemplate(
        Severity.HIGH,
        "Photo evidence suggests a possible equipment or attachment condition that needs priority review.",
        "NESC 261",
        "Inspect attachment loading, pole condition, and hardware before closing the report.",
        "vt-joint-use-attachment",
        "joint_use_attachment",
        "joint_use",
        "Joint-use attachment",
        ("NESC Rule 235", "NESC Rule 238", "NESC Rule 261"),
        "Attachment owner/type, measured height, separation from supply conductors, permit/ticket reference.",
        {"measurement_kind": "clearance", "unit": "ft", "confirm": "attachment separation and ownership"},
    ),
    _FindingTemplate(
        Severity.MEDIUM,
        "Submitted photos show field conditions that need reviewer confirmation.",
        "NESC field review",
        "Review the uploaded images, confirm the violation type, and assign a work priority.",
        None,
        None,
        None,
        "Field review required",
        ("NESC field review",),
        "Photos, pole type, location, field notes, and reviewer confirmation.",
        {"measurement_kind": "manual_review", "confirm": "violation family and severity"},
    ),
    _FindingTemplate(
        Severity.MEDIUM,
        "The submitted photo set appears suitable for routine field validation.",
        "NESC field review",
        "Confirm pole type, attachment condition, and clearance context during review.",
        None,
        None,
        None,
        "Routine field validation",
        ("NESC field review",),
        "Photos, pole type, location, and reviewer confirmation.",
        {"measurement_kind": "manual_review", "confirm": "pole type, attachments, clearance context"},
    ),
    _FindingTemplate(
        Severity.LOW,
        "Submitted photos do not show an obvious emergency condition from available metadata.",
        "NESC field review",
        "Keep the report open for routine inspection review.",
        None,
        None,
        None,
        "Routine inspection review",
        ("NESC field review",),
        "Photos and field notes.",
        {"measurement_kind": "manual_review", "confirm": "no visible urgent issue"},
    ),
]


def _image_signature(photos: list[SubmittedPhoto]) -> int:
    sample = "".join(photo.data_url[:120] + photo.data_url[-120:] for photo in photos)
    return sum((index + 1) * ord(char) for index, char in enumerate(sample))


def analyze_report_photos(photos: list[SubmittedPhoto], description: str | None = None) -> PhotoAnalysis:
    """Backend MVP analyzer.

    This is intentionally deterministic so uploads produce stable review text.
    A real vision model can replace this function without changing the API.
    """
    searchable = (description or "").lower()
    signature = _image_signature(photos)
    template = next(
        (candidate for keywords, candidate in _KEYWORD_FINDINGS if any(word in searchable for word in keywords)),
        _DEFAULT_FINDINGS[signature % len(_DEFAULT_FINDINGS)],
    )
    confidence = min(92, 58 + (len(photos) * 8) + min(len(searchable) // 80, 10) + (signature % 7))
    return PhotoAnalysis(
        severity=template.severity,
        finding=template.finding,
        confidence=confidence,
        nesc=template.nesc,
        action=template.action,
        violation_type_id=template.violation_type_id,
        violation_code=template.violation_code,
        violation_family=template.violation_family,
        dashboard_title=template.dashboard_title,
        regulations=list(template.regulations),
        evidence_required=template.evidence_required,
        specifications=template.specifications,
        is_utility_structure=True,
        structure_confidence=55,
        rejection_reason=None,
    )
