"""FastAPI application: upload a car photo, detect damage, price the repair.

Flow (matches the notebook):
  POST /api/analyses        upload image -> YOLO detections + repair options
  POST /api/reports         chosen repair methods -> repair-cost report (UK prices, sources)
  GET  /api/reports/{id}    a saved report
Run:  uvicorn app.main:app --reload   (from the backend folder)
"""

import io
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError

from . import assessment
from .config import Settings, get_settings
from .database import Database, utc_now
from .detector import Detector, ModelUnavailable, YoloDetector
from .report import ReportError, build_report
from .schemas import ReportRequest

log = logging.getLogger("car_damage")

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp", "application/octet-stream"}
MIN_CONFIDENCE, MAX_CONFIDENCE = 0.05, 0.95


def create_app(settings: Settings | None = None, detector: Detector | None = None) -> FastAPI:
    settings = settings or get_settings()
    db = Database(settings.db_path)
    detector = detector or YoloDetector(settings.model_path, settings.image_size)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db.init()
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        if isinstance(detector, YoloDetector):
            try:
                detector.load()
            except ModelUnavailable as exc:
                log.warning("%s", exc)
        yield

    app = FastAPI(
        title="Car Damage Repair-Cost API",
        version="1.0.0",
        description="YOLO car-damage detection with UK repair-cost estimates from a SQLite price database.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.db = db
    app.state.detector = detector

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    def labels() -> dict[str, str]:
        return {c["name"]: c["label"] for c in db.damage_classes()}

    def repair_options(damage_types: list[str]) -> dict[str, list[dict]]:
        return {t: db.repair_methods(t) for t in damage_types}

    def analysis_response(analysis: dict) -> dict:
        out = {k: v for k, v in analysis.items() if k != "image_file"}
        out["image_url"] = f"/api/analyses/{analysis['id']}/image"
        out["repair_options"] = repair_options(analysis["summary"]["damage_types"])
        return out

    # ---------------------------------------------------------------- health
    @app.get("/api/health")
    def health() -> dict:
        status = detector.status
        return {
            "status": "ok" if detector.available else "model_missing",
            "model": status,
            "database": {
                "path": str(settings.db_path),
                "repair_methods": len(db.repair_methods()),
                "sources": len(db.sources()),
            },
            "default_confidence": settings.default_confidence,
        }

    # ------------------------------------------------------- reference data
    @app.get("/api/damage-classes")
    def damage_classes() -> list[dict]:
        return [{**c, "repair_methods": db.repair_methods(c["name"])} for c in db.damage_classes()]

    @app.get("/api/repair-methods")
    def repair_methods(damage_type: str | None = None) -> list[dict]:
        return db.repair_methods(damage_type)

    @app.get("/api/sources")
    def sources() -> list[dict]:
        return db.sources()

    # ------------------------------------------------------------- analyses
    @app.post("/api/analyses", status_code=201)
    async def create_analysis(
        image: UploadFile = File(..., description="Car photo (JPEG, PNG, WebP or BMP)"),
        confidence: float | None = Form(default=None),
    ) -> dict:
        conf = settings.default_confidence if confidence is None else confidence
        if not MIN_CONFIDENCE <= conf <= MAX_CONFIDENCE:
            raise HTTPException(422, f"confidence must be between {MIN_CONFIDENCE} and {MAX_CONFIDENCE}")
        if image.content_type and image.content_type not in ALLOWED_TYPES:
            raise HTTPException(415, "Upload a JPEG, PNG, WebP or BMP image")

        limit = settings.max_upload_mb * 1024 * 1024
        data = await image.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"Image is larger than {settings.max_upload_mb} MB")
        if not data:
            raise HTTPException(400, "The uploaded file is empty")

        try:
            pil = Image.open(io.BytesIO(data))
            pil.load()
            # Phone photos are often stored sideways with an EXIF rotation flag;
            # apply it so the boxes match the picture people see.
            pil = ImageOps.exif_transpose(pil).convert("RGB")
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
            raise HTTPException(
                400, "The file is not a readable image (iPhone HEIC photos: save as JPEG first)"
            )

        if not detector.available:
            try:
                if isinstance(detector, YoloDetector):
                    detector.load()
            except ModelUnavailable:
                pass
        if not detector.available:
            raise HTTPException(503, detector.status.get("error") or "The damage model is not loaded")

        raw = await run_in_threadpool(detector.detect, pil, conf)
        width, height = pil.size
        names = labels()
        detections = assessment.build_detections(raw, width, height, names)
        summary = assessment.summarise(detections, names)

        analysis_id = uuid.uuid4().hex
        image_file = f"{analysis_id}.jpg"
        # Saved without EXIF metadata (no GPS location kept).
        pil.save(settings.upload_dir / image_file, format="JPEG", quality=90)

        analysis = {
            "id": analysis_id,
            "created_at": utc_now(),
            "image_name": Path(image.filename or "upload").name[:200],
            "image_file": image_file,
            "image_width": width,
            "image_height": height,
            "confidence_threshold": conf,
            "model_name": detector.name,
            "detections": detections,
            "summary": summary,
        }
        db.save_analysis(analysis)
        return analysis_response(analysis)

    def _load_analysis(analysis_id: str) -> dict:
        analysis = db.get_analysis(analysis_id)
        if analysis is None:
            raise HTTPException(404, "Analysis not found")
        return analysis

    @app.get("/api/analyses/{analysis_id}")
    def get_analysis(analysis_id: str) -> dict:
        return analysis_response(_load_analysis(analysis_id))

    @app.get("/api/analyses/{analysis_id}/image")
    def get_analysis_image(analysis_id: str) -> FileResponse:
        analysis = _load_analysis(analysis_id)
        path = settings.upload_dir / analysis["image_file"]
        if not path.is_file():
            raise HTTPException(404, "Image file is missing")
        return FileResponse(path, media_type="image/jpeg")

    # -------------------------------------------------------------- reports
    @app.post("/api/reports", status_code=201)
    def create_report(body: ReportRequest) -> dict:
        analysis = _load_analysis(body.analysis_id)
        try:
            report = build_report(analysis, body, db)
        except ReportError as exc:
            raise HTTPException(422, str(exc))
        db.save_report(report)
        return report

    @app.get("/api/reports")
    def list_reports(limit: int = 50) -> list[dict]:
        return db.list_reports(max(1, min(limit, 200)))

    @app.get("/api/reports/{report_id}")
    def get_report(report_id: str) -> dict:
        report = db.get_report(report_id)
        if report is None:
            raise HTTPException(404, "Report not found")
        return report

    @app.exception_handler(ModelUnavailable)
    async def _model_unavailable(_: Request, exc: ModelUnavailable) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    # Serve the built React app (frontend/dist) on the same port, if present.
    if settings.frontend_dist.is_dir() and (settings.frontend_dist / "index.html").is_file():
        app.mount("/", StaticFiles(directory=settings.frontend_dist, html=True), name="frontend")

    return app


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
app = create_app()
