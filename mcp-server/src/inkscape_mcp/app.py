"""
Inkscape MCP — FastMCP 3.1 REST API Bridge

/api/generate-svg pipeline:
  1. Ollama (local RTX 4090) generates SVG XML — primary
  2. Inkscape CLI validates & saves the SVG to disk — always
  3. Cloud APIs (Gemini/Anthropic) — optional fallback if Ollama is unreachable

Environment (via .env or system):
    OLLAMA_BASE_URL     default: http://localhost:11434
    OLLAMA_MODEL        default: qwen2.5-coder:latest
    INKSCAPE_SAVE_DIR   default: ~/Documents/inkscape-mcp/generated
    GEMINI_API_KEY      optional cloud fallback
    ANTHROPIC_API_KEY   optional cloud fallback
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any

try:
    import httpx
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from starlette.routing import Mount

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger(__name__)

# ── Config from env ───────────────────────────────────────────────────────────


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _ollama_base() -> str:
    return _env("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def _ollama_model() -> str:
    return _env("OLLAMA_MODEL", "qwen2.5-coder:latest")


def _save_dir() -> Path:
    d = _env("INKSCAPE_SAVE_DIR", "")
    if d:
        return Path(d)
    return Path.home() / "Documents" / "inkscape-mcp" / "generated"


# ── SVG System prompt ─────────────────────────────────────────────────────────

_SVG_SYSTEM = """You are an expert SVG artist. Generate complete, valid SVG XML.

RULES:
- Output ONLY valid SVG XML. NO markdown fences, NO explanation, NO commentary.
- Start with <svg xmlns="http://www.w3.org/2000/svg" width="W" height="H">
- Use proper SVG elements: <path>, <circle>, <rect>, <polygon>, <g>, <defs>,
  <linearGradient>, <radialGradient>, <text>, <symbol>
- For HERALDIC requests:
  * "asses rampant" = donkeys rearing on hind legs, facing each other
  * Include shield shape, charges (figures on the shield), crest at top,
    supporters on sides, motto scroll at bottom
  * Tinctures: azure=blue, gules=red, or=gold, argent=silver, sable=black,
    vert=green, purpure=purple
  * Draw actual animal/figure shapes as SVG paths, not placeholder boxes
- For GEOMETRIC: mathematical precision, clean shapes
- For ORGANIC: flowing bezier curves, natural forms
- For ABSTRACT: expressive, artistic, layered
- For TECHNICAL: labelled diagram with precise layout

Output NOTHING except the SVG XML itself."""


def _user_prompt(
    description: str, style: str, width: int, height: int, quality: str
) -> str:
    detail = {
        "draft": "Simple, minimal detail.",
        "standard": "Good detail, all elements rendered.",
        "high": "Rich detail, gradients, multiple layers.",
        "ultra": "Maximum artistic detail, complex paths, full composition.",
    }.get(quality, "Good detail.")
    return (
        f"Create a {style} SVG ({width}x{height}px).\n"
        f"Description: {description}\n"
        f"Quality: {detail}\n"
        f'The SVG must have width="{width}" and height="{height}".'
    )


def _extract_svg(text: str) -> str | None:
    """Strip markdown wrappers and extract the SVG block."""
    text = re.sub(r"```(?:svg|xml)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE).strip()
    m = re.search(r"(<\?xml[^>]*\?>)?\s*(<svg[\s\S]*?</svg>)", text, re.IGNORECASE)
    if m:
        decl = (m.group(1) or "").strip()
        svg = m.group(2).strip()
        return f"{decl}\n{svg}".strip() if decl else svg
    return None


# ── Ollama call ───────────────────────────────────────────────────────────────


async def _call_ollama(prompt: str, system: str) -> str:
    """POST to Ollama /api/chat — no external API key needed."""
    url = f"{_ollama_base()}/api/chat"
    payload = {
        "model": _ollama_model(),
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.7, "num_predict": 8192},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
    return r.json()["message"]["content"]


# ── Cloud fallbacks ───────────────────────────────────────────────────────────


async def _call_gemini(prompt: str, system: str) -> str:
    api_key = _env("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
    candidates = r.json().get("candidates", [])
    parts = candidates[0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


async def _call_anthropic(prompt: str, system: str) -> str:
    api_key = _env("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5",
                "max_tokens": 8192,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        r.raise_for_status()
    return r.json()["content"][0]["text"]


# ── Primary generation pipeline ───────────────────────────────────────────────


async def _generate_svg(
    description: str, style: str, dimensions: str, quality: str
) -> tuple[str, str]:
    """
    Returns (svg_xml, model_used).
    Tries Ollama first, then cloud APIs if configured.
    """
    try:
        w, h = (int(x) for x in dimensions.lower().split("x"))
    except ValueError:
        w, h = 800, 600

    user_p = _user_prompt(description, style, w, h, quality)

    # 1. Ollama (local — primary)
    try:
        raw = await _call_ollama(user_p, _SVG_SYSTEM)
        model_used = f"ollama/{_ollama_model()}"
        logger.info("SVG generated via Ollama (%s)", _ollama_model())
    except Exception as ollama_err:
        logger.warning("Ollama unavailable (%s), trying cloud fallbacks", ollama_err)
        # 2. Gemini fallback
        if _env("GEMINI_API_KEY"):
            raw = await _call_gemini(user_p, _SVG_SYSTEM)
            model_used = "gemini-2.0-flash"
        # 3. Anthropic fallback
        elif _env("ANTHROPIC_API_KEY"):
            raw = await _call_anthropic(user_p, _SVG_SYSTEM)
            model_used = "claude-haiku-4-5"
        else:
            raise ValueError(
                f"Ollama unreachable ({ollama_err}) and no cloud API keys configured. "
                "Check that Ollama is running: ollama serve"
            )

    svg = _extract_svg(raw)
    if not svg:
        logger.warning(
            "Could not parse SVG from response (len=%d), constructing fallback",
            len(raw),
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
            f'<rect width="{w}" height="{h}" fill="#1a1a2e"/>'
            f'<text x="{w // 2}" y="{h // 2}" text-anchor="middle" fill="#e94560" '
            f'font-family="monospace" font-size="14">'
            f"SVG parse error — raw response length: {len(raw)} chars"
            f"</text></svg>"
        )
    return svg, model_used


# ── Inkscape CLI save ─────────────────────────────────────────────────────────


async def _save_via_inkscape(
    svg_xml: str, stem: str, inkscape_exe: str | None
) -> str | None:
    """
    Write SVG to temp file, then use Inkscape to re-export it (normalises,
    validates, and saves a clean SVG). Returns final saved path or None.
    """
    if not inkscape_exe or not Path(inkscape_exe).exists():
        return None
    try:
        save_dir = _save_dir()
        save_dir.mkdir(parents=True, exist_ok=True)

        # Write raw LLM SVG to temp
        with tempfile.NamedTemporaryFile(
            suffix=".svg", delete=False, dir=save_dir, mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write(svg_xml)
            tmp_path = tmp.name

        # Output path
        out_path = str(save_dir / f"{stem}.svg")

        # Inkscape: load temp, export as plain SVG
        proc = await asyncio.create_subprocess_exec(
            inkscape_exe,
            tmp_path,
            "--export-type=svg",
            f"--export-filename={out_path}",
            "--export-plain-svg",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        Path(tmp_path).unlink(missing_ok=True)

        if proc.returncode == 0 and Path(out_path).exists():
            logger.info("Inkscape saved SVG to %s", out_path)
            return out_path
        else:
            logger.warning(
                "Inkscape save failed (rc=%d): %s",
                proc.returncode,
                stderr.decode()[:200],
            )
            return None
    except Exception as e:
        logger.warning("Inkscape save error: %s", e)
        return None


# ── FastAPI app factory ───────────────────────────────────────────────────────


def register_rest_api(mcp: Any, config: Any | None = None) -> None:
    """Attach /api/* REST layer to the FastMCP 3.1 HTTP server."""
    if not FASTAPI_AVAILABLE:
        logger.warning("fastapi/httpx not installed — REST API bridge unavailable.")
        return
    if not hasattr(mcp, "_additional_http_routes"):
        logger.warning(
            "FastMCP has no _additional_http_routes — REST bridge unavailable."
        )
        return

    # Grab Inkscape path from config if available
    inkscape_exe: str | None = None
    if config and hasattr(config, "inkscape_executable"):
        inkscape_exe = config.inkscape_executable

    app = FastAPI(title="Inkscape MCP REST Bridge", version="2.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── /api/health ──────────────────────────────────────────────────────────
    @app.get("/api/health")
    async def health() -> dict:
        ollama_ok = False
        try:
            async with httpx.AsyncClient(timeout=3.0) as c:
                r = await c.get(f"{_ollama_base()}/api/tags")
                if r.status_code == 200:
                    models = [m["name"] for m in r.json().get("models", [])]
                    ollama_ok = True
        except Exception:
            models = []
        return {
            "status": "ok",
            "server": "inkscape-mcp",
            "version": "2.0.0b0",
            "providers": {
                "ollama": {
                    "available": ollama_ok,
                    "base_url": _ollama_base(),
                    "model": _ollama_model(),
                    "models": models,
                },
                "inkscape": {
                    "available": bool(inkscape_exe and Path(inkscape_exe).exists()),
                    "path": inkscape_exe,
                },
                "gemini_key": bool(_env("GEMINI_API_KEY")),
                "anthropic_key": bool(_env("ANTHROPIC_API_KEY")),
            },
        }

    # ── /api/generate-svg ────────────────────────────────────────────────────
    @app.post("/api/generate-svg")
    async def generate_svg_endpoint(request_data: dict) -> JSONResponse:
        """
        Generate SVG via local Ollama → Inkscape CLI pipeline.
        Falls back to cloud APIs only if Ollama is unreachable.
        """
        try:
            description = request_data.get("description", "a simple geometric design")
            style = request_data.get("style_preset", "geometric")
            dimensions = request_data.get("dimensions", "800x600")
            quality = request_data.get("quality", "standard")

            logger.info(
                "generate-svg: %r [%s %s %s]",
                description[:60],
                style,
                dimensions,
                quality,
            )

            svg_xml, model_used = await _generate_svg(
                description, style, dimensions, quality
            )

            # Save via Inkscape CLI
            import re as _re

            stem = _re.sub(r"[^\w]", "_", description[:40]).strip("_") or "generated"
            svg_path = await _save_via_inkscape(svg_xml, stem, inkscape_exe)

            file_size_kb = round(len(svg_xml.encode()) / 1024, 2)

            return JSONResponse(
                {
                    "success": True,
                    "svg_content": svg_xml,
                    "svg_path": svg_path,
                    "file_size_kb": file_size_kb,
                    "steps_taken": 1,
                    "model_used": model_used,
                }
            )

        except ValueError as e:
            return JSONResponse(
                {"success": False, "error": str(e), "error_type": "configuration"},
                status_code=400,
            )
        except Exception as e:
            logger.exception("generate-svg error: %s", e)
            return JSONResponse(
                {"success": False, "error": str(e), "error_type": "internal"},
                status_code=500,
            )

    # ── /api/capabilities ────────────────────────────────────────────────────
    @app.get("/api/capabilities")
    async def capabilities() -> dict:
        from inkscape_mcp.agentic import (  # noqa: PLC0415
            get_inkscape_file_capabilities,
            get_inkscape_vector_capabilities,
            get_inkscape_heraldic_capabilities,
            get_inkscape_style_capabilities,
            get_svg_generation_approach,
        )

        return {
            "file": get_inkscape_file_capabilities(),
            "vector": get_inkscape_vector_capabilities(),
            "heraldic": get_inkscape_heraldic_capabilities(),
            "style": get_inkscape_style_capabilities(),
            "generation_approach": get_svg_generation_approach(),
        }

    try:
        mcp._additional_http_routes.append(Mount("/api", app=app))
        logger.info(
            "REST API bridge mounted at /api  [Ollama: %s/%s]",
            _ollama_base(),
            _ollama_model(),
        )
    except Exception as e:
        logger.warning("Failed to mount REST API bridge: %s", e)
