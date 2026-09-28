"""Depot REST endpoints: CRUD for demo workflows + the assets their runs produce.

See docs/DEPOT_WORKFLOW_PLAN.md. Wired the same way apps_routes.py is:

    from .services.depot_routes import register_depot_routes
    register_depot_routes(router, call_tool)

`call_tool` is an async `(tool_name, params) -> {success, data, error}` callable -
app.py passes its existing `_call_mcp_tool` bound to the live `mcp` instance, so
workflow execution reuses the one place that already understands FastMCP's
ToolResult shapes instead of a second implementation here.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import depot_store

logger = logging.getLogger("depot_routes")

CallTool = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


def _tool_ok(result: dict[str, Any]) -> bool:
    """Every tool in this repo returns its own {success, ...} dict as `data` -
    a transport-level success from _call_mcp_tool does not mean the operation
    itself succeeded (e.g. render_preview can fail with success=True at the
    transport level while data.success is False). Prefer the inner flag.
    """
    data = result.get("data")
    if isinstance(data, dict) and "success" in data:
        return bool(data["success"])
    return bool(result.get("success"))


def _tool_error(result: dict[str, Any]) -> str:
    data = result.get("data")
    if isinstance(data, dict) and data.get("message"):
        return str(data["message"])
    return str(result.get("error") or "unknown error")


class StepIn(BaseModel):
    tool: str
    operation: str
    params: dict[str, Any] = {}


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    steps: list[StepIn]


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    steps: list[StepIn] | None = None


class AssetUpdate(BaseModel):
    name: str | None = None
    tags: list[str] | None = None


def register_depot_routes(router: APIRouter, call_tool: CallTool) -> None:
    depot_store.init_db()

    @router.get("/depot/workflows")
    async def list_workflows() -> list[dict[str, Any]]:
        return depot_store.list_workflows()

    @router.post("/depot/workflows")
    async def create_workflow(body: WorkflowCreate) -> dict[str, Any]:
        return depot_store.create_workflow(
            body.name, body.description, [s.model_dump() for s in body.steps]
        )

    @router.get("/depot/workflows/{workflow_id}")
    async def get_workflow(workflow_id: str) -> dict[str, Any]:
        wf = depot_store.get_workflow(workflow_id)
        if wf is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return wf

    @router.put("/depot/workflows/{workflow_id}")
    async def update_workflow(workflow_id: str, body: WorkflowUpdate) -> dict[str, Any]:
        try:
            steps = [s.model_dump() for s in body.steps] if body.steps is not None else None
            wf = depot_store.update_workflow(workflow_id, body.name, body.description, steps)
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e)) from e
        if wf is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return wf

    @router.delete("/depot/workflows/{workflow_id}")
    async def delete_workflow(workflow_id: str) -> dict[str, bool]:
        try:
            ok = depot_store.delete_workflow(workflow_id)
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e)) from e
        if not ok:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return {"success": True}

    @router.post("/depot/workflows/{workflow_id}/run")
    async def run_workflow(workflow_id: str) -> dict[str, Any]:
        wf = depot_store.get_workflow(workflow_id)
        if wf is None:
            raise HTTPException(status_code=404, detail="Workflow not found")

        run_id = f"{int(time.time() * 1000)}"
        svg_path = str(depot_store.ASSETS_DIR / f"{workflow_id}_{run_id}.svg")
        thumb_path = str(depot_store.ASSETS_DIR / f"{workflow_id}_{run_id}.png")

        step_results = []
        current_path = ""
        for i, step in enumerate(wf["steps"]):
            params = dict(step.get("params") or {})
            # Chain output_path -> input_path across steps; the last step writes
            # to the run's final svg_path so every workflow produces exactly one asset.
            is_last = i == len(wf["steps"]) - 1
            if current_path and "input_path" not in params:
                params["input_path"] = current_path
            params["output_path"] = svg_path if is_last else params.get("output_path", svg_path)
            result = await call_tool(step["tool"], {"operation": step["operation"], **params})
            step_results.append({"tool": step["tool"], "operation": step["operation"], "result": result})
            if not _tool_ok(result):
                return {
                    "success": False,
                    "error": f"Step {i} ({step['tool']}.{step['operation']}) failed: {_tool_error(result)}",
                    "step_results": step_results,
                }
            current_path = svg_path

        if not Path(svg_path).exists():
            return {
                "success": False,
                "error": "Workflow completed but produced no output file",
                "step_results": step_results,
            }

        thumb_result = await call_tool(
            "inkscape_render",
            {"operation": "export_preview", "input_path": svg_path, "output_path": thumb_path, "dpi": 96},
        )
        thumbnail_path = thumb_path if _tool_ok(thumb_result) and Path(thumb_path).exists() else None

        asset = depot_store.create_asset(
            name=f"{wf['name']} ({run_id})",
            file_path=svg_path,
            thumbnail_path=thumbnail_path,
            workflow_id=workflow_id,
        )
        return {"success": True, "asset": asset, "step_results": step_results}

    @router.get("/depot/assets")
    async def list_assets(workflow_id: str = "") -> list[dict[str, Any]]:
        return depot_store.list_assets(workflow_id or None)

    @router.get("/depot/assets/{asset_id}")
    async def get_asset(asset_id: str) -> dict[str, Any]:
        asset = depot_store.get_asset(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset

    @router.patch("/depot/assets/{asset_id}")
    async def update_asset(asset_id: str, body: AssetUpdate) -> dict[str, Any]:
        asset = depot_store.update_asset(asset_id, body.name, body.tags)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset

    @router.delete("/depot/assets/{asset_id}")
    async def delete_asset(asset_id: str) -> dict[str, bool]:
        ok = depot_store.delete_asset(asset_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Asset not found")
        return {"success": True}

    @router.get("/depot/assets/{asset_id}/file")
    async def get_asset_file(asset_id: str) -> FileResponse:
        asset = depot_store.get_asset(asset_id)
        if asset is None or not Path(asset["file_path"]).exists():
            raise HTTPException(status_code=404, detail="Asset file not found")
        return FileResponse(asset["file_path"], media_type="image/svg+xml")

    @router.get("/depot/assets/{asset_id}/thumbnail")
    async def get_asset_thumbnail(asset_id: str) -> FileResponse:
        asset = depot_store.get_asset(asset_id)
        if asset is None or not asset["thumbnail_path"] or not Path(asset["thumbnail_path"]).exists():
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        return FileResponse(asset["thumbnail_path"], media_type="image/png")
