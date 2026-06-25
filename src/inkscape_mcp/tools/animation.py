"""SVG animation — SMIL and CSS keyframe animation generator.

PORTMANTEAU RATIONALE: Consolidates element animation, transform animation,
motion along path, opacity/color fading, and preset animation generators into
a single tool.
"""

from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel


class AnimResult(BaseModel):
    success: bool
    operation: str
    message: str
    data: dict[str, Any]
    execution_time_ms: float
    error: str = ""


def _make_animation_svg(width: int, height: int, defs: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <style>{defs}</style>
  </defs>
  {body}
</svg>"""


# ── Preset animation builders ─────────────────────────────────────────────────


def _preset_bounce(cx: float, cy: float, r: float, fill: str, dur: float) -> str:
    rise = cy - r * 4
    return f"""<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}">
  <animate attributeName="cy" values="{cy};{rise};{cy}" dur="{dur}s" repeatCount="indefinite"
    calcMode="spline" keySplines="0.33 0 0.66 1;0.33 0 0.66 1" keyTimes="0;0.5;1"/>
</circle>"""


def _preset_fade_in(w: float, h: float, fill: str, dur: float) -> str:
    return f"""<rect x="0" y="0" width="{w}" height="{h}" fill="{fill}">
  <animate attributeName="opacity" values="0;1" dur="{dur}s" fill="freeze"/>
</rect>"""


def _preset_fade_out(w: float, h: float, fill: str, dur: float) -> str:
    return f"""<rect x="0" y="0" width="{w}" height="{h}" fill="{fill}">
  <animate attributeName="opacity" values="1;0" dur="{dur}s" fill="freeze"/>
</rect>"""


def _preset_slide(cx: float, cy: float, r: float, fill: str, dur: float) -> str:
    return f"""<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}">
  <animate attributeName="cx" values="{-r};{cx}" dur="{dur}s" fill="freeze" calcMode="spline"
    keySplines="0.25 0.1 0.25 1" keyTimes="0;1"/>
</circle>"""


def _preset_rotate(cx: float, cy: float, fill: str, dur: float, shape: str = "rect") -> str:
    if shape == "rect":
        elem = f'<rect x="{cx-30}" y="{cy-20}" width="60" height="40" rx="4" fill="{fill}"/>'
    else:
        elem = f'<circle cx="{cx}" cy="{cy}" r="30" fill="{fill}"/>'
    return f"""<g>
  <animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/>
  {elem}
</g>"""


def _preset_pulse(cx: float, cy: float, r: float, fill: str, dur: float) -> str:
    return f"""<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}">
  <animate attributeName="r" values="{r};{r*1.5};{r}" dur="{dur}s" repeatCount="indefinite"
    calcMode="spline" keySplines="0.33 0 0.66 1;0.33 0 0.66 1" keyTimes="0;0.5;1"/>
  <animate attributeName="opacity" values="1;0.6;1" dur="{dur}s" repeatCount="indefinite"/>
</circle>"""


def _preset_shake(cx: float, cy: float, r: float, fill: str, dur: float) -> str:
    amp = r * 0.3
    vals = ";".join(f"{cx + amp * math.sin(i * math.pi / 4):.1f}" for i in range(1, 17))
    return f"""<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}">
  <animate attributeName="cx" values="{cx};{vals}" dur="{dur}s" repeatCount="indefinite"/>
</circle>"""


_PRESETS: dict[str, Any] = {
    "bounce": _preset_bounce,
    "fade_in": _preset_fade_in,
    "fade_out": _preset_fade_out,
    "slide": _preset_slide,
    "rotate": _preset_rotate,
    "pulse": _preset_pulse,
    "shake": _preset_shake,
}


# ── Main portmanteau ─────────────────────────────────────────────────────────


async def inkscape_animation(
    operation: Literal[
        "list_presets",
        "apply_preset",
        "animate_element",
        "animate_transform",
        "animate_motion",
        "animate_color",
        "css_animation",
    ],
    output_path: str = "",
    input_path: str = "",
    target_id: str = "",
    attribute: str = "",
    values: str = "",
    key_times: str = "",
    key_splines: str = "",
    duration: float = 1.0,
    repeat: str = "indefinite",
    fill_mode: str = "freeze",
    preset_name: str = "",
    shape: str = "rect",
    color_from: str = "",
    color_to: str = "",
    animation_name: str = "",
    css_keyframes: str = "",
    x: float = 400,
    y: float = 300,
    r: float = 50,
    fill: str = "#4488ff",
    width: int = 800,
    height: int = 600,
    _cli_wrapper: Any = None,
    _config: Any = None,
) -> dict[str, Any]:
    """SVG animation generator portmanteau tool."""
    _start = time.time()

    def ok(op: str, msg: str, data: dict[str, Any]) -> dict[str, Any]:
        return AnimResult(success=True, operation=op, message=msg, data=data,
                          execution_time_ms=(time.time() - _start) * 1000).model_dump()

    def fail(op: str, msg: str, err: str = "", data: dict[str, Any] | None = None) -> dict[str, Any]:
        return AnimResult(success=False, operation=op, message=msg,
                          data=data or {}, error=err, execution_time_ms=0).model_dump()

    if operation == "list_presets":
        return ok("list_presets", f"{len(_PRESETS)} animation presets available",
                  {"presets": list(_PRESETS.keys()), "count": len(_PRESETS)})

    if operation == "apply_preset":
        if preset_name not in _PRESETS:
            return fail("apply_preset", f"Unknown preset '{preset_name}'",
                        data={"available": list(_PRESETS.keys())})
        try:
            builder = _PRESETS[preset_name]
            body = builder(x, y, r, fill, duration)
            doc = _make_animation_svg(width, height, "", body)
            if not output_path:
                output_path = f"animation_{preset_name}.svg"
            Path(output_path).write_text(doc, encoding="utf-8")
            return ok("apply_preset", f"Generated '{preset_name}' animation at {output_path}",
                      {"preset": preset_name, "output_path": output_path, "duration": duration})
        except Exception as e:
            return fail("apply_preset", f"Failed: {e}", str(e))

    if operation == "animate_element":
        if not target_id or not attribute or not values or not output_path:
            return fail("animate_element", "Required: target_id, attribute, values, output_path")
        anim = f'<animate attributeName="{attribute}" values="{values}" dur="{duration}s" repeatCount="{repeat}" fill="{fill_mode}"'
        if key_times:
            anim += f' keyTimes="{key_times}"'
        if key_splines:
            anim += f' keySplines="{key_splines}"'
        if ";" in values or "," in values:
            anim += ' calcMode="spline"'
        anim += "/>"

        if input_path:
            # Inject into existing SVG — append animation to target element
            try:
                svg = Path(input_path).read_text(encoding="utf-8", errors="replace")
                import re
                # Find the element and insert animation child
                def _inject(m: re.Match) -> str:
                    full = m.group(0)
                    # Insert before closing tag
                    if "/>" in full:
                        return full.replace("/>", f">{anim}\n</{m.group(1)}>")
                    return full.rstrip(">").rstrip() + f">{anim}</{m.group(1)}>"
                pattern = re.compile(
                    rf'<(\w+)(?:\s+[^>]*)?\s+id="{re.escape(target_id)}"[^>]*/?>', re.DOTALL
                )
                if not pattern.search(svg):
                    return fail("animate_element", f"Element '{target_id}' not found in {input_path}")
                new_svg = pattern.sub(_inject, svg)
                Path(output_path).write_text(new_svg, encoding="utf-8")
                return ok("animate_element", f"Animation injected into '{target_id}'",
                          {"target_id": target_id, "attribute": attribute,
                           "values": values, "duration": duration, "output_path": output_path})
            except Exception as e:
                return fail("animate_element", f"Failed to inject: {e}", str(e))
        else:
            # Standalone SVG with animated element
            body = f'<{shape} id="{target_id}"'
            for attr, val in [("cx", x), ("cy", y), ("r", r), ("fill", fill),
                              ("x", 0), ("y", 0), ("width", width), ("height", height)]:
                if shape in ("circle", "ellipse") and attr in ("x", "y", "width", "height"):
                    continue
                if attr in ("cx", "cy", "r") and shape not in ("circle",):
                    continue
                body += f' {attr}="{val}"'
            body += f">\n  {anim}\n</{shape}>"
            doc = _make_animation_svg(width, height, "", body)
            Path(output_path).write_text(doc, encoding="utf-8")
            return ok("animate_element", f"Created animated SVG at {output_path}",
                      {"target_id": target_id, "attribute": attribute,
                       "values": values, "duration": duration, "output_path": output_path})

    if operation == "animate_transform":
        if not target_id or not values or not output_path:
            return fail("animate_transform", "Required: target_id, values, output_path")
        # values format: "0 0;360 0" = rotation "from to" or "0,0;100,0" = translation
        anim_type = "rotate"
        if "translate" in attribute.lower() or attribute in ("x", "y"):
            anim_type = "translate"
        elif attribute in ("scale", "scale_x", "scale_y"):
            anim_type = "scale"
        anim = f'<animateTransform attributeName="transform" type="{anim_type}" ' \
               f'values="{values}" dur="{duration}s" repeatCount="{repeat}" fill="{fill_mode}"'
        if key_times:
            anim += f' keyTimes="{key_times}"'
        if key_splines:
            anim += f' keySplines="{key_splines}"'
        anim += "/>"
        body = f'<rect id="{target_id}" x="{x-30}" y="{y-20}" width="60" height="40" rx="4" fill="{fill}">\n  {anim}\n</rect>'
        doc = _make_animation_svg(width, height, "", body)
        Path(output_path).write_text(doc, encoding="utf-8")
        return ok("animate_transform", f"Transform animation for '{target_id}'",
                  {"target_id": target_id, "type": anim_type,
                   "values": values, "duration": duration, "output_path": output_path})

    if operation == "animate_motion":
        if not target_id or not output_path:
            return fail("animate_motion", "Required: target_id, output_path")
        d = values or f"M {x-width/2},{y} C {x-width/4},{y-height/4} {x+width/4},{y+height/4} {x+width/2},{y}"
        anim = f'<animateMotion dur="{duration}s" repeatCount="{repeat}" fill="{fill_mode}" path="{d}"/>'
        body = f'<circle id="{target_id}" cx="0" cy="0" r="{min(r, 20)}" fill="{fill}">\n  {anim}\n</circle>'
        doc = _make_animation_svg(width, height, "", body)
        Path(output_path).write_text(doc, encoding="utf-8")
        return ok("animate_motion", f"Motion path animation for '{target_id}'",
                  {"target_id": target_id, "path": d, "duration": duration, "output_path": output_path})

    if operation == "animate_color":
        if not target_id or not color_to or not output_path:
            return fail("animate_color", "Required: target_id, color_to, output_path")
        attr = attribute or "fill"
        vals = f"{color_from or fill};{color_to};{color_from or fill}"
        anim = f'<animate attributeName="{attr}" values="{vals}" dur="{duration}s" repeatCount="{repeat}"/>'
        body = f'<circle id="{target_id}" cx="{x}" cy="{y}" r="{r}" fill="{fill}">\n  {anim}\n</circle>'
        doc = _make_animation_svg(width, height, "", body)
        Path(output_path).write_text(doc, encoding="utf-8")
        return ok("animate_color", f"Color animation for '{target_id}'",
                  {"target_id": target_id, "attr": attr,
                   "from": color_from or fill, "to": color_to, "output_path": output_path})

    if operation == "css_animation":
        if not animation_name or not css_keyframes or not output_path:
            return fail("css_animation", "Required: animation_name, css_keyframes, output_path")
        style = f"""
@{'keyframes ' + animation_name} {{
  {css_keyframes}
}}
.{animation_name} {{
  animation: {animation_name} {duration}s {repeat.replace("indefinite", "infinite")};
}}"""
        body = f'<circle class="{animation_name}" cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>'
        doc = _make_animation_svg(width, height, style, body)
        Path(output_path).write_text(doc, encoding="utf-8")
        return ok("css_animation", f"CSS animation '{animation_name}' at {output_path}",
                  {"animation_name": animation_name, "keyframes": css_keyframes,
                   "duration": duration, "output_path": output_path})

    return fail(operation, f"Unknown operation: {operation}")
