"""Turns raw YOLO boxes into the damage assessment from the notebook.

Cells 14, 19, 21-23 and 28 of DAMAGEPREDICTION.ipynb: confidence and image
coverage per box, the inspection-priority rule, box overlap (IoU) and the
summary. Physical severity is not assessed, as in the notebook.
"""

from __future__ import annotations

from itertools import combinations
from statistics import mean

from .detector import RawDetection

# Notebook cell 23: damage that affects safety needs a prompt inspection.
SAFETY_RELATED = {"glass shatter", "lamp broken", "tire flat"}

LOW_CONFIDENCE_PCT = 50.0

PRIORITY_PROMPT = "Prompt inspection"
PRIORITY_REVIEW = "Visual review required"
PRIORITY_NONE = "No damage detected by model"


def _label(class_name: str, labels: dict[str, str]) -> str:
    return labels.get(class_name, class_name.capitalize())


def iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def build_detections(
    raw: list[RawDetection], width: int, height: int, labels: dict[str, str]
) -> list[dict]:
    image_area = float(width * height) or 1.0
    ordered = sorted(raw, key=lambda d: d.confidence, reverse=True)
    detections = []
    for index, d in enumerate(ordered, start=1):
        x1, y1, x2, y2 = d.box
        w, h = max(0.0, x2 - x1), max(0.0, y2 - y1)
        confidence_pct = round(d.confidence * 100, 2)
        detections.append(
            {
                "id": index,
                "damage_type": d.class_name,
                "label": _label(d.class_name, labels),
                "confidence": confidence_pct,
                "low_confidence": confidence_pct < LOW_CONFIDENCE_PCT,
                "box": {"x1": round(x1, 1), "y1": round(y1, 1), "x2": round(x2, 1), "y2": round(y2, 1)},
                "width_px": round(w, 1),
                "height_px": round(h, 1),
                "coverage_pct": round(w * h / image_area * 100, 2),
            }
        )
    return detections


def inspection_priority(damage_types: list[str]) -> str:
    if any(d in SAFETY_RELATED for d in damage_types):
        return PRIORITY_PROMPT
    if damage_types:
        return PRIORITY_REVIEW
    return PRIORITY_NONE


def summarise(detections: list[dict], labels: dict[str, str]) -> dict:
    damage_types = sorted({d["damage_type"] for d in detections})
    confidences = [d["confidence"] for d in detections]

    overlaps = []
    for a, b in combinations(detections, 2):
        box_a = tuple(a["box"].values())
        box_b = tuple(b["box"].values())
        overlaps.append(
            {"pair": [a["id"], b["id"]], "iou_pct": round(iou(box_a, box_b) * 100, 2)}
        )
    max_overlap = max((o["iou_pct"] for o in overlaps), default=0.0)

    by_type = []
    for t in damage_types:
        items = [d for d in detections if d["damage_type"] == t]
        by_type.append(
            {
                "damage_type": t,
                "label": _label(t, labels),
                "count": len(items),
                "max_confidence": max(d["confidence"] for d in items),
                "safety_related": t in SAFETY_RELATED,
            }
        )

    return {
        "total_detections": len(detections),
        "damage_types": damage_types,
        "by_type": by_type,
        "highest_confidence": max(confidences) if confidences else None,
        "average_confidence": round(mean(confidences), 2) if confidences else None,
        "largest_coverage_pct": max((d["coverage_pct"] for d in detections), default=None),
        "max_overlap_pct": max_overlap,
        "substantial_overlaps": [o for o in overlaps if o["iou_pct"] >= 50],
        "inspection_priority": inspection_priority(damage_types),
        "physical_severity": "Not assessed",
    }
