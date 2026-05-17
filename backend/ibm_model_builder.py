from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .inspection_training_data import PROJECT_ROOT, build_training_records

DEFAULT_PACKAGE_DIR = PROJECT_ROOT / "dataset" / "inspection_training"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for row in rows:
            file.write(json.dumps(row, sort_keys=True) + "\n")


def build_ibm_model_package(output_dir: Path = DEFAULT_PACKAGE_DIR) -> dict[str, Any]:
    """Build a local IBM-ready training package from the SVG exemplar library.

    The generated files are intentionally provider-neutral JSONL plus an IBM-oriented
    manifest. A caller can upload the referenced preview images and labels to MVI, or
    convert the message JSONL for watsonx model tuning/evaluation.
    """
    records = build_training_records()
    severity_counts = Counter(record.dashboard_severity for record in records)
    violation_counts = Counter(record.violation_type_id or "none" for record in records)
    scene_type_counts = Counter(record.scene_type for record in records)
    weather_counts = Counter(record.weather_condition or "none" for record in records)

    image_classification_rows = []
    chat_rows = []
    dashboard_contract_rows = []

    for record in records:
        image_path = record.source_preview or record.source_svg
        image_classification_rows.append(
            {
                "id": record.record_id,
                "image": image_path,
                "labels": {
                    "dashboard_severity": record.dashboard_severity,
                    "violation_type_id": record.violation_type_id,
                    "violation_family": record.violation_family,
                    "scene_type": record.scene_type,
                    "weather_condition": record.weather_condition,
                },
                "defects": [
                    {
                        "violation": defect.violation,
                        "severity": defect.severity,
                        "dashboard_severity": defect.dashboard_severity,
                        "violation_type_id": defect.violation_type_id,
                    }
                    for defect in record.defects
                ],
                "expected_dashboard_output": record.dashboard_output,
            }
        )
        chat_rows.append(
            {
                "id": record.record_id,
                "image": image_path,
                "messages": record.ibm_messages,
                "metadata": {
                    "scene_id": record.scene_id,
                    "pole_type_id": record.pole_type_id,
                    "dashboard_severity": record.dashboard_severity,
                    "violation_type_id": record.violation_type_id,
                },
            }
        )
        dashboard_contract_rows.append(
            {
                "id": record.record_id,
                "input": {
                    "image": image_path,
                    "pole_type": record.pole_type,
                    "scene_id": record.scene_id,
                },
                "expected_output": record.dashboard_output,
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_dir / "ibm_mvi_image_labels.jsonl", image_classification_rows)
    _write_jsonl(output_dir / "ibm_messages.jsonl", chat_rows)
    _write_jsonl(output_dir / "dashboard_contracts.jsonl", dashboard_contract_rows)

    manifest = {
        "name": "amped-up-pole-inspection-v0.7",
        "description": "Pole inspection model package generated from SVG exemplar scenes.",
        "record_count": len(records),
        "source": "dataset/svgs/out",
        "image_label_file": str((output_dir / "ibm_mvi_image_labels.jsonl").relative_to(PROJECT_ROOT)),
        "message_file": str((output_dir / "ibm_messages.jsonl").relative_to(PROJECT_ROOT)),
        "dashboard_contract_file": str((output_dir / "dashboard_contracts.jsonl").relative_to(PROJECT_ROOT)),
        "task_targets": [
            "dashboard_severity",
            "violation_type_id",
            "violation_family",
            "scene_type",
            "weather_condition",
        ],
        "severity_counts": dict(sorted(severity_counts.items())),
        "violation_type_counts": dict(sorted(violation_counts.items())),
        "scene_type_counts": dict(sorted(scene_type_counts.items())),
        "weather_condition_counts": dict(sorted(weather_counts.items())),
        "recommended_workflow": [
            "Upload preview PNGs as image assets in IBM MVI.",
            "Use ibm_mvi_image_labels.jsonl to map each image to classification labels.",
            "Train detection/classification models for visible defect categories and severity.",
            "Use ibm_messages.jsonl for a companion watsonx/LLM evaluation or tuning set.",
            "Validate model output against dashboard_contracts.jsonl before enabling live report automation.",
        ],
    }
    _write_json(output_dir / "ibm_mvi_manifest.json", manifest)
    return manifest


def get_ibm_model_build_plan() -> dict[str, Any]:
    records = build_training_records()
    return {
        "role_of_ibm_mvi": (
            "IBM MVI trains/hosts the visual recognition model that classifies uploaded pole images."
        ),
        "record_count": len(records),
        "local_package_dir": str(DEFAULT_PACKAGE_DIR.relative_to(PROJECT_ROOT)),
        "outputs": [
            "ibm_mvi_manifest.json",
            "ibm_mvi_image_labels.jsonl",
            "ibm_messages.jsonl",
            "dashboard_contracts.jsonl",
        ],
        "live_app_flow": [
            "Field technician submits photos.",
            "IBM watsonx Granite Vision analyzes photos and identifies structural violations.",
            "AI maps findings to NESC/OSHA/MPSC rules and assigns dashboard severity.",
            "Dashboard report stores violation_type_id, evidence requirements, specifications, and action.",
        ],
    }

