"""Settings, read from environment variables with sensible defaults.

Every path defaults to a location inside the backend folder, so the app
runs with no configuration once the model weights are in ``models/``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent


def _path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return Path(value).expanduser().resolve() if value else default


def _float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


@dataclass(frozen=True)
class Settings:
    # The trained YOLO11n weights from the notebook (cell 12 saves them to
    # Google Drive as car_damage_yolo11n_improved.pt).
    model_path: Path = field(
        default_factory=lambda: _path(
            "MODEL_PATH", BACKEND_DIR / "models" / "car_damage_yolo11n_improved.pt"
        )
    )
    db_path: Path = field(
        default_factory=lambda: _path("DB_PATH", BACKEND_DIR / "data" / "repair_costs.db")
    )
    upload_dir: Path = field(
        default_factory=lambda: _path("UPLOAD_DIR", BACKEND_DIR / "data" / "uploads")
    )
    frontend_dist: Path = field(
        default_factory=lambda: _path("FRONTEND_DIST", PROJECT_DIR / "frontend" / "dist")
    )
    # Same defaults as the notebook: conf=0.25, imgsz=640.
    default_confidence: float = field(default_factory=lambda: _float("CONFIDENCE", 0.25))
    image_size: int = field(default_factory=lambda: _int("IMAGE_SIZE", 640))
    max_upload_mb: int = field(default_factory=lambda: _int("MAX_UPLOAD_MB", 15))
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip()
            for o in os.getenv(
                "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",")
            if o.strip()
        )
    )


def get_settings() -> Settings:
    return Settings()
