"""UI vector / sim-art portmanteau (icon packs, sheets, Resonite handoff)."""

from __future__ import annotations

import json
import logging
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from ..utils.ai_svg_handoff import build_ai_svg_handoff
from ..utils.fleet_handoff import push_raster_to_gimp
from ..utils.fleet_staging import stage_file
from ..utils.svg_pack_audit import audit_svg_pack_directory
from ..utils.svg_pack_presets import ATLAS_LAYOUTS
from ..utils.svg_pack_presets import DEFAULT_SIM_STAGING
from ..utils.svg_pack_presets import detect_svg_icons
from ..utils.svg_pack_presets import list_svg_pack_presets
from ..utils.svg_pack_presets import resolve_icon_template
from ..utils.svg_pack_presets import validate_svg_pack_layout
from .render_tools import inkscape_render

logger = logging.getLogger(__name__)

SimArtOperation = Literal[
    "list_presets",
    "svg_pack_batch",
    "build_icon_sheet",
    "audit_svg_pack",
    "ai_svg_refine_loop",
    "push_gimp_texture_sheet",
    "stage_resonite_ui",
    "run_sim_pipeline",
]

SVG_NS = "http://www.w3.org/2000/svg"


class SimArtResult(BaseModel):
    success: bool
    operation: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    files: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    error: str = ""


def _iter_svgs(input_dir: Path) -> list[Path]:
    return sorted({p.resolve() for p in input_dir.glob("*.svg") if p.is_file()})


def _normalize_svg_to_template(src: Path, dest: Path, template: dict[str, Any]) -> None:
    tree = ET.parse(src)
    root = tree.getroot()
    if not (root.tag.endswith("svg") or root.tag == "svg"):
        raise ValueError(f"Not an SVG root: {src}")

    if root.tag.startswith("{"):
        root.tag = "svg"

    width = int(template["width"])
    height = int(template["height"])
    view_box = str(template["view_box"])

    root.set("width", str(width))
    root.set("height", str(height))
    root.set("viewBox", view_box)
    if "xmlns" not in root.attrib:
        root.set("xmlns", SVG_NS)

    dest.parent.mkdir(parents=True, exist_ok=True)
    tree.write(dest, encoding="utf-8", xml_declaration=True)


async def _svg_pack_batch(
    *,
    input_dir: Path,
    output_dir: Path,
    template_id: str,
    validate: bool,
) -> dict[str, Any]:
    template = resolve_icon_template(template_id)
    if template is None:
        return {"success": False, "error": f"Unknown template: {template_id}"}
    if not input_dir.is_dir():
        return {"success": False, "error": f"Input directory not found: {input_dir}"}

    icons = detect_svg_icons(input_dir)
    layout_issues = validate_svg_pack_layout(icons)
    if layout_issues:
        return {"success": False, "error": "; ".join(layout_issues), "layout_issues": layout_issues}

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []
    failures: list[dict[str, str]] = []

    for stem, src in icons.items():
        dest = output_dir / f"{stem}_{template_id}.svg"
        try:
            _normalize_svg_to_template(src, dest, template)
            outputs.append(str(dest))
            if validate:
                from .validation_tools import inkscape_validation

                audit = await inkscape_validation("audit_web_svg", str(dest))
                passed = bool(audit.get("success"))
                if not passed:
                    failures.append({"path": str(dest), "issues": str(audit.get("issues", []))})
        except Exception as exc:
            logger.exception("SVG pack batch failed for %s", src)
            failures.append({"path": str(src), "issues": str(exc)})

    if not outputs:
        return {"success": False, "error": "No SVG icons processed", "failures": failures}

    return {
        "success": len(failures) == 0,
        "template_id": template_id,
        "output_dir": str(output_dir),
        "files": outputs,
        "count": len(outputs),
        "failures": failures,
    }


async def _build_icon_sheet(
    *,
    input_dir: Path,
    output_path: Path,
    layout: str,
    cell_size: int,
    margin_px: int = 0,
    bleed_px: int = 0,
) -> dict[str, Any]:
    if layout not in ATLAS_LAYOUTS:
        return {"success": False, "error": f"Unknown layout: {layout}"}

    cols, rows = ATLAS_LAYOUTS[layout]
    sources = _iter_svgs(input_dir)
    max_cells = cols * rows
    if not sources:
        return {"success": False, "error": f"No SVG files in {input_dir}"}
    if len(sources) > max_cells:
        sources = sources[:max_cells]

    margin_px = max(0, margin_px)
    bleed_px = max(0, bleed_px)
    stride = cell_size + margin_px
    sheet_w = cols * stride - margin_px
    sheet_h = rows * stride - margin_px

    root = ET.Element("svg", attrib={"xmlns": SVG_NS, "viewBox": f"0 0 {sheet_w} {sheet_h}"})
    root.set("width", str(sheet_w))
    root.set("height", str(sheet_h))
    manifest_entries: list[dict[str, Any]] = []

    for index, src in enumerate(sources):
        col = index % cols
        row = index // cols
        x = col * stride
        y = row * stride
        inner = max(1, cell_size - bleed_px * 2)
        nested = ET.SubElement(
            root,
            "svg",
            attrib={
                "x": str(x + bleed_px),
                "y": str(y + bleed_px),
                "width": str(inner),
                "height": str(inner),
                "viewBox": f"0 0 {inner} {inner}",
            },
        )
        nested.set("data-source", src.name)
        try:
            child_tree = ET.parse(src)
            child_root = child_tree.getroot()
            source_viewbox = child_root.get("viewBox") or child_root.get("viewbox") or f"0 0 {inner} {inner}"
            nested.set("viewBox", source_viewbox)
            for child in list(child_root):
                nested.append(child)
        except ET.ParseError as exc:
            return {"success": False, "error": f"Invalid SVG {src}: {exc}"}

        content_u0 = (x + bleed_px) / sheet_w if sheet_w else 0.0
        content_v0 = (y + bleed_px) / sheet_h if sheet_h else 0.0
        content_u1 = (x + cell_size - bleed_px) / sheet_w if sheet_w else 1.0
        content_v1 = (y + cell_size - bleed_px) / sheet_h if sheet_h else 1.0
        manifest_entries.append(
            {
                "source": str(src),
                "name": src.stem,
                "cell_index": index,
                "column": col,
                "row": row,
                "margin_px": margin_px,
                "bleed_px": bleed_px,
                "cell_size": cell_size,
                "pixel_rect": {"x": x, "y": y, "w": cell_size, "h": cell_size},
                "uv": {
                    "u0": round(content_u0, 6),
                    "v0": round(content_v0, 6),
                    "u1": round(content_u1, 6),
                    "v1": round(content_v1, 6),
                },
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    manifest_path = output_path.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(
            {
                "layout": layout,
                "cell_size": cell_size,
                "margin_px": margin_px,
                "bleed_px": bleed_px,
                "sheet_size": {"width": sheet_w, "height": sheet_h},
                "entries": manifest_entries,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "success": True,
        "output_path": str(output_path),
        "manifest_path": str(manifest_path),
        "layout": layout,
        "margin_px": margin_px,
        "bleed_px": bleed_px,
        "cell_count": len(manifest_entries),
        "entries": manifest_entries,
    }


async def _audit_svg_pack_dir(input_dir: Path) -> dict[str, Any]:
    return await audit_svg_pack_directory(input_dir)


async def inkscape_sim_art(
    operation: SimArtOperation,
    *,
    input_dir: str = "",
    output_dir: str = "",
    output_path: str = "",
    template_id: str = "ui_icon_128",
    layout: str = "2x2",
    cell_size: int = 128,
    margin_px: int = 0,
    bleed_px: int = 0,
    staging_dir: str = "",
    gimp_url: str = "",
    target_platform: str = "unity",
    validate: bool = True,
    goal: str = "",
    dpi: int = 192,
    cli_wrapper: Any = None,
    config: Any = None,
) -> dict[str, Any]:
    """UI vector packs, icon sheets, and Resonite/VRChat staging."""
    start = time.time()
    stage = Path(staging_dir) if staging_dir else Path(DEFAULT_SIM_STAGING)

    try:
        if operation == "list_presets":
            return SimArtResult(
                success=True,
                operation=operation,
                message="Sim art preset catalog",
                data=list_svg_pack_presets(),
            ).model_dump()

        if operation == "svg_pack_batch":
            if not input_dir:
                return SimArtResult(
                    success=False,
                    operation=operation,
                    message="input_dir required",
                    error="ValueError",
                ).model_dump()
            out = Path(output_dir) if output_dir else stage / "svg_pack"
            result = await _svg_pack_batch(
                input_dir=Path(input_dir),
                output_dir=out,
                template_id=template_id,
                validate=validate,
            )
            return SimArtResult(
                success=bool(result.get("success")),
                operation=operation,
                message=f"SVG pack batch template={template_id}: {result.get('count', 0)} file(s)",
                data=result,
                files=list(result.get("files") or []),
                error="" if result.get("success") else str(result.get("error") or "BatchError"),
            ).model_dump()

        if operation == "build_icon_sheet":
            if not input_dir:
                return SimArtResult(
                    success=False,
                    operation=operation,
                    message="input_dir required",
                    error="ValueError",
                ).model_dump()
            sheet_path = Path(output_path) if output_path else stage / "icon_sheet.svg"
            result = await _build_icon_sheet(
                input_dir=Path(input_dir),
                output_path=sheet_path,
                layout=layout,
                cell_size=cell_size,
                margin_px=margin_px,
                bleed_px=bleed_px,
            )
            files = [str(sheet_path)] if result.get("success") else []
            manifest = result.get("manifest_path")
            if manifest:
                files.append(str(manifest))
            return SimArtResult(
                success=bool(result.get("success")),
                operation=operation,
                message="Icon sheet built" if result.get("success") else "Icon sheet failed",
                data=result,
                files=files,
                error="" if result.get("success") else str(result.get("error") or "SheetError"),
            ).model_dump()

        if operation == "audit_svg_pack":
            if not input_dir:
                return SimArtResult(
                    success=False,
                    operation=operation,
                    message="input_dir required",
                    error="ValueError",
                ).model_dump()
            audit = await _audit_svg_pack_dir(Path(input_dir))
            return SimArtResult(
                success=bool(audit.get("passed")),
                operation=operation,
                message="SVG pack audit passed" if audit.get("passed") else "SVG pack audit failed",
                data=audit,
                error="" if audit.get("passed") else "ValidationError",
            ).model_dump()

        if operation == "ai_svg_refine_loop":
            if not input_dir:
                return SimArtResult(
                    success=False,
                    operation=operation,
                    message="input_dir required",
                    error="ValueError",
                ).model_dump()
            audit = await _audit_svg_pack_dir(Path(input_dir))
            issues = list(audit.get("issues") or [])
            handoff = build_ai_svg_handoff(goal=goal, svg_issues=issues)
            return SimArtResult(
                success=True,
                operation=operation,
                message=f"SVG refine loop: {len(issues)} issue(s)",
                data={
                    "issue_count": len(issues),
                    "issues": issues,
                    "audit": audit,
                    "ai_handoff": handoff,
                },
            ).model_dump()

        if operation == "push_gimp_texture_sheet":
            sheet_svg = output_path or str(stage / "icon_sheet.svg")
            png_out = str(Path(sheet_svg).with_suffix(".png"))
            export = await inkscape_render(
                operation="export_preview",
                input_path=sheet_svg,
                output_path=png_out,
                dpi=dpi,
                cli_wrapper=cli_wrapper,
                config=config,
            )
            if not export.get("success"):
                return SimArtResult(
                    success=False,
                    operation=operation,
                    message="PNG export failed before GIMP handoff",
                    data=export,
                    error=export.get("error") or "ExportError",
                ).model_dump()
            gimp = await push_raster_to_gimp(
                png_path=png_out,
                gimp_url=gimp_url or None,
                target_platform=target_platform,
            )
            return SimArtResult(
                success=bool(gimp.get("success")),
                operation=operation,
                message="Texture sheet pushed to GIMP QA",
                data={"export": export, "gimp_handoff": gimp},
                files=[png_out],
                error="" if gimp.get("success") else str(gimp.get("error") or "GimpHandoffError"),
            ).model_dump()

        if operation == "stage_resonite_ui":
            if not input_dir:
                return SimArtResult(
                    success=False,
                    operation=operation,
                    message="input_dir required",
                    error="ValueError",
                ).model_dump()
            dest = stage / "resonite_ui"
            dest.mkdir(parents=True, exist_ok=True)
            staged_files: list[str] = []
            for src in _iter_svgs(Path(input_dir)):
                staged = await stage_file(
                    source_path=str(src),
                    staging_dir=dest,
                    subdir="icons",
                )
                if staged.get("success"):
                    staged_files.append(str(staged.get("staged_path")))
            sheet = output_path or str(stage / "icon_sheet.svg")
            if Path(sheet).is_file():
                staged_sheet = await stage_file(
                    source_path=sheet,
                    staging_dir=dest,
                    subdir="sheets",
                )
                if staged_sheet.get("success"):
                    staged_files.append(str(staged_sheet.get("staged_path")))
            ok = len(staged_files) > 0
            return SimArtResult(
                success=ok,
                operation=operation,
                message="Staged UI vectors for Resonite pipeline",
                data={"staging_dir": str(dest), "files": staged_files},
                files=staged_files,
                error="" if ok else "NoFilesStaged",
            ).model_dump()

        if operation == "run_sim_pipeline":
            src_dir = Path(input_dir) if input_dir else stage / "svg_in"
            pack_out = stage / "svg_pack"
            sheet_path = stage / "icon_sheet.svg"
            batch = await _svg_pack_batch(
                input_dir=src_dir,
                output_dir=pack_out,
                template_id=template_id,
                validate=validate,
            )
            sheet = await _build_icon_sheet(
                input_dir=pack_out if pack_out.is_dir() else src_dir,
                output_path=sheet_path,
                layout=layout,
                cell_size=cell_size,
                margin_px=margin_px,
                bleed_px=bleed_px,
            )
            audit = await _audit_svg_pack_dir(pack_out if pack_out.is_dir() else src_dir)
            return SimArtResult(
                success=bool(batch.get("success")) and bool(sheet.get("success")),
                operation=operation,
                message="Sim art pipeline complete",
                data={"batch": batch, "sheet": sheet, "audit": audit},
                files=list(batch.get("files") or []) + ([str(sheet_path)] if sheet.get("success") else []),
            ).model_dump()

        return SimArtResult(
            success=False,
            operation=operation,
            message=f"Unknown operation: {operation}",
            error="ValueError",
        ).model_dump()
    except Exception as exc:
        logger.exception("inkscape_sim_art failed operation=%s", operation)
        return SimArtResult(
            success=False,
            operation=operation,
            message=str(exc),
            error=str(exc),
            execution_time_ms=(time.time() - start) * 1000,
        ).model_dump()
