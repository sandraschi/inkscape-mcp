"""Agent vision render operations for Inkscape MCP (Phase 1)."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from .analysis import inkscape_analysis
from .vector_operations import _render_preview

logger = logging.getLogger(__name__)

RenderOperation = Literal["export_preview", "export_multi_dpi", "get_document_summary"]

DEFAULT_PREVIEW_DPIS = (96, 192, 384)


class RenderResult(BaseModel):
    """Result model for render operations."""

    success: bool
    operation: str
    message: str
    data: dict[str, Any]
    execution_time_ms: float
    error: str = ""


def _parse_dpi_list(raw: str) -> list[int]:
    if not raw.strip():
        return list(DEFAULT_PREVIEW_DPIS)
    values: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        dpi = int(part)
        if dpi < 36 or dpi > 1200:
            raise ValueError(f"DPI out of range (36-1200): {dpi}")
        values.append(dpi)
    if not values:
        raise ValueError("dpi_list must contain at least one integer")
    return values


def _default_preview_path(input_path: str, dpi: int, config: Any) -> str:
    stem = Path(input_path).stem or "preview"
    temp_dir = Path(getattr(config, "temp_directory", Path.cwd()))
    temp_dir.mkdir(parents=True, exist_ok=True)
    return str(temp_dir / f"{stem}_preview_{dpi}dpi.png")


async def inkscape_render(
    operation: RenderOperation,
    input_path: str = "",
    output_path: str = "",
    dpi: int = 96,
    dpi_list: str = "",
    cli_wrapper: Any = None,
    config: Any = None,
) -> dict[str, Any]:
    """Inkscape agent vision render portmanteau tool."""
    start_time = time.time()

    try:
        if operation == "export_preview":
            if not input_path:
                return RenderResult(
                    success=False,
                    operation=operation,
                    message="input_path is required for export_preview",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="ValueError",
                ).model_dump()

            input_obj = Path(input_path)
            if not input_obj.exists():
                return RenderResult(
                    success=False,
                    operation=operation,
                    message=f"File not found: {input_path}",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="FileNotFoundError",
                ).model_dump()

            if cli_wrapper is None or config is None:
                return RenderResult(
                    success=False,
                    operation=operation,
                    message="Inkscape CLI wrapper is not initialized",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="RuntimeError",
                ).model_dump()

            target_dpi = max(36, min(int(dpi), 1200))
            target_output = output_path or _default_preview_path(input_path, target_dpi, config)
            result = await _render_preview(
                str(input_obj),
                target_output,
                target_dpi,
                cli_wrapper,
                config,
            )
            if result.get("success"):
                result["operation"] = "export_preview"
                result["message"] = (
                    f"Agent preview exported at {target_dpi} DPI. "
                    "Use in vision loops or fleet handoff to gimp-mcp."
                )
                result.setdefault("data", {})["agent_vision"] = True
            return result

        if operation == "export_multi_dpi":
            if not input_path:
                return RenderResult(
                    success=False,
                    operation=operation,
                    message="input_path is required for export_multi_dpi",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="ValueError",
                ).model_dump()

            if cli_wrapper is None or config is None:
                return RenderResult(
                    success=False,
                    operation=operation,
                    message="Inkscape CLI wrapper is not initialized",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="RuntimeError",
                ).model_dump()

            try:
                dpis = _parse_dpi_list(dpi_list)
            except ValueError as exc:
                return RenderResult(
                    success=False,
                    operation=operation,
                    message=str(exc),
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="ValueError",
                ).model_dump()

            exports: list[dict[str, Any]] = []
            for item_dpi in dpis:
                out_path = output_path
                if not out_path:
                    out_path = _default_preview_path(input_path, item_dpi, config)
                elif len(dpis) > 1:
                    stem = Path(out_path).stem
                    suffix = Path(out_path).suffix or ".png"
                    parent = Path(out_path).parent
                    out_path = str(parent / f"{stem}_{item_dpi}dpi{suffix}")

                item_result = await _render_preview(
                    input_path,
                    out_path,
                    item_dpi,
                    cli_wrapper,
                    config,
                )
                exports.append(
                    {
                        "dpi": item_dpi,
                        "output_path": out_path,
                        "success": item_result.get("success", False),
                        "message": item_result.get("message", ""),
                    }
                )

            all_ok = all(item["success"] for item in exports)
            return RenderResult(
                success=all_ok,
                operation=operation,
                message=(
                    f"Exported {sum(1 for e in exports if e['success'])}/{len(exports)} "
                    f"preview(s) for agent vision."
                ),
                data={"input_path": input_path, "exports": exports, "agent_vision": True},
                execution_time_ms=(time.time() - start_time) * 1000,
                error="" if all_ok else "PartialExportError",
            ).model_dump()

        if operation == "get_document_summary":
            if not input_path:
                return RenderResult(
                    success=False,
                    operation=operation,
                    message="input_path is required for get_document_summary",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="ValueError",
                ).model_dump()

            input_obj = Path(input_path)
            if not input_obj.exists():
                return RenderResult(
                    success=False,
                    operation=operation,
                    message=f"File not found: {input_path}",
                    data={},
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="FileNotFoundError",
                ).model_dump()

            stats = await inkscape_analysis(
                operation="statistics",
                input_path=input_path,
                cli_wrapper=cli_wrapper,
                config=config,
            )
            validation = await inkscape_analysis(
                operation="validate",
                input_path=input_path,
                cli_wrapper=cli_wrapper,
                config=config,
            )

            summary = {
                "path": str(input_obj.resolve()),
                "file_size_bytes": input_obj.stat().st_size,
                "statistics": stats.get("data", {}),
                "valid": validation.get("success", False),
                "validation": validation.get("data", {}),
                "recommended_next": [
                    "inkscape_render operation=export_preview for agent vision",
                    "inkscape_analysis operation=objects before ID-based edits",
                    "inkscape_system operation=execution_mode for Hands-In vs batch",
                ],
            }

            return RenderResult(
                success=stats.get("success", False),
                operation=operation,
                message=f"Document summary ready for {input_path}",
                data=summary,
                execution_time_ms=(time.time() - start_time) * 1000,
                error="" if stats.get("success") else stats.get("error", "AnalysisError"),
            ).model_dump()

        return RenderResult(
            success=False,
            operation=operation,
            message=f"Unknown operation: {operation}",
            data={},
            execution_time_ms=(time.time() - start_time) * 1000,
            error="ValueError",
        ).model_dump()

    except Exception as exc:
        logger.exception("inkscape_render failed for operation=%s", operation)
        return RenderResult(
            success=False,
            operation=operation,
            message=f"Render operation failed: {exc}",
            data={},
            execution_time_ms=(time.time() - start_time) * 1000,
            error=str(exc),
        ).model_dump()
