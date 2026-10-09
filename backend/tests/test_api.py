from __future__ import annotations

import io

from fastapi.testclient import TestClient
from PIL import Image

from app.detector import RawDetection
from app.main import create_app

from conftest import FakeDetector, jpeg_bytes, make_settings, upload

DENT = RawDetection("dent", 0.6461, (300.0, 200.0, 500.0, 350.0))


def method_id(options: list[dict], name: str) -> int:
    return next(m["id"] for m in options if m["method"] == name)


# ------------------------------------------------------------------ reference
def test_health_and_reference_data(client):
    health = client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["database"]["repair_methods"] == 16
    assert health["database"]["sources"] == 9

    classes = client.get("/api/damage-classes").json()
    assert [c["name"] for c in classes] == [
        "dent", "scratch", "crack", "glass shatter", "lamp broken", "tire flat",
    ]
    for c in classes:
        assert c["repair_methods"], f"{c['name']} has no repair methods"
        for m in c["repair_methods"]:
            assert 0 < m["min_gbp"] <= m["max_gbp"]
            assert m["source"]["url"].startswith("https://")
            assert m["source"]["publisher"] and m["source"]["note"]
            assert m["source"]["retrieved_on"] == "2026-10-09"


def test_notebook_scratch_methods_are_present(client):
    names = [m["method"] for m in client.get("/api/repair-methods?damage_type=scratch").json()]
    assert names == [
        "Clear-coat scratch repair",
        "Paintwork scratch repair",
        "Deep scratch repair",
        "Full-panel repaint",
    ]


# ------------------------------------------------------------------- analysis
def test_dent_example_from_notebook(client, detector):
    detector.detections = [DENT]
    r = upload(client)
    assert r.status_code == 201, r.text
    body = r.json()
    det = body["detections"][0]
    assert det["damage_type"] == "dent" and det["label"] == "Dent"
    assert det["confidence"] == 64.61
    assert det["coverage_pct"] == round(200 * 150 / (1000 * 667) * 100, 2)
    assert body["summary"]["inspection_priority"] == "Visual review required"
    assert body["summary"]["physical_severity"] == "Not assessed"
    assert [m["method"] for m in body["repair_options"]["dent"]] == [
        "Paintless dent removal", "Dent repair and repaint",
    ]
    assert detector.calls == [((1000, 667), 0.25)]
    img = client.get(body["image_url"])
    assert img.status_code == 200 and img.headers["content-type"] == "image/jpeg"
    assert client.get(f"/api/analyses/{body['id']}").json()["detections"] == body["detections"]


def test_safety_damage_needs_prompt_inspection(client, detector):
    detector.detections = [
        RawDetection("scratch", 0.9, (0, 0, 100, 100)),
        RawDetection("glass shatter", 0.98, (100, 100, 400, 300)),
    ]
    body = upload(client).json()
    assert body["summary"]["inspection_priority"] == "Prompt inspection"
    # Ordered by confidence, highest first.
    assert [d["damage_type"] for d in body["detections"]] == ["glass shatter", "scratch"]


def test_no_damage(client):
    body = upload(client).json()
    assert body["detections"] == []
    assert body["summary"]["inspection_priority"] == "No damage detected by model"
    report = client.post("/api/reports", json={"analysis_id": body["id"], "selections": []})
    assert report.status_code == 201
    assert report.json()["totals"]["min_gbp"] == 0


def test_confidence_threshold_is_passed_and_validated(client, detector):
    detector.detections = [DENT]
    body = upload(client, confidence=0.7).json()
    assert body["detections"] == [] and detector.calls[-1][1] == 0.7
    assert upload(client, confidence=0).status_code == 422


def test_overlap_between_boxes(client, detector):
    detector.detections = [
        RawDetection("scratch", 0.9, (0, 0, 100, 100)),
        RawDetection("scratch", 0.8, (50, 0, 150, 100)),
    ]
    summary = upload(client).json()["summary"]
    assert summary["max_overlap_pct"] == round(5000 / 15000 * 100, 2)
    assert summary["by_type"][0]["count"] == 2


def test_rejects_bad_uploads(client):
    assert upload(client, b"not an image", name="x.jpg").status_code == 400
    assert upload(client, b"", name="x.jpg").status_code == 400
    assert upload(client, b"%PDF-1.4", name="x.pdf", ctype="application/pdf").status_code == 415
    big = jpeg_bytes() + b"\0" * (2 * 1024 * 1024)
    assert upload(client, big).status_code == 413


def test_phone_photo_rotation_is_applied(client, detector):
    exif = Image.Exif()
    exif[0x0112] = 6  # stored landscape, displayed portrait
    body = upload(client, jpeg_bytes(size=(400, 300), exif=exif)).json()
    assert (body["image_width"], body["image_height"]) == (300, 400)
    saved = Image.open(io.BytesIO(client.get(body["image_url"]).content))
    assert saved.size == (300, 400)
    assert not saved.getexif().get(0x0112)


def test_missing_model_gives_clear_503(tmp_path):
    app = create_app(make_settings(tmp_path))  # real YoloDetector, no weights file
    with TestClient(app) as c:
        health = c.get("/api/health").json()
        assert health["status"] == "model_missing"
        assert "car_damage_yolo11n_improved.pt" in health["model"]["error"]
        r = upload(c)
        assert r.status_code == 503
        assert "backend/models" in r.json()["detail"]


# --------------------------------------------------------------------- report
def test_report_prices_from_database(client, detector):
    detector.detections = [DENT, RawDetection("dent", 0.4, (10, 10, 50, 50))]
    analysis = upload(client).json()
    pdr = method_id(analysis["repair_options"]["dent"], "Paintless dent removal")

    r = client.post(
        "/api/reports",
        json={"analysis_id": analysis["id"],
              "selections": [{"damage_type": "dent", "method_id": pdr, "quantity": 2}]},
    )
    assert r.status_code == 201, r.text
    report = r.json()
    line = report["lines"][0]
    assert (line["unit_min_gbp"], line["unit_max_gbp"]) == (60, 180)
    assert (line["min_gbp"], line["max_gbp"], line["midpoint_gbp"]) == (120, 360, 240)
    assert line["detections"] == 2 and line["max_confidence"] == 64.61
    assert line["source"]["publisher"] == "Dentscout"
    assert line["source"]["url"] == "https://dentscout.co.uk/blog/dent-repair-cost-uk"
    assert report["totals"] == {
        "currency": "GBP", "min_gbp": 120, "max_gbp": 360, "midpoint_gbp": 240, "max_open": False,
    }
    assert report["estimate_status"].startswith("Indicative only")
    assert report["id"].startswith("RC-")

    assert client.get(f"/api/reports/{report['id']}").json() == report
    listed = client.get("/api/reports").json()
    assert listed[0]["id"] == report["id"] and listed[0]["damage_types"] == ["dent"]


def test_report_with_exclusion_and_open_ended_price(client, detector):
    detector.detections = [
        RawDetection("crack", 0.5, (0, 0, 10, 10)),
        RawDetection("scratch", 0.3, (20, 20, 40, 40)),
    ]
    analysis = upload(client).json()
    replace = method_id(analysis["repair_options"]["crack"], "Panel replacement")
    report = client.post(
        "/api/reports",
        json={"analysis_id": analysis["id"], "selections": [
            {"damage_type": "crack", "method_id": replace},
            {"damage_type": "scratch", "excluded": True, "note": "Reflection, not a scratch"},
        ]},
    ).json()
    assert report["totals"]["max_open"] is True
    assert report["totals"]["min_gbp"] == 600
    assert report["excluded"][0]["note"] == "Reflection, not a scratch"


def test_report_validation(client, detector):
    detector.detections = [DENT, RawDetection("scratch", 0.8, (0, 0, 10, 10))]
    analysis = upload(client).json()
    pdr = method_id(analysis["repair_options"]["dent"], "Paintless dent removal")
    clear = method_id(analysis["repair_options"]["scratch"], "Clear-coat scratch repair")

    def post(selections):
        return client.post("/api/reports", json={"analysis_id": analysis["id"], "selections": selections})

    # every detected damage type must be priced or excluded
    r = post([{"damage_type": "dent", "method_id": pdr}])
    assert r.status_code == 422 and "Scratch" in r.json()["detail"]
    # a scratch method cannot price a dent
    r = post([{"damage_type": "dent", "method_id": clear}, {"damage_type": "scratch", "method_id": clear}])
    assert r.status_code == 422 and "not dent" in r.json()["detail"]
    # damage that was not detected
    r = post([{"damage_type": "tire flat", "excluded": True}])
    assert r.status_code == 422
    # duplicates, a method plus exclusion, no method, bad quantity, unknown method
    assert post([{"damage_type": "dent", "method_id": pdr}] * 2).status_code == 422
    assert post([{"damage_type": "dent", "method_id": pdr, "excluded": True}]).status_code == 422
    assert post([{"damage_type": "dent"}]).status_code == 422
    assert post([{"damage_type": "dent", "method_id": pdr, "quantity": 0}]).status_code == 422
    r = post([{"damage_type": "dent", "method_id": 9999}, {"damage_type": "scratch", "excluded": True}])
    assert r.status_code == 422
    assert client.post("/api/reports", json={"analysis_id": "nope", "selections": []}).status_code == 404


def test_class_without_prices_is_listed_for_assessment(client, detector):
    # e.g. weights trained with an extra class that has no prices yet
    detector.detections = [RawDetection("bumper missing", 0.7, (0, 0, 10, 10))]
    analysis = upload(client).json()
    assert analysis["repair_options"] == {"bumper missing": []}
    report = client.post("/api/reports", json={"analysis_id": analysis["id"], "selections": []}).json()
    assert report["unpriced"][0]["note"] == "Professional assessment required"
    assert report["totals"]["max_gbp"] == 0


def test_old_reports_keep_their_prices(tmp_path):
    detector = FakeDetector([DENT])
    settings = make_settings(tmp_path)
    app = create_app(settings, detector=detector)
    with TestClient(app) as c:
        analysis = upload(c).json()
        pdr = method_id(analysis["repair_options"]["dent"], "Paintless dent removal")
        report = c.post("/api/reports", json={"analysis_id": analysis["id"], "selections": [
            {"damage_type": "dent", "method_id": pdr}]}).json()
        with app.state.db.connect() as conn:
            conn.execute("UPDATE repair_methods SET min_gbp = 999, max_gbp = 1999 WHERE id = ?", (pdr,))
        assert c.get(f"/api/reports/{report['id']}").json()["totals"]["min_gbp"] == 60
