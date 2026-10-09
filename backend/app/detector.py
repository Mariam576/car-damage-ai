"""YOLO damage detector (the model trained in DAMAGEPREDICTION.ipynb)."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from PIL import Image

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RawDetection:
    class_name: str
    confidence: float  # 0..1
    box: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels


class ModelUnavailable(RuntimeError):
    """The weights file is missing or could not be loaded."""


class Detector(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def available(self) -> bool: ...

    @property
    def status(self) -> dict: ...

    def detect(self, image: Image.Image, confidence: float) -> list[RawDetection]: ...


class YoloDetector:
    """Wraps ``ultralytics.YOLO``; loads the weights once and serialises predictions."""

    def __init__(self, model_path: Path, image_size: int = 640):
        self.model_path = Path(model_path)
        self.image_size = image_size
        self._model = None
        self._error: str | None = None
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return self.model_path.name

    @property
    def available(self) -> bool:
        return self._model is not None

    @property
    def status(self) -> dict:
        return {
            "loaded": self.available,
            "model_file": str(self.model_path),
            "classes": list(self._model.names.values()) if self._model is not None else [],
            "error": self._error,
        }

    def load(self) -> None:
        if self._model is not None:
            return
        if not self.model_path.is_file():
            self._error = (
                f"Model weights not found at {self.model_path}. Copy "
                "car_damage_yolo11n_improved.pt (saved by the notebook to Google Drive, "
                "MyDrive/Car_Damage_AI/models/) into backend/models/, or set MODEL_PATH."
            )
            raise ModelUnavailable(self._error)
        try:
            from ultralytics import YOLO  # imported here: slow import, optional in tests

            self._model = YOLO(str(self.model_path))
            self._error = None
            log.info("Loaded YOLO model %s with classes %s", self.model_path, self._model.names)
        except Exception as exc:  # pragma: no cover - depends on the weights file
            self._error = f"Could not load {self.model_path}: {exc}"
            raise ModelUnavailable(self._error) from exc

    def detect(self, image: Image.Image, confidence: float) -> list[RawDetection]:
        if self._model is None:
            self.load()
        with self._lock:
            result = self._model.predict(
                source=image, conf=confidence, imgsz=self.image_size, verbose=False
            )[0]
        names = result.names
        detections: list[RawDetection] = []
        for box in result.boxes:
            class_id = int(box.cls.item())
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
            detections.append(
                RawDetection(
                    class_name=str(names[class_id]),
                    confidence=float(box.conf.item()),
                    box=(x1, y1, x2, y2),
                )
            )
        return detections
