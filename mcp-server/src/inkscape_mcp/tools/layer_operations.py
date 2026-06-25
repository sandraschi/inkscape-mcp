"""Layer management for Inkscape SVG documents.

PORTMANTEAU: Consolidates create, rename, hide/show, reorder, lock/unlock,
and list operations into a single tool.

Operations target SVG `<g inkscape:groupmode="layer">` elements directly —
most ops are pure XML manipulation (no CLI needed).
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel


class LayerResult(BaseModel):
    success: bool
    operation: str
    message: str
    data: dict[str, Any]
    execution_time_ms: float
    error: str = ""


# ── XML helpers ───────────────────────────────────────────────────────────────

_NS = r'inkscape:groupmode="layer"'
_LAYER_RE = re.compile(
    r'(<g\b[^>]*inkscape:groupmode="layer"[^>]*>.*?</g>)', re.DOTALL
)
_ATTR_RE = re.compile(r'(\b[a-zA-Z_:][\w._:-]*)\s*=\s*["\']([^"\']*)["\']')


def _parse_svg_xml(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _write_svg_xml(path: str, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def _extract_layers(svg_xml: str) -> list[dict[str, str | None]]:
    """Find all `<g inkscape:groupmode="layer">` elements and return their attributes."""
    layers: list[dict[str, str | None]] = []
    for match in _LAYER_RE.findall(svg_xml):
        tag = match[: match.index(">") + 1] if ">" in match else match
        attrs: dict[str, str | None] = {}
        for a_name, a_val in _ATTR_RE.findall(tag):
            attrs[a_name] = a_val
        layers.append({
            "id": attrs.get("id"),
            "label": attrs.get("inkscape:label"),
            "style": attrs.get("style"),
            "visible": "display:none" not in (attrs.get("style") or ""),
            "locked": attrs.get("sodipodi:insensitive") == "true",
        })
    return layers


def _layer_by_id(svg_xml: str, layer_id: str) -> tuple[str | None, dict[str, str | None]]:
    """Return (full_tag, attrs_dict) for a layer matching the id, or (None, {})."""
    for match in _LAYER_RE.findall(svg_xml):
        tag_open = match[: match.index(">") + 1] if ">" in match else match
        attrs: dict[str, str | None] = {}
        for a_name, a_val in _ATTR_RE.findall(tag_open):
            attrs[a_name] = a_val
        if attrs.get("id") == layer_id:
            return match, attrs
    return None, {}


def _next_layer_id(svg_xml: str) -> str:
    existing = {lyr["id"] for lyr in _extract_layers(svg_xml) if lyr["id"]}
    for i in range(1, 100):
        lid = f"layer{i}"
        if lid not in existing:
            return lid
    return f"layer{len(existing) + 1}"


def _set_layer_attr(svg_xml: str, layer_id: str, attr: str, value: str) -> str:
    """Replace an attribute on a layer by id. Returns modified SVG XML."""
    old_tag, _ = _layer_by_id(svg_xml, layer_id)
    if old_tag is None:
        raise ValueError(f"Layer '{layer_id}' not found")

    # Replace or add the attribute in the opening tag
    tag_open = old_tag[: old_tag.index(">") + 1]
    if f'{attr}="' in tag_open or f"{attr}='" in tag_open:
        new_tag = re.sub(
            rf'\b{attr}\s*=\s*["\'][^"\']*["\']',
            f'{attr}="{value}"',
            tag_open,
        )
    else:
        # Insert before the closing >
        new_tag = tag_open[:-1] + f' {attr}="{value}">'
    new_tag_body = new_tag + old_tag[old_tag.index(">") + 1 :]
    return svg_xml.replace(old_tag, new_tag_body)


# ── Operation implementations ─────────────────────────────────────────────────


async def inkscape_layers(
    operation: Literal["list", "get", "create", "rename", "hide", "show", "reorder", "lock", "unlock"],
    input_path: str = "",
    output_path: str = "",
    layer_id: str = "",
    label: str = "",
    new_label: str = "",
    position: int = 0,
    _cli_wrapper: Any = None,
    _config: Any = None,
) -> dict[str, Any]:
    """Inkscape layer management portmanteau tool."""
    _start = time.time()

    def ok(op: str, msg: str, data: dict[str, Any]) -> dict[str, Any]:
        return LayerResult(
            success=True, operation=op, message=msg, data=data,
            execution_time_ms=(time.time() - _start) * 1000,
        ).model_dump()

    def fail(op: str, msg: str, err: str = "", data: dict[str, Any] | None = None) -> dict[str, Any]:
        return LayerResult(
            success=False, operation=op, message=msg,
            data=data or {}, error=err, execution_time_ms=0,
        ).model_dump()

    if not input_path or not Path(input_path).exists():
        return fail(operation, f"File not found: {input_path}", "FileNotFoundError")

    try:
        svg = _parse_svg_xml(input_path)
    except Exception as e:
        return fail(operation, f"Cannot read SVG: {e}", str(e))

    try:
        if operation == "list":
            layers = _extract_layers(svg)
            return ok("list", f"Found {len(layers)} layer(s)", {"layers": layers, "count": len(layers)})

        elif operation == "get":
            layers = _extract_layers(svg)
            match = next((ly for ly in layers if ly["id"] == layer_id), None)
            if not match:
                return fail("get", f"Layer '{layer_id}' not found", data={"available": [ly["id"] for ly in layers]})
            return ok("get", f"Layer: {layer_id}", {"layer": match})

        elif operation == "create":
            lid = _next_layer_id(svg)
            lbl = label or f"Layer {lid[len('layer'):]}"
            layer_tag = (
                f'<g\n'
                f'    inkscape:groupmode="layer"\n'
                f'    id="{lid}"\n'
                f'    inkscape:label="{lbl}">\n'
                f'  </g>'
            )
            # Insert before closing </svg>
            if "</svg>" in svg:
                new_svg = svg.replace("</svg>", f"  {layer_tag}\n</svg>")
            else:
                new_svg = svg + f"\n  {layer_tag}\n"
            dest = output_path or input_path
            _write_svg_xml(dest, new_svg)
            return ok("create", f"Created layer '{lid}' ({lbl})", {"id": lid, "label": lbl, "path": dest})

        elif operation == "rename":
            if not layer_id or not new_label:
                return fail("rename", "layer_id and new_label are required", "ValueError")
            new_svg = _set_layer_attr(svg, layer_id, "inkscape:label", new_label)
            dest = output_path or input_path
            _write_svg_xml(dest, new_svg)
            return ok("rename", f"Renamed '{layer_id}' → '{new_label}'", {"id": layer_id, "label": new_label})

        elif operation == "hide":
            if not layer_id:
                return fail("hide", "layer_id is required", "ValueError")
            # Get current style or default
            _, attrs = _layer_by_id(svg, layer_id)
            cur = attrs.get("style") or "display:inline"
            cur = cur.replace("display:inline;", "").replace("display:inline", "").strip()
            new_style = ("display:none;" + cur).rstrip(";")
            new_svg = _set_layer_attr(svg, layer_id, "style", new_style)
            dest = output_path or input_path
            _write_svg_xml(dest, new_svg)
            return ok("hide", f"Hidden layer '{layer_id}'", {"id": layer_id, "style": new_style})

        elif operation == "show":
            if not layer_id:
                return fail("show", "layer_id is required", "ValueError")
            _, attrs = _layer_by_id(svg, layer_id)
            cur = attrs.get("style") or "display:none"
            cur = cur.replace("display:none;", "").replace("display:none", "").strip()
            if not cur:
                cur = "display:inline"
            new_svg = _set_layer_attr(svg, layer_id, "style", cur)
            dest = output_path or input_path
            _write_svg_xml(dest, new_svg)
            return ok("show", f"Showed layer '{layer_id}'", {"id": layer_id, "style": cur})

        elif operation == "reorder":
            # Move layer to position in <svg> child order
            layers = _extract_layers(svg)
            if position < 0 or position >= len(layers):
                return fail("reorder", f"Position {position} out of range (0-{len(layers)-1})", "ValueError")
            target = next((ly for ly in layers if ly["id"] == layer_id), None)
            if not target:
                return fail("reorder", f"Layer '{layer_id}' not found", data={"available": [ly["id"] for ly in layers]})

            # Remove the layer tag and re-insert at position
            old_tag, _ = _layer_by_id(svg, layer_id)
            if old_tag is None:
                return fail("reorder", f"Cannot read layer tag for '{layer_id}'")
            svg_without = svg.replace(old_tag + ("\n" if "\n" + old_tag in svg else ""), "\n<!-- reorder-temp -->\n")
            # Re-insert: find the position-th <g after <svg>
            parts = svg_without.split("<!-- reorder-temp -->")
            if len(parts) != 2:
                return fail("reorder", "Internal error: could not split SVG at marker")
            # Count <g> elements before insertion point
            before = parts[0]
            g_elements = list(re.finditer(r"<g\b[^>]*inkscape:groupmode=\"layer\"[^>]*>", before))
            if position > len(g_elements):
                position = len(g_elements)
            if position == 0:
                # Insert right after the first layer
                first = re.search(r"<g\b[^>]*inkscape:groupmode=\"layer\"[^>]*>", before)
                if first:
                    insert_pos = first.start()
                    new_svg = before[:insert_pos] + old_tag + "\n" + before[insert_pos:]
                else:
                    # No layers yet — insert after <svg ...> tag
                    match = re.search(r"<svg\b[^>]*>", before)
                    insert_pos = match.end() if match else 0
                    new_svg = before[:insert_pos] + "\n  " + old_tag + "\n" + before[insert_pos:]
            else:
                g_list = list(re.finditer(r"<g\b[^>]*inkscape:groupmode=\"layer\"[^>]*>", before))
                target_g = g_list[position - 1]
                insert_pos = target_g.end()
                new_svg = before[:insert_pos] + "\n" + old_tag + "\n" + before[insert_pos:]
            new_svg = new_svg.replace("<!-- reorder-temp -->", "")
            if parts[1]:
                new_svg += parts[1]

            dest = output_path or input_path
            _write_svg_xml(dest, new_svg)
            return ok("reorder", f"Moved '{layer_id}' to position {position}", {"id": layer_id, "position": position})

        elif operation == "lock":
            if not layer_id:
                return fail("lock", "layer_id is required", "ValueError")
            new_svg = _set_layer_attr(svg, layer_id, "sodipodi:insensitive", "true")
            dest = output_path or input_path
            _write_svg_xml(dest, new_svg)
            return ok("lock", f"Locked layer '{layer_id}'", {"id": layer_id})

        elif operation == "unlock":
            if not layer_id:
                return fail("unlock", "layer_id is required", "ValueError")
            new_svg = _set_layer_attr(svg, layer_id, "sodipodi:insensitive", "false")
            dest = output_path or input_path
            _write_svg_xml(dest, new_svg)
            return ok("unlock", f"Unlocked layer '{layer_id}'", {"id": layer_id})

        else:
            return fail(operation, f"Unknown operation: {operation}", "ValueError")

    except Exception as e:
        return fail(operation, f"Layer operation failed: {e}", str(e))
