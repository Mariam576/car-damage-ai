"""SQLite storage: the UK repair-cost reference data, analyses and reports.

Uses the standard-library ``sqlite3`` module. A short-lived connection is
opened per operation, which is cheap for SQLite and safe across the
threads FastAPI uses for synchronous endpoints.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from . import seed_data

SCHEMA = """
CREATE TABLE IF NOT EXISTS damage_classes (
    name           TEXT PRIMARY KEY,
    label          TEXT NOT NULL,
    safety_related INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sources (
    id           INTEGER PRIMARY KEY,
    key          TEXT NOT NULL UNIQUE,
    publisher    TEXT NOT NULL,
    title        TEXT NOT NULL,
    url          TEXT NOT NULL,
    published    TEXT,
    updated      TEXT,
    retrieved_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repair_methods (
    id          INTEGER PRIMARY KEY,
    damage_type TEXT NOT NULL REFERENCES damage_classes(name),
    method      TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    min_gbp     REAL NOT NULL,
    max_gbp     REAL NOT NULL,
    max_open    INTEGER NOT NULL DEFAULT 0,
    unit        TEXT NOT NULL,
    source_id   INTEGER NOT NULL REFERENCES sources(id),
    source_note TEXT NOT NULL DEFAULT '',
    sort_order  INTEGER NOT NULL DEFAULT 0,
    UNIQUE (damage_type, method),
    CHECK (min_gbp >= 0 AND max_gbp >= min_gbp)
);

CREATE TABLE IF NOT EXISTS analyses (
    id                   TEXT PRIMARY KEY,
    created_at           TEXT NOT NULL,
    image_name           TEXT NOT NULL,
    image_file           TEXT NOT NULL,
    image_width          INTEGER NOT NULL,
    image_height         INTEGER NOT NULL,
    confidence_threshold REAL NOT NULL,
    model_name           TEXT NOT NULL,
    detections_json      TEXT NOT NULL,
    summary_json         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id          TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL REFERENCES analyses(id),
    created_at  TEXT NOT NULL,
    total_min   REAL NOT NULL,
    total_max   REAL NOT NULL,
    report_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_methods_damage ON repair_methods(damage_type, sort_order);
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at);
"""

METHOD_QUERY = """
SELECT m.id, m.damage_type, m.method, m.description, m.min_gbp, m.max_gbp,
       m.max_open, m.unit, m.source_note, m.sort_order,
       s.publisher, s.title AS source_title, s.url AS source_url,
       s.published AS source_published, s.updated AS source_updated,
       s.retrieved_on AS source_retrieved_on
FROM repair_methods m
JOIN sources s ON s.id = m.source_id
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)

    # -- connection ---------------------------------------------------------
    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # -- schema and reference data -------------------------------------------
    def init(self) -> None:
        """Create tables, and load the reference data if the tables are empty."""
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            empty = conn.execute("SELECT COUNT(*) FROM repair_methods").fetchone()[0] == 0
        if empty:
            self.seed(reset=False)

    def seed(self, reset: bool = False) -> None:
        """Load damage classes, sources and repair methods from seed_data.

        reset=True replaces the reference tables (saved analyses and reports
        keep their own copy of the prices, so they are unaffected).
        """
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            if reset:
                conn.execute("DELETE FROM repair_methods")
                conn.execute("DELETE FROM sources")
                conn.execute("DELETE FROM damage_classes")
            for c in seed_data.DAMAGE_CLASSES:
                conn.execute(
                    "INSERT OR REPLACE INTO damage_classes(name, label, safety_related) VALUES (?, ?, ?)",
                    (c["name"], c["label"], int(c["safety_related"])),
                )
            source_ids: dict[str, int] = {}
            for s in seed_data.SOURCES:
                conn.execute(
                    """INSERT INTO sources(key, publisher, title, url, published, updated, retrieved_on)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(key) DO UPDATE SET publisher=excluded.publisher,
                         title=excluded.title, url=excluded.url, published=excluded.published,
                         updated=excluded.updated, retrieved_on=excluded.retrieved_on""",
                    (s["key"], s["publisher"], s["title"], s["url"], s["published"],
                     s["updated"], seed_data.RETRIEVED_ON),
                )
                source_ids[s["key"]] = conn.execute(
                    "SELECT id FROM sources WHERE key = ?", (s["key"],)
                ).fetchone()[0]
            for order, m in enumerate(seed_data.REPAIR_METHODS):
                conn.execute(
                    """INSERT INTO repair_methods(damage_type, method, description, min_gbp, max_gbp,
                         max_open, unit, source_id, source_note, sort_order)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(damage_type, method) DO UPDATE SET
                         description=excluded.description, min_gbp=excluded.min_gbp,
                         max_gbp=excluded.max_gbp, max_open=excluded.max_open, unit=excluded.unit,
                         source_id=excluded.source_id, source_note=excluded.source_note,
                         sort_order=excluded.sort_order""",
                    (m["damage_type"], m["method"], m["description"], m["min_gbp"], m["max_gbp"],
                     int(m["max_open"]), m["unit"], source_ids[m["source"]], m["source_note"], order),
                )

    # -- reference queries -----------------------------------------------------
    def damage_classes(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT name, label, safety_related FROM damage_classes ORDER BY rowid"
            ).fetchall()
        return [
            {"name": r["name"], "label": r["label"], "safety_related": bool(r["safety_related"])}
            for r in rows
        ]

    def repair_methods(self, damage_type: str | None = None) -> list[dict]:
        sql = METHOD_QUERY
        params: tuple = ()
        if damage_type is not None:
            sql += " WHERE m.damage_type = ?"
            params = (damage_type,)
        sql += " ORDER BY m.sort_order, m.id"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_method_row(r) for r in rows]

    def repair_method(self, method_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(METHOD_QUERY + " WHERE m.id = ?", (method_id,)).fetchone()
        return _method_row(row) if row else None

    def sources(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT key, publisher, title, url, published, updated, retrieved_on FROM sources ORDER BY id"
            ).fetchall()
        return [dict(r) for r in rows]

    # -- analyses ----------------------------------------------------------------
    def save_analysis(self, analysis: dict) -> None:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO analyses(id, created_at, image_name, image_file, image_width, image_height,
                     confidence_threshold, model_name, detections_json, summary_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    analysis["id"], analysis["created_at"], analysis["image_name"],
                    analysis["image_file"], analysis["image_width"], analysis["image_height"],
                    analysis["confidence_threshold"], analysis["model_name"],
                    json.dumps(analysis["detections"]), json.dumps(analysis["summary"]),
                ),
            )

    def get_analysis(self, analysis_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "image_name": row["image_name"],
            "image_file": row["image_file"],
            "image_width": row["image_width"],
            "image_height": row["image_height"],
            "confidence_threshold": row["confidence_threshold"],
            "model_name": row["model_name"],
            "detections": json.loads(row["detections_json"]),
            "summary": json.loads(row["summary_json"]),
        }

    # -- reports -------------------------------------------------------------------
    def save_report(self, report: dict) -> None:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO reports(id, analysis_id, created_at, total_min, total_max, report_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    report["id"], report["analysis_id"], report["created_at"],
                    report["totals"]["min_gbp"], report["totals"]["max_gbp"], json.dumps(report),
                ),
            )

    def get_report(self, report_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT report_json FROM reports WHERE id = ?", (report_id,)).fetchone()
        return json.loads(row["report_json"]) if row else None

    def list_reports(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT r.id, r.analysis_id, r.created_at, r.total_min, r.total_max, r.report_json,
                          a.image_name
                   FROM reports r JOIN analyses a ON a.id = r.analysis_id
                   ORDER BY r.created_at DESC, r.rowid DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        out = []
        for r in rows:
            report = json.loads(r["report_json"])
            out.append(
                {
                    "id": r["id"],
                    "analysis_id": r["analysis_id"],
                    "created_at": r["created_at"],
                    "image_name": r["image_name"],
                    "total_min_gbp": r["total_min"],
                    "total_max_gbp": r["total_max"],
                    "max_open": report["totals"]["max_open"],
                    "damage_types": sorted({line["damage_type"] for line in report["lines"]}),
                    "inspection_priority": report["inspection_priority"],
                }
            )
        return out


def _method_row(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "damage_type": r["damage_type"],
        "method": r["method"],
        "description": r["description"],
        "min_gbp": r["min_gbp"],
        "max_gbp": r["max_gbp"],
        "max_open": bool(r["max_open"]),
        "unit": r["unit"],
        "source": {
            "publisher": r["publisher"],
            "title": r["source_title"],
            "url": r["source_url"],
            "published": r["source_published"],
            "updated": r["source_updated"],
            "retrieved_on": r["source_retrieved_on"],
            "note": r["source_note"],
        },
    }
