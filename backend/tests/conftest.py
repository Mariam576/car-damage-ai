from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings  # noqa: E402
from app.detector import RawDetection  # noqa: E402
from app.main import create_app  # noqa: E402


class FakeDetector:
    """Stands in for YOLO: returns preset boxes above the confidence threshold."""

    def __init__(self, detections: list[RawDetection] | None = None):
        self.detections = detections or []
        self.calls: list[tuple[tuple[int, int], float]] = []

    name = "fake_model.pt"
    available = True

    @property
    def status(self) -> dict:
        return {"loaded": True, "model_file": "fake_model.pt", "classes": [], "error": None}

    def detect(self, image, confidence):
        self.calls.append((image.size, confidence))
        return [d for d in self.detections if d.confidence >= confidence]


def make_settings(tmp_path: Path, **overrides) -> Settings:
    values = dict(
        model_path=tmp_path / "missing.pt",
        db_path=tmp_path / "test.db",
        upload_dir=tmp_path / "uploads",
        frontend_dist=tmp_path / "no-frontend",
        default_confidence=0.25,
        image_size=640,
        max_upload_mb=2,
        cors_origins=("http://localhost:5173",),
    )
    values.update(overrides)
    return Settings(**values)


def jpeg_bytes(size=(1000, 667), color=(120, 130, 140), exif=None) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color)
    if exif is not None:
        img.save(buf, format="JPEG", exif=exif)
    else:
        img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def detector() -> FakeDetector:
    return FakeDetector()


@pytest.fixture
def client(tmp_path, detector):
    app = create_app(make_settings(tmp_path), detector=detector)
    with TestClient(app) as c:
        yield c


def upload(client, data: bytes | None = None, name="car.jpg", ctype="image/jpeg", **form):
    return client.post(
        "/api/analyses",
        files={"image": (name, data if data is not None else jpeg_bytes(), ctype)},
        data={k: str(v) for k, v in form.items()},
    )
