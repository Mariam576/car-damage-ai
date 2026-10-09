from app.assessment import build_detections, inspection_priority, iou, summarise
from app.detector import RawDetection


def test_iou_matches_notebook_definition():
    assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1
    assert iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0
    assert round(iou((0, 0, 10, 10), (5, 0, 15, 10)), 4) == round(50 / 150, 4)
    assert iou((0, 0, 0, 0), (0, 0, 0, 0)) == 0


def test_priority_rules():
    assert inspection_priority(["dent"]) == "Visual review required"
    assert inspection_priority(["dent", "tire flat"]) == "Prompt inspection"
    assert inspection_priority([]) == "No damage detected by model"


def test_summary_figures():
    raw = [
        RawDetection("scratch", 0.9125, (0, 0, 500, 500)),
        RawDetection("scratch", 0.3051, (900, 600, 1000, 667)),
    ]
    dets = build_detections(raw, 1000, 667, {"scratch": "Scratch"})
    assert dets[1]["low_confidence"] is True and dets[0]["low_confidence"] is False
    s = summarise(dets, {"scratch": "Scratch"})
    assert s["total_detections"] == 2
    assert s["highest_confidence"] == 91.25
    assert s["average_confidence"] == round((91.25 + 30.51) / 2, 2)
    assert s["largest_coverage_pct"] == round(250000 / 667000 * 100, 2)
    assert s["damage_types"] == ["scratch"]
