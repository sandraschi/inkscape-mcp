"""SVG QA validation portmanteau for Agent Lab and fleet handoff."""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

logger = logging.getLogger(__name__)

ValidationOperation = Literal[
    "validate_svg",
    "check_viewbox",
    "check_stroke_fill",
    "check_size_limits",
    "audit_web_svg",
    "audit_svg_pack",
]

SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


class ValidationResult(BaseModel):
    success: bool
    operation: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    error: str | None = None


def _parse_svg_root(path: Path) -> ET.Element:
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag.endswith("svg") or root.tag == "svg":
        return root
    raise ValueError("Root element is not SVG")


def _svg_metrics(path: Path, root: ET.Element) -> dict[str, Any]:
    view_box = root.get("viewBox", "").strip()
    width = root.get("width", "")
    height = root.get("height", "")
    elements = list(root.iter())
    tagged = [el for el in elements if el.tag.endswith(("rect", "path", "circle", "ellipse", "polygon", "line", "text"))]
    painted = 0
    for el in tagged:
        if el.get("fill") not in (None, "none") or el.get("stroke") not in (None, "none"):
            painted += 1
    return {
        "path": str(path.resolve()),
        "file_size_bytes": path.stat().st_size,
        "view_box": view_box,
        "width_attr": width,
        "height_attr": height,
        "element_count": len(elements),
        "shape_count": len(tagged),
        "painted_shape_count": painted,
    }


def _viewbox_issues(view_box: str) -> list[str]:
    issues: list[str] = []
    if not view_box:
        issues.append("Missing viewBox attribute")
        return issues
    parts = view_box.replace(",", " ").split()
    if len(parts) != 4:
        issues.append(f"viewBox must have 4 numbers, got: {view_box!r}")
        return issues
    try:
        _x, _y, w, h = (float(p) for p in parts)
        if w <= 0 or h <= 0:
            issues.append(f"viewBox width/height must be positive: {view_box!r}")
    except ValueError:
        issues.append(f"viewBox contains non-numeric values: {view_box!r}")
    return issues


async def inkscape_validation(
    operation: ValidationOperation,
    input_path: str,
    *,
    max_file_size_mb: int = 10,
    max_dimension: float = 16384,
    min_painted_shapes: int = 0,
    cli_wrapper: Any = None,
    config: Any = None,
) -> dict[str, Any]:
    """SVG QA validation for agents and web export pipelines.

    Operations:
        validate_svg - viewBox, size limits, and basic paint coverage
        check_viewbox - viewBox presence and numeric sanity
        check_stroke_fill - ensure drawable elements have stroke or fill
        check_size_limits - file size and declared dimension caps
        audit_web_svg - web-oriented bundle (viewBox + size + paint)
        audit_svg_pack - directory audit for fleet UI icon packs
    """
    del cli_wrapper, config  # reserved for future Inkscape CLI cross-check
    start = time.time()
    path = Path(input_path)

    if operation == "audit_svg_pack":
        if not path.is_dir():
            return ValidationResult(
                success=False,
                operation=operation,
                message=f"Input directory not found: {input_path}",
                error="FileNotFoundError",
            ).model_dump()
        try:
            from ..utils.svg_pack_audit import audit_svg_pack_directory

            audit = await audit_svg_pack_directory(path)
            passed = bool(audit.get("passed"))
            return ValidationResult(
                success=passed,
                operation=operation,
                message="SVG pack audit passed" if passed else "SVG pack audit failed",
                data=audit,
                issues=list(audit.get("issues") or []),
                execution_time_ms=(time.time() - start) * 1000,
                error=None if passed else "ValidationError",
            ).model_dump()
        except Exception as exc:
            logger.exception("audit_svg_pack failed for %s", input_path)
            return ValidationResult(
                success=False,
                operation=operation,
                message=str(exc),
                error=str(exc),
                execution_time_ms=(time.time() - start) * 1000,
            ).model_dump()

    if not path.is_file():
        return ValidationResult(
            success=False,
            operation=operation,
            message=f"Input file not found: {input_path}",
            error="FileNotFoundError",
        ).model_dump()

    try:
        root = _parse_svg_root(path)
        metrics = _svg_metrics(path, root)
    except ET.ParseError as exc:
        logger.error("SVG parse failed for %s: %s", input_path, exc)
        return ValidationResult(
            success=False,
            operation=operation,
            message=f"Invalid SVG XML: {exc}",
            error="ParseError",
        ).model_dump()
    except Exception as exc:
        logger.error("Validation failed for %s: %s", input_path, exc, exc_info=True)
        return ValidationResult(
            success=False,
            operation=operation,
            message=f"Validation error: {exc}",
            error=str(exc),
        ).model_dump()

    issues: list[str] = []
    viewbox_issues = _viewbox_issues(metrics["view_box"])

    if operation in ("validate_svg", "check_viewbox", "audit_web_svg"):
        issues.extend(viewbox_issues)

    if operation in ("validate_svg", "check_stroke_fill", "audit_web_svg"):
        if metrics["shape_count"] > 0 and metrics["painted_shape_count"] == 0:
            issues.append("No drawable shapes with stroke or fill detected")
        if metrics["shape_count"] == 0:
            issues.append("No vector shapes found in document")

    if operation in ("validate_svg", "check_size_limits", "audit_web_svg"):
        max_bytes = max_file_size_mb * 1024 * 1024
        if metrics["file_size_bytes"] > max_bytes:
            issues.append(
                f"File size {metrics['file_size_bytes']} exceeds {max_file_size_mb} MB limit"
            )
        for attr in ("width_attr", "height_attr"):
            raw = metrics[attr]
            if raw and raw.endswith(("px", "pt", "mm", "cm", "in")):
                try:
                    value = float("".join(ch for ch in raw if ch.isdigit() or ch == "."))
                    if value > max_dimension:
                        issues.append(f"{attr} {raw} exceeds max dimension {max_dimension}")
                except ValueError:
                    issues.append(f"Could not parse dimension {attr}={raw!r}")

    if operation == "check_stroke_fill" and min_painted_shapes > 0:
        if metrics["painted_shape_count"] < min_painted_shapes:
            issues.append(
                f"Only {metrics['painted_shape_count']} painted shapes; "
                f"minimum {min_painted_shapes} required"
            )

    ok = len(issues) == 0
    return ValidationResult(
        success=ok,
        operation=operation,
        message="SVG validation passed" if ok else f"SVG validation found {len(issues)} issue(s)",
        data=metrics,
        issues=issues,
        execution_time_ms=(time.time() - start) * 1000,
        error=None if ok else "ValidationError",
    ).model_dump()
