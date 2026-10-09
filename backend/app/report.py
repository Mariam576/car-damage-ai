"""Builds the repair-cost report (notebook cells 25-27, from the SQLite prices)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .database import Database, utc_now
from .schemas import ReportRequest

ESTIMATE_STATUS = "Indicative only - repair method requires verification"
DISCLAIMER = (
    "Damage was detected automatically from one photo by a YOLO11n model; it can miss damage "
    "or report damage that is not there, and it does not judge severity. Prices are published "
    "UK guide ranges from the sources listed, not quotations: the cost of a real repair depends "
    "on the vehicle, paint, parts, labour rates and location. Get a quote from a repairer "
    "after a physical inspection."
)
UNPRICED_NOTE = "Professional assessment required"


class ReportError(ValueError):
    """The selections do not match the analysis or the price database."""


def _money(value: float) -> float:
    return round(float(value), 2)


def new_report_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"RC-{today}-{uuid.uuid4().hex[:6].upper()}"


def build_report(analysis: dict, request: ReportRequest, db: Database) -> dict:
    summary = analysis["summary"]
    by_type = {t["damage_type"]: t for t in summary["by_type"]}
    labels = {c["name"]: c["label"] for c in db.damage_classes()}

    # Damage types with at least one repair method in the database must be
    # addressed (priced or excluded); the others are listed as unpriced.
    priceable = {t for t in by_type if db.repair_methods(t)}

    seen: set[str] = set()
    for sel in request.selections:
        if sel.damage_type not in by_type:
            raise ReportError(f"'{sel.damage_type}' was not detected in this analysis")
        if sel.damage_type in seen:
            raise ReportError(f"'{sel.damage_type}' has more than one selection")
        seen.add(sel.damage_type)

    missing = sorted(priceable - seen)
    if missing:
        raise ReportError(
            "Choose a repair method (or exclude) for: " + ", ".join(labels.get(m, m) for m in missing)
        )

    lines, excluded = [], []
    for sel in request.selections:
        t = by_type[sel.damage_type]
        if sel.excluded:
            excluded.append(
                {
                    "damage_type": sel.damage_type,
                    "label": t["label"],
                    "detections": t["count"],
                    "max_confidence": t["max_confidence"],
                    "note": sel.note or "Excluded by reviewer",
                }
            )
            continue
        method = db.repair_method(sel.method_id)
        if method is None:
            raise ReportError(f"Repair method {sel.method_id} does not exist")
        if method["damage_type"] != sel.damage_type:
            raise ReportError(
                f"'{method['method']}' is a repair for {method['damage_type']}, not {sel.damage_type}"
            )
        qty = sel.quantity
        line_min = _money(method["min_gbp"] * qty)
        line_max = _money(method["max_gbp"] * qty)
        lines.append(
            {
                "damage_type": sel.damage_type,
                "label": t["label"],
                "detections": t["count"],
                "max_confidence": t["max_confidence"],
                "method_id": method["id"],
                "method": method["method"],
                "description": method["description"],
                "quantity": qty,
                "unit": method["unit"],
                "unit_min_gbp": _money(method["min_gbp"]),
                "unit_max_gbp": _money(method["max_gbp"]),
                "max_open": method["max_open"],
                "min_gbp": line_min,
                "max_gbp": line_max,
                "midpoint_gbp": _money((line_min + line_max) / 2),
                "source": method["source"],
                "note": sel.note,
            }
        )

    unpriced = [
        {"damage_type": t, "label": by_type[t]["label"], "detections": by_type[t]["count"],
         "note": UNPRICED_NOTE}
        for t in sorted(set(by_type) - priceable)
    ]

    total_min = _money(sum(line["min_gbp"] for line in lines))
    total_max = _money(sum(line["max_gbp"] for line in lines))

    return {
        "id": new_report_id(),
        "analysis_id": analysis["id"],
        "created_at": utc_now(),
        "image_name": analysis["image_name"],
        "image_url": f"/api/analyses/{analysis['id']}/image",
        "image_width": analysis["image_width"],
        "image_height": analysis["image_height"],
        "model_name": analysis["model_name"],
        "confidence_threshold": analysis["confidence_threshold"],
        "detections": analysis["detections"],
        "summary": summary,
        "inspection_priority": summary["inspection_priority"],
        "physical_severity": summary["physical_severity"],
        "lines": lines,
        "excluded": excluded,
        "unpriced": unpriced,
        "totals": {
            "currency": "GBP",
            "min_gbp": total_min,
            "max_gbp": total_max,
            "midpoint_gbp": _money((total_min + total_max) / 2),
            "max_open": any(line["max_open"] for line in lines),
        },
        "estimate_status": ESTIMATE_STATUS,
        "disclaimer": DISCLAIMER,
    }
