"""SQLite-backed store for the webapp's Depot page (demo workflows + generated assets).

See docs/DEPOT_WORKFLOW_PLAN.md for the design. Schema/CRUD only - execution
(calling MCP tools for a workflow's steps) lives in depot_routes.py, which is
the one place that needs the live `mcp` instance.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger("depot_store")

DEPOT_DIR = Path.home() / ".config" / "inkscape-mcp" / "depot"
ASSETS_DIR = DEPOT_DIR / "assets"
DB_PATH = DEPOT_DIR / "depot.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    steps TEXT NOT NULL,
    is_builtin INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    workflow_id TEXT,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    thumbnail_path TEXT,
    tags TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
"""

_BUILTIN_WORKFLOWS: list[dict[str, Any]] = [
    {
        "name": "Bouncing circle",
        "description": "Create a filled circle, then apply the bounce SMIL animation preset.",
        "steps": [
            {
                "tool": "inkscape_vector",
                "operation": "create_object",
                "params": {"shape": "circle", "params": {"cx": 100, "cy": 100, "r": 40, "fill": "#4488ff"}},
            },
            {
                "tool": "inkscape_animation",
                "operation": "apply_preset",
                "params": {"preset_name": "bounce", "shape": "circle", "fill": "#4488ff"},
            },
        ],
    },
    {
        "name": "Layer rename + hide",
        "description": "Create a base shape, add a layer, rename it, then hide it.",
        "steps": [
            {
                "tool": "inkscape_vector",
                "operation": "create_object",
                "params": {"shape": "rect", "params": {"x": 0, "y": 0, "width": 100, "height": 100, "fill": "#888"}},
            },
            {"tool": "inkscape_layers", "operation": "create", "params": {"label": "Draft"}},
            {"tool": "inkscape_layers", "operation": "rename", "params": {"layer_id": "layer1", "new_label": "Background"}},
            {"tool": "inkscape_layers", "operation": "hide", "params": {"layer_id": "layer1"}},
        ],
    },
    {
        "name": "Text to roughened path",
        "description": "Create text, convert to a path, then apply the roughen Live Path Effect.",
        "steps": [
            {
                "tool": "inkscape_vector",
                "operation": "create_object",
                "params": {
                    "shape": "text",
                    "params": {"content": "Inkscape MCP", "x": 20, "y": 60, "font_size": 32, "fill": "#222222"},
                },
            },
            {"tool": "inkscape_vector", "operation": "text_to_path", "params": {}},
            {"tool": "inkscape_vector", "operation": "apply_lpe", "params": {"lpe_id": "roughen"}},
        ],
    },
]


def _connect() -> sqlite3.Connection:
    DEPOT_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if missing and seed builtin workflows once."""
    with _connect() as conn:
        conn.executescript(_SCHEMA)
        existing = conn.execute("SELECT COUNT(*) AS n FROM workflows WHERE is_builtin = 1").fetchone()
        if existing["n"] == 0:
            now = _now()
            for wf in _BUILTIN_WORKFLOWS:
                conn.execute(
                    "INSERT INTO workflows (id, name, description, steps, is_builtin, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, 1, ?, ?)",
                    (str(uuid.uuid4()), wf["name"], wf["description"], json.dumps(wf["steps"]), now, now),
                )
            conn.commit()
            logger.info("Seeded %d builtin depot workflows", len(_BUILTIN_WORKFLOWS))


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _row_to_workflow(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "steps": json.loads(row["steps"]),
        "is_builtin": bool(row["is_builtin"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _row_to_asset(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "workflow_id": row["workflow_id"],
        "name": row["name"],
        "file_path": row["file_path"],
        "thumbnail_path": row["thumbnail_path"],
        "tags": [t for t in row["tags"].split(",") if t],
        "created_at": row["created_at"],
    }


# ── Workflows ──────────────────────────────────────────────────────────────


def list_workflows() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM workflows ORDER BY created_at DESC").fetchall()
        return [_row_to_workflow(r) for r in rows]


def get_workflow(workflow_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        return _row_to_workflow(row) if row else None


def create_workflow(name: str, description: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    workflow_id = str(uuid.uuid4())
    now = _now()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO workflows (id, name, description, steps, is_builtin, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 0, ?, ?)",
            (workflow_id, name, description, json.dumps(steps), now, now),
        )
        conn.commit()
    return get_workflow(workflow_id)  # type: ignore[return-value]


def update_workflow(
    workflow_id: str, name: str | None, description: str | None, steps: list[dict[str, Any]] | None
) -> dict[str, Any] | None:
    existing = get_workflow(workflow_id)
    if existing is None:
        return None
    if existing["is_builtin"]:
        raise ValueError("Builtin workflows are read-only - use 'save as' to create an editable copy")
    with _connect() as conn:
        conn.execute(
            "UPDATE workflows SET name = ?, description = ?, steps = ?, updated_at = ? WHERE id = ?",
            (
                name if name is not None else existing["name"],
                description if description is not None else existing["description"],
                json.dumps(steps) if steps is not None else json.dumps(existing["steps"]),
                _now(),
                workflow_id,
            ),
        )
        conn.commit()
    return get_workflow(workflow_id)


def delete_workflow(workflow_id: str) -> bool:
    existing = get_workflow(workflow_id)
    if existing is None:
        return False
    if existing["is_builtin"]:
        raise ValueError("Builtin workflows cannot be deleted")
    with _connect() as conn:
        conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
        conn.commit()
    return True


# ── Assets ─────────────────────────────────────────────────────────────────


def list_assets(workflow_id: str | None = None) -> list[dict[str, Any]]:
    with _connect() as conn:
        if workflow_id:
            rows = conn.execute(
                "SELECT * FROM assets WHERE workflow_id = ? ORDER BY created_at DESC", (workflow_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM assets ORDER BY created_at DESC").fetchall()
        return [_row_to_asset(r) for r in rows]


def get_asset(asset_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        return _row_to_asset(row) if row else None


def create_asset(
    name: str,
    file_path: str,
    thumbnail_path: str | None,
    workflow_id: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    asset_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO assets (id, workflow_id, name, file_path, thumbnail_path, tags, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (asset_id, workflow_id, name, file_path, thumbnail_path, ",".join(tags or []), _now()),
        )
        conn.commit()
    return get_asset(asset_id)  # type: ignore[return-value]


def update_asset(asset_id: str, name: str | None, tags: list[str] | None) -> dict[str, Any] | None:
    existing = get_asset(asset_id)
    if existing is None:
        return None
    with _connect() as conn:
        conn.execute(
            "UPDATE assets SET name = ?, tags = ? WHERE id = ?",
            (
                name if name is not None else existing["name"],
                ",".join(tags) if tags is not None else ",".join(existing["tags"]),
                asset_id,
            ),
        )
        conn.commit()
    return get_asset(asset_id)


def delete_asset(asset_id: str) -> bool:
    existing = get_asset(asset_id)
    if existing is None:
        return False
    for path_str in (existing["file_path"], existing["thumbnail_path"]):
        if path_str:
            try:
                Path(path_str).unlink(missing_ok=True)
            except OSError:
                logger.warning("Could not delete asset file %s", path_str)
    with _connect() as conn:
        conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        conn.commit()
    return True
