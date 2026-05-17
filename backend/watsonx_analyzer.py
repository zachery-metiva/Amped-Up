"""
watsonx.ai Severity & Violations Analyzer
==========================================
Calls the IBM watsonx.ai REST API directly (no SDK) to classify utility pole
inspection reports using ibm/granite-3-8b-instruct.

Env vars required:
  WATSONX_API_KEY     — IBM Cloud API key
  WATSONX_PROJECT_ID  — watsonx.ai project ID
  WATSONX_URL         — defaults to https://us-south.ml.cloud.ibm.com
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

try:
    import requests
    from requests import HTTPError as RequestsHTTPError
except ImportError:  # Allows the dashboard to run before optional Watson deps are installed.
    requests = None  # type: ignore[assignment]
    RequestsHTTPError = Exception

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "ca84b127-745f-4d8f-a8be-706a82a6f110")
TEXT_MODEL_ID   = "ibm/granite-3-8b-instruct"              # text-only path (no photos)
VISION_MODEL_ID = "meta-llama/llama-3-2-11b-vision-instruct"  # photo analysis path
MODEL_ID = TEXT_MODEL_ID   # kept for backwards compat
API_VERSION = "2023-05-29"
MAX_PHOTOS_PER_REQUEST = 1  # llama-3-2-11b-vision-instruct allows at most 1 image per prompt
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

# OSHA 29 CFR 1903.14 → app severity mapping
OSHA_TO_APP: dict[str, str] = {
    "imminent_danger":    "critical",
    "serious":            "high",
    "other_than_serious": "medium",
    "de_minimis":         "low",
    "deminimis":          "low",
    "multi_defect":       "high",
    "compliant":          "low",
}

# Violation → default OSHA class (used as rule-based fallback)
VIOLATION_SEVERITY_MAP: dict[str, str] = {
    # Imminent danger
    "vegetation_contact_primary":        "imminent_danger",
    "vegetation_contact_phase_a":        "imminent_danger",
    "vegetation_contact_transmission":   "imminent_danger",
    "downed_conductor_dead_end_failure": "imminent_danger",
    "pole_lean_excessive":               "imminent_danger",
    "stub_lean_excessive":               "imminent_danger",
    "clearance_loss_from_ice_sag":       "imminent_danger",
    "insulator_string_shattered":        "imminent_danger",
    "dead_end_clamp_failure_phase_c":    "imminent_danger",
    "open_neutral":                      "imminent_danger",
    # Serious
    "crossarm_decay":                    "serious",
    "crossarm_split":                    "serious",
    "groundline_decay":                  "serious",
    "pole_decay_groundline":             "serious",
    "pole_decay_woodpecker":             "serious",
    "transformer_oil_leak":              "serious",
    "recloser_oil_leak":                 "serious",
    "guy_strand_corroded":               "serious",
    "guy_strand_corrosion":              "serious",
    "anchor_pulled":                     "serious",
    "insulator_arc_tracking":            "serious",
    "polymer_insulator_tracking":        "serious",
    "riser_insulation_burned":           "serious",
    "splice_thermal_damage":             "serious",
    "conductor_strand_break":            "serious",
    "missing_equipment_ground":          "serious",
    "ground_lead_disconnected":          "serious",
    "cracked_bushing":                   "serious",
    "jumper_damaged":                    "serious",
    "dead_end_clamp_slipped":            "serious",
    # Other-than-serious
    "vegetation_encroachment_primary":   "other_than_serious",
    "tall_vegetation_in_row":            "other_than_serious",
    "anchor_rod_exposed":                "other_than_serious",
    "anchor_bolt_corrosion_both_poles":  "other_than_serious",
    "guy_guard_damaged":                 "other_than_serious",
    "insulator_weather_stain":           "other_than_serious",
    "loose_bank_hardware":               "other_than_serious",
    "loose_tap_clamp":                   "other_than_serious",
    "loose_transformer_hardware":        "other_than_serious",
    "jumper_loop_sag_excessive":         "other_than_serious",
    "service_drop_ground_clearance":     "other_than_serious",
    "primary_conductor_ground_clearance":"other_than_serious",
    "phase_neutral_separation_undersized":"other_than_serious",
    "exposed_underground_cable":         "other_than_serious",
    "weather_head_damaged":              "other_than_serious",
    "weather_head_missing":              "other_than_serious",
    "control_cable_damaged":             "other_than_serious",
    "riser_pipe_damaged":                "other_than_serious",
    "climbing_barrier_missing":          "other_than_serious",
    "bird_nest_on_equipment":            "other_than_serious",
    "bird_nest_on_recloser":             "other_than_serious",
    "unauthorized_attachment":           "other_than_serious",
    "unauthorized_antenna_attachment":   "other_than_serious",
    # De minimis
    "id_tag_illegible":                  "de_minimis",
    "id_tag_missing":                    "de_minimis",
    "pole_id_faded":                     "de_minimis",
    "pole_tag_missing":                  "de_minimis",
    "pole_id_paint_faded":               "de_minimis",
    "id_stencil_faded":                  "de_minimis",
    "manufacturer_label_faded":          "de_minimis",
    "structure_id_plate_faded":          "de_minimis",
    "paint_topcoat_faded":               "de_minimis",
    "uv_resin_chalking":                 "de_minimis",
    "graffiti":                          "de_minimis",
    "aerial_marker_weathered":           "de_minimis",
}

# Representative few-shot examples drawn from the SVG dataset
FEW_SHOT_EXAMPLES: list[dict[str, Any]] = [
    {
        "pole_type": "ang40c4",
        "description": "Active tree branch in contact with primary conductor. Bark scorching visible.",
        "photo_count": 2,
        "output": {
            "severity": "critical",
            "violations": ["vegetation_contact_primary"],
            "osha_class": "imminent_danger",
            "nesc_rules": ["NESC 218", "NESC 232"],
            "recommendation": "De-energize circuit and clear vegetation before re-energizing",
            "ai_score": 95,
            "confidence": "high",
        },
    },
    {
        "pole_type": "de45c3",
        "description": "Crossarm shows significant rot and splitting at the midpoint. Guy wire corroded at anchor plate.",
        "photo_count": 3,
        "output": {
            "severity": "high",
            "violations": ["crossarm_split", "guy_strand_corroded"],
            "osha_class": "serious",
            "nesc_rules": ["NESC 261", "NESC 235"],
            "recommendation": "Out-of-service order; crossarm replacement and guy wire inspection required",
            "ai_score": 83,
            "confidence": "high",
        },
    },
    {
        "pole_type": "ju40c4",
        "description": "Tall vegetation within 3 feet of conductor clearance zone. Approaching NESC minimum.",
        "photo_count": 1,
        "output": {
            "severity": "medium",
            "violations": ["vegetation_encroachment_primary"],
            "osha_class": "other_than_serious",
            "nesc_rules": ["NESC 218"],
            "recommendation": "Schedule vegetation trim within 60 days per maintenance cycle",
            "ai_score": 72,
            "confidence": "medium",
        },
    },
    {
        "pole_type": "sp35c5",
        "description": "Pole ID tag missing. No visible identification marking on pole body.",
        "photo_count": 1,
        "output": {
            "severity": "low",
            "violations": ["id_tag_missing"],
            "osha_class": "de_minimis",
            "nesc_rules": ["MPSC R 460.601"],
            "recommendation": "Re-tag within 90 days at next scheduled maintenance visit",
            "ai_score": 55,
            "confidence": "high",
        },
    },
    {
        "pole_type": "bank45c3",
        "description": "Transformer oil staining on pole body and ground below. Active leak suspected. Ice loading on conductors.",
        "photo_count": 4,
        "output": {
            "severity": "critical",
            "violations": ["transformer_oil_leak", "clearance_loss_from_ice_sag"],
            "osha_class": "imminent_danger",
            "nesc_rules": ["NESC 250", "NESC 232", "OSHA 1910.269"],
            "recommendation": "Dispatch hazmat; test dielectric strength and replace transformer unit; check ice clearances",
            "ai_score": 91,
            "confidence": "high",
        },
    },
]

SYSTEM_PROMPT = """\
You are an expert utility pole inspection AI trained on OSHA 29 CFR 1903.14, \
NESC 2023 (IEEE C2), MIOSHA Part 86, MPSC R 460.3504, and ANSI O5.1-2023.

Your job is to analyze a field technician's inspection report and return a \
structured JSON assessment with:
- is_utility_structure: boolean, true only when the report/photos describe an electric utility pole, service pole, transmission/distribution structure, transformer bank, recloser, riser, guy/anchor assembly, or directly attached utility equipment
- structure_confidence: integer 0-100 for that utility-structure decision
- rejection_reason: short string when is_utility_structure is false, otherwise null
- severity: "critical" | "high" | "medium" | "low"  (mapped from OSHA class)
- violations: array of detected violation identifiers from the taxonomy
- osha_class: "imminent_danger" | "serious" | "other_than_serious" | "de_minimis"
- nesc_rules: array of applicable NESC/OSHA/ANSI rule references
- recommendation: one-sentence corrective action
- ai_score: integer 0-100 (confidence-weighted risk score)
- confidence: "high" | "medium" | "low"

Severity mapping:
  imminent_danger    → critical  (death or serious harm certain without abatement)
  serious            → high      (substantial probability of death or serious harm)
  other_than_serious → medium    (safety-related, unlikely to cause death)
  de_minimis         → low       (technical/documentation gap only)

Return ONLY valid JSON. No explanation. No markdown fences."""

VISION_SYSTEM_PROMPT = """\
You are an expert utility pole safety inspector with deep knowledge of OSHA 29 CFR 1903.14, \
NESC 2023 (IEEE C2), MIOSHA Part 86, and ANSI O5.1-2023.

Carefully examine the attached field inspection photo(s). Identify every visible defect, \
structural anomaly, clearance violation, or safety hazard.

Return ONLY a single valid JSON object — no markdown, no explanation:
{
  "is_utility_structure": true | false,
  "structure_confidence": 0-100,
  "rejection_reason": null | "short reason this is not a utility pole/utility structure",
  "severity": "critical" | "high" | "medium" | "low",
  "violations": ["violation_id_1", "violation_id_2"],
  "osha_class": "imminent_danger" | "serious" | "other_than_serious" | "de_minimis",
  "nesc_rules": ["NESC 218", "NESC 261", ...],
  "recommendation": "one-sentence corrective action",
  "ai_score": 0-100,
  "confidence": "high" | "medium" | "low",
  "visual_observations": ["brief description of each defect you can see"]
}

First decide whether the image contains an electric utility pole, service pole, distribution or \
transmission structure, transformer bank, recloser, riser, guy/anchor assembly, or directly \
attached utility equipment. If it does not, set is_utility_structure to false, set severity \
"low", violations ["not_utility_structure"], osha_class "de_minimis", and explain why in \
rejection_reason. Do not invent pole findings for non-utility images.

Severity mapping:
  imminent_danger    → critical  (visible immediate collapse or electrocution risk)
  serious            → high      (clear structural or electrical defect requiring prompt repair)
  other_than_serious → medium    (encroachment, wear, or documentation gap without immediate danger)
  de_minimis         → low       (cosmetic or marking issue only)

Use specific violation IDs when confident (e.g. vegetation_contact_primary, crossarm_split, \
pole_lean_excessive, transformer_oil_leak, groundline_decay, guy_strand_corroded). \
If no defect is visible, return severity "low" with violations ["none"] and osha_class "de_minimis"."""


SYNTHESIS_SYSTEM_PROMPT = """\
You are an expert utility pole safety inspector. You have received separate AI analyses of {n} photos \
taken of the SAME pole during one field inspection. Combine them into a single unified assessment.

Return ONLY a single valid JSON object — no markdown, no explanation:
{{
  "severity": "critical" | "high" | "medium" | "low",
  "violations": ["deduplicated union of all violation_ids found across photos"],
  "osha_class": "worst OSHA class across all photos",
  "nesc_rules": ["deduplicated union of all NESC/OSHA/ANSI rules cited"],
  "recommendation": "single highest-priority corrective action for this pole",
  "summary": "2-3 sentence narrative describing overall pole condition and key findings",
  "ai_score": 0-100,
  "confidence": "high" | "medium" | "low"
}}

Rules:
- severity must be the WORST severity found across all photos
- violations must include ALL unique violations from all photos (no duplicates)
- summary must read as a coherent professional assessment, not a list
- if photos disagree on severity, use the most serious"""


# ── IAM token cache ──────────────────────────────────────────────────────────

class _TokenCache:
    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0

    def get(self, api_key: str) -> str:
        if requests is None:
            raise RuntimeError("requests is not installed")
        if self._token and time.time() < self._expires_at - 300:
            return self._token
        resp = requests.post(
            IAM_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}",
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        self._token = body["access_token"]
        self._expires_at = time.time() + body.get("expires_in", 3600)
        return self._token


_token_cache = _TokenCache()


# ── Main analyzer ────────────────────────────────────────────────────────────

class WatsonXAnalyzer:
    """
    Calls ibm/granite-3-8b-instruct on watsonx.ai to classify pole violations
    and severity from a field technician's inspection description.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("WATSONX_API_KEY")
        self.project_id = WATSONX_PROJECT_ID
        self.base_url = WATSONX_URL
        self._configured = bool(self.api_key and requests is not None)

    @property
    def is_configured(self) -> bool:
        return self._configured

    # ── Prompt builder ────────────────────────────────────────────────────────

    def _build_prompt(self, pole_type: str | None, description: str, photo_count: int) -> str:
        parts = [f"<|system|>\n{SYSTEM_PROMPT}\n"]

        # Include few-shot examples
        for ex in FEW_SHOT_EXAMPLES:
            user_msg = (
                f"Pole type: {ex['pole_type']}\n"
                f"Description: {ex['description']}\n"
                f"Photos captured: {ex['photo_count']}"
            )
            parts.append(f"<|user|>\n{user_msg}\n")
            parts.append(f"<|assistant|>\n{json.dumps(ex['output'])}\n")

        # Actual request
        pole_str = pole_type or "unknown"
        user_msg = (
            f"Pole type: {pole_str}\n"
            f"Description: {description or 'No description provided — classify based on pole type and photo count.'}\n"
            f"Photos captured: {photo_count}"
        )
        parts.append(f"<|user|>\n{user_msg}\n<|assistant|>\n")
        return "".join(parts)

    # ── REST calls ────────────────────────────────────────────────────────────

    def _call_granite(self, prompt: str) -> str:
        """Text-only generation via ibm/granite-3-8b-instruct."""
        token = _token_cache.get(self.api_key)  # type: ignore[arg-type]
        url = f"{self.base_url}/ml/v1/text/generation?version={API_VERSION}"
        payload = {
            "model_id": TEXT_MODEL_ID,
            "project_id": self.project_id,
            "input": prompt,
            "parameters": {
                "max_new_tokens": 400,
                "temperature": 0.0,
                "repetition_penalty": 1.1,
                "stop_sequences": ["\n<|user|>", "\n<|system|>"],
            },
        }
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["results"][0]["generated_text"].strip()

    def _call_vision_model(
        self,
        photos: list[str],
        pole_type: str | None,
        description: str,
    ) -> str:
        """
        Multimodal analysis via meta-llama/llama-3-2-11b-vision-instruct.
        Uses the /ml/v1/text/chat endpoint with image_url content blocks.
        """
        token = _token_cache.get(self.api_key)  # type: ignore[arg-type]
        url = f"{self.base_url}/ml/v1/text/chat?version={API_VERSION}"

        # Build the user message content — text instruction + one block per photo
        pole_str = pole_type or "unknown"
        tech_note = f'Tech notes: "{description}"' if description else "No tech notes provided."
        user_text = (
            f"Pole type: {pole_str}. {tech_note}\n\n"
            f"Inspect the attached photo(s) for all safety violations and structural defects. "
            f"Return your assessment as a single JSON object."
        )

        user_content: list[dict] = [{"type": "text", "text": user_text}]
        for photo_url in photos[:MAX_PHOTOS_PER_REQUEST]:
            # Ensure it's a proper data URL; skip malformed entries
            if photo_url.startswith("data:image"):
                user_content.append({"type": "image_url", "image_url": {"url": photo_url}})

        payload = {
            "model_id": VISION_MODEL_ID,
            "project_id": self.project_id,
            "messages": [
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "parameters": {
                "max_new_tokens": 500,
                "temperature": 0.0,
            },
        }
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=45,  # vision calls take a bit longer
        )
        resp.raise_for_status()
        body = resp.json()
        # Chat completions response shape
        return body["choices"][0]["message"]["content"].strip()

    # ── Response parser ───────────────────────────────────────────────────────

    def _parse_response(self, raw: str) -> dict[str, Any]:
        # Vision model may surround the JSON with prose or markdown fences.
        # Try to extract the first {...} block anywhere in the response.
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            raw = json_match.group(0)
        else:
            # Fall back to stripping just leading/trailing markdown fences
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        data = json.loads(raw)

        # Normalise severity
        sev = str(data.get("severity", "medium")).lower()
        if sev not in ("critical", "high", "medium", "low"):
            osha = str(data.get("osha_class", "other_than_serious")).lower()
            sev = OSHA_TO_APP.get(osha, "medium")
        data["severity"] = sev

        # Guarantee required fields
        data.setdefault("violations", [])
        data.setdefault("osha_class", "other_than_serious")
        data.setdefault("nesc_rules", [])
        data.setdefault("recommendation", "Review findings and schedule appropriate corrective action")
        data.setdefault("ai_score", 70)
        data.setdefault("confidence", "medium")
        data.setdefault("is_utility_structure", True)
        data.setdefault("structure_confidence", data.get("ai_score", 70))
        data.setdefault("rejection_reason", None)
        data["powered_by"] = "watsonx.ai · ibm/granite-3-8b-instruct"
        return data

    # ── Rule-based fallback ───────────────────────────────────────────────────

    @staticmethod
    def _rule_based_classify(description: str, photo_count: int) -> dict[str, Any]:
        """
        Simple keyword-based classifier used when watsonx.ai is unavailable.
        Scans the description for known violation terms.
        """
        desc_lower = description.lower()
        detected: list[str] = []
        worst_osha = "de_minimis"
        osha_order = ["de_minimis", "other_than_serious", "serious", "imminent_danger"]
        structure_terms = (
            "pole", "utility", "electric", "distribution", "transmission", "conductor",
            "wire", "transformer", "recloser", "crossarm", "insulator", "guy", "anchor",
            "riser", "service drop", "feeder", "circuit",
        )
        has_structure_context = any(term in desc_lower for term in structure_terms) or photo_count > 0

        for viol, osha in VIOLATION_SEVERITY_MAP.items():
            keyword = viol.replace("_", " ")
            if keyword in desc_lower or viol in desc_lower:
                detected.append(viol)
                if osha_order.index(osha) > osha_order.index(worst_osha):
                    worst_osha = osha

        # Keyword shortcuts
        if any(kw in desc_lower for kw in ("lean", "tilt", "tilting")):
            if "lean" not in str(detected):
                detected.append("pole_lean_excessive")
                worst_osha = "imminent_danger"
        if any(kw in desc_lower for kw in ("rot", "decay", "rotting")):
            if not any("decay" in d or "rot" in d for d in detected):
                detected.append("groundline_decay")
                if osha_order.index("serious") > osha_order.index(worst_osha):
                    worst_osha = "serious"
        if any(kw in desc_lower for kw in ("vegetation", "branch", "tree", "contact")):
            if not any("vegetation" in d or "veg" in d for d in detected):
                detected.append("vegetation_contact_primary")
                worst_osha = "imminent_danger"
        if any(kw in desc_lower for kw in ("insulator", "cracked", "tracking")):
            if not any("insulator" in d for d in detected):
                detected.append("insulator_arc_tracking")
                if osha_order.index("serious") > osha_order.index(worst_osha):
                    worst_osha = "serious"
        if any(kw in desc_lower for kw in ("oil", "leak", "stain", "transformer")):
            if not any("oil" in d or "leak" in d for d in detected):
                detected.append("transformer_oil_leak")
                if osha_order.index("serious") > osha_order.index(worst_osha):
                    worst_osha = "serious"

        if not detected:
            detected = ["none"]
            worst_osha = "de_minimis"

        severity = OSHA_TO_APP.get(worst_osha, "low")
        score_map = {"imminent_danger": 88, "serious": 72, "other_than_serious": 55, "de_minimis": 38}
        score = score_map.get(worst_osha, 50)
        if photo_count > 2:
            score = min(score + 5, 99)

        recs = {
            "imminent_danger": "Immediate isolation and emergency repair order required",
            "serious": "Schedule corrective action within 30 days; restrict climbing until resolved",
            "other_than_serious": "Schedule corrective action within 90 days per maintenance cycle",
            "de_minimis": "Document and address at next scheduled maintenance visit",
        }

        return {
            "severity": severity,
            "violations": detected,
            "osha_class": worst_osha,
            "nesc_rules": [],
            "recommendation": recs.get(worst_osha, "Review and schedule corrective action"),
            "ai_score": score,
            "confidence": "medium",
            "is_utility_structure": has_structure_context,
            "structure_confidence": 55 if has_structure_context else 20,
            "rejection_reason": None if has_structure_context else "No utility pole or utility structure context was detected.",
            "powered_by": "rule-based fallback (watsonx.ai not configured)",
        }

    # ── Synthesis ─────────────────────────────────────────────────────────────

    @staticmethod
    def _merge_analyses(analyses: list[dict[str, Any]]) -> dict[str, Any]:
        """Mechanical fallback: union violations, take worst severity."""
        sev_order = ["low", "medium", "high", "critical"]
        all_viols = list(dict.fromkeys(
            v for a in analyses for v in a.get("violations", [])
        ))
        worst_sev = max(
            (a.get("severity", "medium") for a in analyses),
            key=lambda s: sev_order.index(s) if s in sev_order else 0,
        )
        worst = next((a for a in analyses if a.get("severity") == worst_sev), analyses[0])
        n_issues = len([v for v in all_viols if v not in ("none", "unknown")])
        return {
            "severity": worst_sev,
            "violations": all_viols,
            "osha_class": worst.get("osha_class", "other_than_serious"),
            "nesc_rules": list(dict.fromkeys(
                r for a in analyses for r in a.get("nesc_rules", [])
            )),
            "recommendation": worst.get("recommendation", "Review and schedule corrective action"),
            "summary": (
                f"Analysis of {len(analyses)} photos identified "
                f"{n_issues} violation(s) on this pole. "
                f"Most severe finding: {worst.get('recommendation', 'review required')}."
            ),
            "ai_score": max(a.get("ai_score", 70) for a in analyses),
            "confidence": "medium",
            "powered_by": "merged (synthesis unavailable)",
        }

    def synthesize(
        self,
        pole_id: str,
        pole_type: str | None,
        analyses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Feed N photo analyses into Granite and get back one unified pole assessment.
        Falls back to mechanical merge if watsonx.ai is unavailable or errors.
        """
        if not self.is_configured or not analyses:
            return self._merge_analyses(analyses)

        n = len(analyses)
        pole_str = pole_type or "unknown"

        photo_blocks = []
        for i, a in enumerate(analyses):
            viols = ", ".join(a.get("violations", [])) or "none"
            nesc  = ", ".join(a.get("nesc_rules", [])) or "N/A"
            photo_blocks.append(
                f"Photo {i + 1} — {a.get('photo_label', f'Photo {i + 1}')}:\n"
                f"  Severity: {a.get('severity', 'medium')}  |  OSHA: {a.get('osha_class', 'other_than_serious')}\n"
                f"  Violations: {viols}\n"
                f"  NESC / rules: {nesc}\n"
                f"  Finding: {a.get('recommendation', 'No finding provided')}"
            )

        user_msg = (
            f"Pole ID: {pole_id}  |  Type: {pole_str}\n"
            f"{n} photos analyzed:\n\n"
            + "\n\n".join(photo_blocks)
            + "\n\nSynthesize these into one unified pole assessment."
        )

        sys_prompt = SYNTHESIS_SYSTEM_PROMPT.format(n=n)
        prompt = f"<|system|>\n{sys_prompt}\n<|user|>\n{user_msg}\n<|assistant|>\n"

        logger.info("synthesize() called for pole=%s with %d analyses", pole_id, n)
        try:
            raw = self._call_granite(prompt)
            logger.info("Synthesis raw response (first 300 chars): %s", raw[:300])
            result = self._parse_response(raw)
            result.setdefault(
                "summary",
                "Multiple issues detected across inspected photos. Review all findings and prioritize corrective action.",
            )
            result["powered_by"] = f"watsonx.ai · {TEXT_MODEL_ID} (synthesis)"
            logger.info("Synthesis result: severity=%s violations=%s", result.get("severity"), result.get("violations"))
            return result
        except RequestsHTTPError as exc:
            logger.error("Synthesis HTTP %s: %s", exc.response.status_code, exc.response.text[:300])
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.error("Synthesis parse error: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.error("Synthesis unexpected error: %s", exc)

        return self._merge_analyses(analyses)

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(
        self,
        description: str,
        pole_type: str | None = None,
        photo_count: int = 0,
        photos: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze an inspection report and return severity + violation classification.

        When `photos` (base64 data URLs) are provided, routes to the vision model
        (llama-3-2-11b-vision-instruct) so it can examine actual pixel content.
        Falls back to text-only Granite when no photos are supplied, and to the
        rule-based classifier if watsonx.ai is not configured or errors.
        """
        if not self.is_configured:
            logger.warning("WATSONX_API_KEY not set — using rule-based fallback")
            return self._rule_based_classify(description, photo_count)

        # ── Vision path (photos provided) ──────────────────────────────────────
        valid_photos = [p for p in (photos or []) if p and p.startswith("data:image")]
        logger.info(
            "analyze() called: photo_count=%d valid_photos=%d desc_len=%d",
            photo_count, len(valid_photos), len(description or ""),
        )
        if valid_photos:
            logger.info("→ Routing to VISION model (%s)", VISION_MODEL_ID)
            try:
                raw = self._call_vision_model(valid_photos, pole_type, description)
                logger.info("Vision model raw response (first 300 chars): %s", raw[:300])
                result = self._parse_response(raw)
                result["powered_by"] = f"watsonx.ai · {VISION_MODEL_ID} ({len(valid_photos)} photo{'s' if len(valid_photos) != 1 else ''})"
                logger.info("Vision result: severity=%s violations=%s", result.get("severity"), result.get("violations"))
                return result
            except RequestsHTTPError as exc:
                logger.error("vision model HTTP %s: %s", exc.response.status_code, exc.response.text[:300])
                logger.info("Falling back to text-only Granite")
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.error("vision model parse error: %s", exc)
                logger.info("Falling back to text-only Granite")
            except Exception as exc:  # noqa: BLE001
                logger.error("vision model unexpected error: %s", exc)
                logger.info("Falling back to text-only Granite")

        # ── Text-only path (no photos, or vision call failed) ──────────────────
        logger.info("→ Routing to TEXT model (%s)", TEXT_MODEL_ID)
        try:
            prompt = self._build_prompt(pole_type, description, photo_count)
            raw = self._call_granite(prompt)
            logger.info("Granite raw response (first 300 chars): %s", raw[:300])
            result = self._parse_response(raw)
            result["powered_by"] = f"watsonx.ai · {TEXT_MODEL_ID}"
            return result
        except RequestsHTTPError as exc:
            logger.error("Granite HTTP %s: %s", exc.response.status_code, exc.response.text[:300])
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.error("Granite parse error: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.error("Granite unexpected error: %s", exc)

        # ── Final fallback ─────────────────────────────────────────────────────
        result = self._rule_based_classify(description, photo_count)
        result["powered_by"] = "rule-based fallback (watsonx.ai error)"
        return result


# ── Module-level singleton ────────────────────────────────────────────────────

_analyzer: WatsonXAnalyzer | None = None


def get_analyzer() -> WatsonXAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = WatsonXAnalyzer()
    return _analyzer
