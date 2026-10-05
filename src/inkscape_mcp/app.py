"""
Inkscape MCP - FastMCP 3.1 REST API Bridge

/api/generate-svg pipeline:
  1. Ollama (local RTX 4090) generates SVG XML - primary
  2. Inkscape CLI validates & saves the SVG to disk - always
  3. Cloud APIs (Gemini/Anthropic) - optional fallback if Ollama is unreachable

Environment (via .env or system):
    OLLAMA_BASE_URL     default: http://localhost:11434
    OLLAMA_MODEL        default: qwen2.5-coder:latest
    INKSCAPE_SAVE_DIR   default: ~/Documents/inkscape-mcp/generated
    GEMINI_API_KEY      optional cloud fallback
    ANTHROPIC_API_KEY   optional cloud fallback
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import os
import re
import tempfile
import threading
import time
from collections.abc import AsyncGenerator
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import PlainTextResponse
from starlette.responses import Response
from starlette.responses import StreamingResponse
from starlette.routing import Mount

from .services import llm_engine
from .services import llm_settings_store
from .services import server_settings

FASTAPI_AVAILABLE = True

logger = logging.getLogger(__name__)

# ── In-memory log ring (HTTP dashboard GET /api/logs) ─────────────────────────
MAX_MEMORY_LOGS = 1000
_memory_logs: list[dict[str, Any]] = []
_memory_lock = threading.Lock()
_memory_handler: logging.Handler | None = None
_log_id_counter = 0


class _MemoryLogHandler(logging.Handler):
    """Capture log records for the web UI (no persistence)."""

    def emit(self, record: logging.LogRecord) -> None:
        global _log_id_counter
        try:
            msg = self.format(record)
            ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            name_lower = record.name.lower()
            if "tool" in name_lower:
                kind = "tool_call"
            elif "export" in name_lower:
                kind = "export"
            else:
                kind = "server"
            with _memory_lock:
                _log_id_counter += 1
                entry = {
                    "id": str(_log_id_counter),
                    "timestamp": ts,
                    "level": record.levelname,
                    "kind": kind,
                    "detail": msg,
                    "meta": {"logger": record.name},
                }
                _memory_logs.append(entry)
                overflow = len(_memory_logs) - MAX_MEMORY_LOGS
                if overflow > 0:
                    del _memory_logs[0:overflow]
        except Exception:
            self.handleError(record)


def _filter_logs(
    logs: list[dict[str, Any]], *, level: str = "", kind: str = "", search: str = ""
) -> list[dict[str, Any]]:
    if level:
        logs = [e for e in logs if e.get("level") == level]
    if kind:
        logs = [e for e in logs if e.get("kind") == kind]
    if search:
        needle = search.lower()
        logs = [
            e
            for e in logs
            if needle in str(e.get("detail", "")).lower()
            or needle in json.dumps(e.get("meta", {})).lower()
        ]
    return logs


def _attach_memory_logging() -> None:
    global _memory_handler
    if _memory_handler is not None:
        return
    _memory_handler = _MemoryLogHandler()
    _memory_handler.setLevel(logging.INFO)
    _memory_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    # When this app is imported directly as an ASGI target (e.g. `uvicorn
    # inkscape_mcp.server:app`, as the fleet launcher does), main.py's CLI-only
    # logging.basicConfig() never runs, so the root logger stays at its default
    # WARNING level and every INFO record - including this buffer's own entries -
    # is dropped before it reaches any handler. Raise it, but never lower a level
    # someone already configured more verbosely.
    if root.level == logging.NOTSET or root.level > logging.INFO:
        root.setLevel(logging.INFO)
    root.addHandler(_memory_handler)
    logger.info("REST: memory log buffer enabled (GET/DELETE /api/logs)")


def _help_payload() -> dict[str, Any]:
    return {
        "title": "Inkscape MCP - help",
        "summary": (
            "Vector and SVG operations run through MCP tools that call the Inkscape CLI. "
            "Use Cursor, Claude Desktop, or another MCP client for natural-language workflows. "
            "This dashboard shows status, logs, and optional REST helpers."
        ),
        "tools": [
            "inkscape_file - load, convert, info, validate, list_formats",
            "inkscape_vector - trace, boolean, simplify, preview, QR, …",
            "inkscape_render - export_preview, export_multi_dpi, get_document_summary",
            "inkscape_validation - validate_svg, check_viewbox, audit_web_svg, …",
            "inkscape_fleet - push_gimp_raster, stage_blender_svg, push_unity_sprite, run_pipeline",
            "inkscape_fab_art - DXF/laser fab paths, Gazebo schematics, robotics staging",
            "inkscape_sim_art - SVG icon packs, icon sheets, Resonite UI staging",
            "inkscape_analysis - statistics, validate, dimensions",
            "inkscape_system - status, execution_mode, help, config, diagnostics",
            "list_local_models - optional Ollama/LM Studio discovery",
        ],
        "http_ports": {
            "vite_dev_ui": 10899,
            "mcp_http_listener": int(os.environ.get("MCP_PORT", "10900")),
        },
        "env": {
            "OLLAMA_BASE_URL": "Optional; for /api/generate-svg and health check",
            "OLLAMA_MODEL": "Default model name for Ollama",
            "MCP_PORT": "HTTP port for MCP + this REST bridge",
            "INKSCAPE_PATH": "Override Inkscape executable if not on PATH",
        },
        "links": [
            {"label": "Repository", "url": "https://github.com/sandraschi/inkscape-mcp"},
            {"label": "Install (docs)", "path": "docs/INSTALL.md"},
        ],
    }


async def _inkscape_version_line(exe: str) -> str | None:
    """First line of `inkscape --version` for health reporting."""
    try:
        proc = await asyncio.create_subprocess_exec(
            exe,
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=10.0)
        if proc.returncode == 0 and out:
            line = out.decode(errors="replace").strip().split("\n")[0].strip()
            return line[:240] if line else None
    except Exception:
        return None
    return None


def _inkscape_version_tuple(version_line: str | None) -> tuple[int, int] | None:
    if not version_line:
        return None
    m = re.search(r"Inkscape\s+(\d+)\.(\d+)", version_line, re.I)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


# ── Config from env ───────────────────────────────────────────────────────────


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _ollama_base() -> str:
    # Same priority as _ollama_model(): the endpoint saved against the active
    # Ollama selection in AI Settings' Active LLM card wins over the
    # server-wide override, so there is one place - not two disconnected
    # ones - that actually controls which Ollama this server talks to.
    active = llm_settings_store.load_settings()
    if active.get("provider") == "ollama" and active.get("endpoint"):
        return str(active["endpoint"]).rstrip("/")
    override = server_settings.load().get("ollama_base_url", "")
    return (override or _env("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")


def _ollama_model() -> str:
    # The model the user actually picked in AI Settings' Active LLM card wins.
    # generate_svg silently defaulting to a different, possibly-not-pulled
    # model while the user has a real one selected and loaded is exactly how
    # a hardcoded "qwen2.5-coder:latest" default 404s against Ollama even
    # though Ollama itself is up and has 30+ other models pulled.
    active = llm_settings_store.load_settings()
    if active.get("provider") == "ollama" and active.get("model"):
        return str(active["model"])
    override = server_settings.load().get("ollama_model", "")
    return override or _env("OLLAMA_MODEL", "qwen2.5-coder:latest")


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


def _user_prompt(description: str, style: str, width: int, height: int, quality: str) -> str:
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
    """POST to Ollama /api/chat - no external API key needed."""
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
        f"gemini-3.5-flash-lite:generateContent?key={api_key}"
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
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 8192,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        r.raise_for_status()
    return r.json()["content"][0]["text"]


async def _call_gemini_chat(messages: list[dict], model: str, api_key: str) -> str:
    """Multi-turn Gemini call for /api/chat (separate from the single-shot
    _call_gemini used by /api/generate-svg's cloud fallback - different
    request shapes, don't conflate the two callers)."""
    system = "\n".join(m["content"] for m in messages if m.get("role") == "system")
    contents = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
        for m in messages
        if m.get("role") in ("user", "assistant")
    ]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model or 'gemini-3.5-flash-lite'}:generateContent?key={api_key}"
    )
    payload: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }
    if system:
        payload["system_instruction"] = {"parts": [{"text": system}]}
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
    candidates = r.json().get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts)


async def _call_anthropic_chat(messages: list[dict], model: str, api_key: str) -> str:
    """Multi-turn Anthropic call for /api/chat (see _call_gemini_chat note)."""
    system = "\n".join(m["content"] for m in messages if m.get("role") == "system")
    turns = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
        if m.get("role") in ("user", "assistant")
    ]
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model or "claude-haiku-4-5-20251001",
                "max_tokens": 8192,
                "system": system,
                "messages": turns or [{"role": "user", "content": ""}],
            },
        )
        r.raise_for_status()
    content = r.json().get("content", [])
    return "".join(c.get("text", "") for c in content if c.get("type") == "text")


# OpenAI, DeepSeek, OpenRouter, and Meta's Model API are all OpenAI-compatible
# /chat/completions - one shared implementation instead of four near-duplicates.
async def _call_openai_compatible(
    prompt: str, system: str, *, base_url: str, api_key: str, model: str
) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 8192,
                "temperature": 0.7,
            },
        )
        r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


async def _call_openai_compatible_chat(
    messages: list[dict], model: str, *, base_url: str, api_key: str
) -> str:
    """Multi-turn call for /api/chat (see _call_gemini_chat note) - unlike
    Gemini/Anthropic, OpenAI-compatible APIs take system+user+assistant all
    in one `messages` array, so no separate system extraction is needed."""
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": m["role"], "content": m["content"]}
                    for m in messages
                    if m.get("role") in ("system", "user", "assistant")
                ],
                "max_tokens": 8192,
                "temperature": 0.7,
            },
        )
        r.raise_for_status()
    choices = r.json().get("choices", [])
    return choices[0]["message"]["content"] if choices else ""


async def _call_openai(prompt: str, system: str) -> str:
    api_key = _env("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return await _call_openai_compatible(
        prompt, system, base_url="https://api.openai.com/v1", api_key=api_key, model="gpt-6-luna"
    )


async def _call_openai_chat(messages: list[dict], model: str, api_key: str) -> str:
    return await _call_openai_compatible_chat(
        messages, model or "gpt-6-luna", base_url="https://api.openai.com/v1", api_key=api_key
    )


async def _call_deepseek(prompt: str, system: str) -> str:
    api_key = _env("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not set")
    return await _call_openai_compatible(
        prompt, system, base_url="https://api.deepseek.com", api_key=api_key, model="deepseek-flash"
    )


async def _call_deepseek_chat(messages: list[dict], model: str, api_key: str) -> str:
    return await _call_openai_compatible_chat(
        messages, model or "deepseek-flash", base_url="https://api.deepseek.com", api_key=api_key
    )


async def _call_openrouter(prompt: str, system: str) -> str:
    api_key = _env("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")
    return await _call_openai_compatible(
        prompt,
        system,
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model="openai/gpt-6-luna",
    )


async def _call_openrouter_chat(messages: list[dict], model: str, api_key: str) -> str:
    return await _call_openai_compatible_chat(
        messages,
        model or "openai/gpt-6-luna",
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


async def _call_meta(prompt: str, system: str) -> str:
    """Meta Model API (Muse Spark). Deliberately NOT part of the automatic
    generate_svg fallback chain (see _generate_svg) - the cheap "-contributor"
    model variants opt prompts/completions into Meta's training pipeline, a
    consent decision that should never be made silently by an env var alone.
    This function exists for the explicit, user-driven /api/chat path only,
    where the model id (and its training-data implications) is visible and
    chosen in AI Settings, not auto-selected."""
    api_key = _env("MODEL_API_KEY")
    if not api_key:
        raise ValueError("MODEL_API_KEY not set")
    return await _call_openai_compatible(
        prompt, system, base_url="https://api.meta.ai/v1", api_key=api_key, model="muse-spark-1.3"
    )


async def _call_meta_chat(messages: list[dict], model: str, api_key: str) -> str:
    return await _call_openai_compatible_chat(
        messages, model or "muse-spark-1.3", base_url="https://api.meta.ai/v1", api_key=api_key
    )


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

    # 1. Ollama (local - primary, free)
    try:
        raw = await _call_ollama(user_p, _SVG_SYSTEM)
        model_used = f"ollama/{_ollama_model()}"
        logger.info("SVG generated via Ollama (%s)", _ollama_model())
    except Exception as ollama_err:
        logger.warning("Ollama unavailable (%s), trying cloud fallbacks", ollama_err)
        # 2. Cloud fallbacks, cheapest-first. Meta's Muse Spark is deliberately
        # excluded here - see _call_meta's docstring on the contributor tier's
        # training-data consent tradeoff, which must be an explicit user
        # choice (AI Settings' /api/chat path), never an automatic fallback.
        cloud_fallbacks = [
            ("GEMINI_API_KEY", "gemini-3.5-flash-lite", _call_gemini),
            ("OPENAI_API_KEY", "gpt-6-luna", _call_openai),
            ("DEEPSEEK_API_KEY", "deepseek-flash", _call_deepseek),
            ("ANTHROPIC_API_KEY", "claude-haiku-4-5-20251001", _call_anthropic),
            ("OPENROUTER_API_KEY", "openai/gpt-6-luna (via OpenRouter)", _call_openrouter),
        ]
        raw = None
        model_used = ""
        cloud_errors: list[str] = []
        tried_any = False
        for env_var, label, caller in cloud_fallbacks:
            if not _env(env_var):
                continue
            tried_any = True
            try:
                raw = await caller(user_p, _SVG_SYSTEM)
                model_used = label
                break
            except Exception as cloud_err:
                # A configured-but-broken provider (bad/rejected key, quota,
                # outage) must not abort the whole chain - that was the bug
                # here before: Gemini alone failing 403'd the entire request
                # even though OpenAI/DeepSeek/Anthropic/OpenRouter keys were
                # also configured and never got a turn.
                logger.warning("%s fallback failed (%s), trying next", label, cloud_err)
                cloud_errors.append(f"{label}: {cloud_err}")
        if raw is None:
            if not tried_any:
                raise ValueError(
                    f"Ollama unreachable ({ollama_err}) and no cloud API keys configured. "
                    "Check that Ollama is running (ollama serve), or set one of GEMINI_API_KEY, "
                    "OPENAI_API_KEY, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY."
                ) from ollama_err
            raise ValueError(
                f"Ollama unreachable ({ollama_err}) and every configured cloud provider failed: "
                + "; ".join(cloud_errors)
            ) from ollama_err

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
            f"SVG parse error - raw response length: {len(raw)} chars"
            f"</text></svg>"
        )
    return svg, model_used


# ── Inkscape CLI save ─────────────────────────────────────────────────────────


async def _save_via_inkscape(svg_xml: str, stem: str, inkscape_exe: str | None) -> str | None:
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


async def _call_mcp_tool(mcp: Any, tool_name: str, params: dict) -> dict[str, Any]:
    """Call an MCP tool and normalize FastMCP's ToolResult into
    {success, data, error} - shared by /v1/tool and the agentic chat
    tool-calling loop so there is exactly one place that understands
    to_mcp_result()'s three possible shapes.

    result.to_mcp_result() returns one of:
      - a CallToolResult (has .isError) - the only shape that actually
        carries an error flag.
      - a (content, structured_content) tuple - NEVER an error path per
        FastMCP's ToolResult.to_mcp_result(); structured_content is a
        dict, not a bool, so it must never be read as an is_error flag
        (a truthy dict would always look like an error - this was a real
        bug here before: every successful tool call with data reported
        as failed).
      - a bare content list.
    """
    try:
        result = await mcp.call_tool(str(tool_name), params)
    except Exception as exc:
        logger.exception("Tool %s failed: %s", tool_name, exc)
        return {"success": False, "data": None, "error": str(exc)}

    mcp_result = result.to_mcp_result()
    is_error = False
    content_list: list[Any] = []
    structured_content: Any = None
    if hasattr(mcp_result, "isError"):
        is_error = bool(mcp_result.isError)
        content_list = getattr(mcp_result, "content", None) or []
        structured_content = getattr(mcp_result, "structuredContent", None)
    elif isinstance(mcp_result, tuple) and len(mcp_result) >= 2:
        content_list, structured_content = mcp_result[0], mcp_result[1]
    else:
        content_list = (
            mcp_result if isinstance(mcp_result, list) else getattr(result, "content", [])
        )

    data: Any = structured_content
    error_text: str | None = None
    if content_list:
        text = getattr(content_list[0], "text", str(content_list[0]))
        if data is None:
            try:
                data = json.loads(text)
            except Exception:
                data = {"output": text}
        if is_error:
            error_text = text

    return {
        "success": not is_error and data is not None,
        "data": data,
        "error": None if not is_error else (error_text or "Tool returned error"),
    }


async def _ollama_tool_schemas(mcp: Any) -> list[dict[str, Any]]:
    """Ollama-format (OpenAI-style) function-tool schemas for every
    registered MCP tool, so the chat tool-calling loop and MCP clients
    expose the same surface - reuses list_tools(), the same call /api/health
    already makes for its tool_count."""
    try:
        raw_tools = await mcp.list_tools()
    except Exception:
        logger.warning("list_tools() failed while building chat tool schemas", exc_info=True)
        return []
    schemas: list[dict[str, Any]] = []
    for t in raw_tools:
        try:
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": (t.description or "")[:1000],
                        "parameters": t.parameters,
                    },
                }
            )
        except Exception:
            continue
    return schemas


# ── Streaming chat helpers ────────────────────────────────────────────────────


class _AgenticEvent:
    """SSE event types for streaming chat."""

    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DONE = "done"


async def _stream_ollama_raw(
    client: httpx.AsyncClient,
    endpoint: str,
    model: str,
    messages: list[dict],
    tools: list[dict] | None = None,
) -> AsyncGenerator[tuple[str, Any], None]:
    """Yields ("text", chunk) for content deltas, or ("tool_calls", list)
    once when the model wants to call tools instead of answering. Ollama
    delivers tool_calls on the final streamed line (done=true), not
    incrementally piece by piece the way OpenAI-style deltas work - so this
    stops yielding text and returns as soon as a line carries them."""
    payload: dict[str, Any] = {"model": model, "messages": messages, "stream": True}
    if tools:
        payload["tools"] = tools
    async with client.stream(
        "POST",
        f"{endpoint}/api/chat",
        json=payload,
        timeout=120,
    ) as r:
        async for line in r.aiter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = data.get("message") or {}
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                yield ("tool_calls", tool_calls)
                return
            chunk = msg.get("content", "")
            if chunk:
                yield ("text", chunk)


async def _stream_lmstudio_raw(
    client: httpx.AsyncClient, endpoint: str, model: str, messages: list[dict]
) -> AsyncGenerator[tuple[str, Any], None]:
    """Yields ("text", chunk) tuples - same tagged shape as
    _stream_ollama_raw for a uniform caller, though LM Studio never yields
    ("tool_calls", ...): tool calling is Ollama-only here (see _event_stream)."""
    async with client.stream(
        "POST",
        f"{endpoint}/v1/chat/completions",
        json={"messages": messages, "model": model, "temperature": 0.7, "stream": True},
        timeout=120,
    ) as r:
        async for line in r.aiter_lines():
            if not line.startswith("data: "):
                continue
            chunk = line[6:]
            if chunk == "[DONE]":
                break
            try:
                data = json.loads(chunk)
                delta = data["choices"][0].get("delta", {}).get("content", "")
                if delta:
                    yield ("text", delta)
            except json.JSONDecodeError:
                pass


# ── FastAPI app factory ───────────────────────────────────────────────────────


def register_rest_api(mcp: Any, config: Any | None = None) -> None:
    """Attach /api/* REST layer to the FastMCP 3.1 HTTP server."""
    if not FASTAPI_AVAILABLE:
        logger.warning("fastapi/httpx not installed - REST API bridge unavailable.")
        return
    if not hasattr(mcp, "_additional_http_routes"):
        logger.warning("FastMCP has no _additional_http_routes - REST bridge unavailable.")
        return

    # Grab Inkscape path from config if available
    inkscape_exe: str | None = None
    if config and hasattr(config, "inkscape_executable"):
        inkscape_exe = config.inkscape_executable

    app = FastAPI(title="Inkscape MCP REST Bridge", version="2.6.0")
    _start_time = datetime.now(UTC)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:11027",
            "http://localhost:11028",
            "http://127.0.0.1:11029",
            "http://localhost:11029",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    _attach_memory_logging()

    from .services.apps_routes import register_apps_routes

    _apps_router = APIRouter(prefix="/api")
    register_apps_routes(_apps_router)
    app.include_router(_apps_router)

    from .services.depot_routes import register_depot_routes

    async def _depot_call_tool(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        return await _call_mcp_tool(mcp, tool_name, params)

    _depot_router = APIRouter(prefix="/api")
    register_depot_routes(_depot_router, _depot_call_tool)
    app.include_router(_depot_router)

    @app.get("/api/logs")
    async def api_logs(
        limit: int = 400,
        offset: int = 0,
        level: str = "",
        kind: str = "",
        search: str = "",
        sort: str = "desc",
        after_id: str = "",
    ) -> dict:
        limit = max(1, min(limit, MAX_MEMORY_LOGS))
        with _memory_lock:
            logs = list(_memory_logs)
        logs = _filter_logs(logs, level=level, kind=kind, search=search)

        if after_id:
            idx = next((i for i, e in enumerate(logs) if e.get("id") == after_id), None)
            tail = logs[idx + 1 :] if idx is not None else []
            return {"logs": tail, "returned": len(tail), "total": len(logs)}

        total = len(logs)
        ordered = list(reversed(logs)) if sort != "asc" else logs
        page = ordered[offset : offset + limit]
        return {"logs": page, "returned": len(page), "total": total}

    @app.get("/api/logs/export")
    async def api_logs_export(
        format: str = "json",
        level: str = "",
        kind: str = "",
        search: str = "",
    ) -> Response:
        with _memory_lock:
            logs = list(_memory_logs)
        logs = _filter_logs(logs, level=level, kind=kind, search=search)

        if format == "csv":
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["id", "timestamp", "level", "kind", "detail"])
            for e in logs:
                writer.writerow(
                    [
                        e.get("id", ""),
                        e.get("timestamp", ""),
                        e.get("level", ""),
                        e.get("kind", ""),
                        e.get("detail", ""),
                    ]
                )
            return Response(
                content=buf.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": 'attachment; filename="logs.csv"'},
            )

        return JSONResponse(
            {"logs": logs, "total": len(logs)},
            headers={"Content-Disposition": 'attachment; filename="logs.json"'},
        )

    @app.delete("/api/logs")
    async def api_logs_clear() -> dict:
        with _memory_lock:
            _memory_logs.clear()
        logger.info("REST: log buffer cleared (DELETE /api/logs)")
        return {"ok": True}

    @app.get("/api/help")
    async def api_help() -> dict:
        return _help_payload()

    @app.get("/api/docs/{path:path}")
    async def api_docs(path: str) -> PlainTextResponse:
        """Serve markdown files from the docs/ directory for the webapp help page."""
        # Security: only allow .md files, reject absolute paths and parent traversal
        if not path.endswith(".md") or ".." in path or path.startswith("/"):
            return PlainTextResponse("Not found", status_code=404)
        # Try repo-root docs/ first, then repo root
        for base in [Path(inkscape_exe).parent.parent if inkscape_exe else Path.cwd(), Path.cwd()]:
            md_file = base / "docs" / path
            if md_file.exists():
                return PlainTextResponse(md_file.read_text(encoding="utf-8", errors="replace"))
            md_file = base / path
            if md_file.exists():
                return PlainTextResponse(md_file.read_text(encoding="utf-8", errors="replace"))
        return PlainTextResponse("Not found", status_code=404)

    @app.post("/api/chat", response_model=None)
    async def api_chat(request: Request):
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        query = str(payload.get("query") or payload.get("message", ""))
        provider = str(payload.get("provider") or "ollama")
        model = str(payload.get("model") or "")
        endpoint = str(payload.get("endpoint") or _ollama_base()).rstrip("/")
        system_prompt = str(payload.get("system_prompt", ""))
        stream = bool(payload.get("stream", False))
        mode = str(payload.get("mode", "llm"))
        history = payload.get("history", [])
        if not isinstance(history, list):
            history = []

        logger.info(
            "REST: /api/chat (query=%r, provider=%s, stream=%s, mode=%s)",
            query[:60],
            provider,
            stream,
            mode,
        )

        if not query:
            return {"reply": "", "status": "error"}

        # SETTINGS_LLM.md rule 6: send-time guard. No fallback model, ever -
        # an empty selection means the user hasn't picked one in Settings yet.
        if not model:
            return {"reply": "Pick a model in Settings before chatting.", "status": "error"}

        if not stream:
            return {"reply": "Streaming is required for chat. Set stream=true.", "status": "error"}

        async def _event_stream():
            msgs: list[dict] = []
            if system_prompt:
                msgs.append({"role": "system", "content": system_prompt})
            for h in history:
                msgs.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            msgs.append({"role": "user", "content": query})

            _cloud_chat_callers = {
                "gemini": _call_gemini_chat,
                "anthropic": _call_anthropic_chat,
                "openai": _call_openai_chat,
                "deepseek": _call_deepseek_chat,
                "openrouter": _call_openrouter_chat,
                "meta": _call_meta_chat,
            }
            if provider in _cloud_chat_callers:
                api_key = llm_settings_store.get_key(provider)
                if not api_key:
                    yield f"data: {json.dumps({'type': _AgenticEvent.TEXT, 'content': f'No API key configured for {provider}. Add one in AI Settings.'})}\n\n"
                    yield f"data: {json.dumps({'type': _AgenticEvent.DONE})}\n\n"
                    return
                try:
                    caller = _cloud_chat_callers[provider]
                    text = await caller(msgs, model, api_key)
                except Exception as exc:
                    text = f"{provider} request failed: {exc}"
                yield f"data: {json.dumps({'type': _AgenticEvent.TEXT, 'content': text})}\n\n"
            else:
                # Agentic tool-calling loop (Ollama only - it's the only
                # provider here whose streaming API surfaces tool_calls;
                # LM Studio's OpenAI-style streaming would need incremental
                # partial-JSON delta assembly across chunks, a materially
                # different and harder problem, not implemented). This is
                # what chat.tsx's tool_call/tool_result SSE handling and its
                # tool-call cards were originally built for but never
                # received - _AgenticEvent.TOOL_CALL was defined and the
                # frontend UI built around it, but nothing server-side ever
                # yielded one.
                tools_schema = await _ollama_tool_schemas(mcp) if provider == "ollama" else None
                max_rounds = 4
                async with httpx.AsyncClient(timeout=120.0) as client:
                    for _round in range(max_rounds):
                        pending_tool_calls: list[dict] | None = None
                        generator = (
                            _stream_lmstudio_raw(client, endpoint, model, msgs)
                            if provider == "lmstudio"
                            else _stream_ollama_raw(
                                client, endpoint, model, msgs, tools=tools_schema or None
                            )
                        )
                        async for kind, item in generator:
                            if kind == "text":
                                yield f"data: {json.dumps({'type': _AgenticEvent.TEXT, 'content': item})}\n\n"
                            elif kind == "tool_calls":
                                pending_tool_calls = item

                        if not pending_tool_calls:
                            break

                        msgs.append(
                            {"role": "assistant", "content": "", "tool_calls": pending_tool_calls}
                        )
                        for tc in pending_tool_calls:
                            fn = (tc or {}).get("function") or {}
                            tool_name = str(fn.get("name") or "")
                            raw_args = fn.get("arguments")
                            if isinstance(raw_args, str):
                                try:
                                    args = json.loads(raw_args) if raw_args else {}
                                except Exception:
                                    args = {}
                            elif isinstance(raw_args, dict):
                                args = raw_args
                            else:
                                args = {}

                            nl_name = tool_name.replace("_", " ").title() or "Tool"
                            yield f"data: {json.dumps({'type': _AgenticEvent.TOOL_CALL, 'tool': tool_name, 'nl_name': nl_name})}\n\n"

                            t0 = time.monotonic()
                            if tool_name:
                                outcome = await _call_mcp_tool(mcp, tool_name, args)
                            else:
                                outcome = {
                                    "success": False,
                                    "data": None,
                                    "error": "model returned an empty tool name",
                                }
                            timing_ms = round((time.monotonic() - t0) * 1000, 1)

                            result_obj = {
                                "success": outcome["success"],
                                "tool": tool_name,
                                "params": args,
                                "result": json.dumps(outcome["data"])
                                if outcome["success"]
                                else None,
                                "error": None
                                if outcome["success"]
                                else (outcome["error"] or "Tool failed"),
                                "timing_ms": timing_ms,
                            }
                            yield f"data: {json.dumps({'type': _AgenticEvent.TOOL_RESULT, 'tool': tool_name, 'result': result_obj})}\n\n"

                            msgs.append(
                                {
                                    "role": "tool",
                                    "tool_name": tool_name,
                                    "content": json.dumps(
                                        outcome["data"]
                                        if outcome["success"]
                                        else {"error": outcome["error"]}
                                    ),
                                }
                            )
                    else:
                        yield f"data: {json.dumps({'type': _AgenticEvent.TEXT, 'content': '(stopped after several tool calls without a final answer - try rephrasing)'})}\n\n"

            yield f"data: {json.dumps({'type': _AgenticEvent.DONE})}\n\n"

        return StreamingResponse(
            _event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # ── /api/llm/* (SETTINGS_LLM.md contract: local + cloud, no-auto-pick) ────
    # models_path/tag_style let _live_cloud_models probe each vendor's real
    # model-list endpoint instead of only ever returning the curated stand-in
    # (mcp-central-docs/templates/llm: GET /llm/models must return `live` when
    # keyed, `curated` + key_missing when not - inkscape-mcp had drifted to
    # curated-always with no key_missing flag, which is exactly the BUG-042
    # "Test lies" shape the template calls out).
    _cloud_providers = {
        "gemini": {
            "label": "Gemini",
            "base_url": "https://generativelanguage.googleapis.com",
            "models_path": "/v1beta/models",
            "tag_style": "gemini",
        },
        "anthropic": {
            "label": "Anthropic",
            "base_url": "https://api.anthropic.com",
            "models_path": "/v1/models",
            "tag_style": "anthropic",
        },
        "openai": {
            "label": "OpenAI",
            "base_url": "https://api.openai.com",
            "models_path": "/v1/models",
            "tag_style": "openai",
        },
        "deepseek": {
            "label": "DeepSeek",
            "base_url": "https://api.deepseek.com",
            "models_path": "/models",
            "tag_style": "openai",
        },
        "openrouter": {
            "label": "OpenRouter",
            "base_url": "https://openrouter.ai/api",
            "models_path": "/v1/models",
            "tag_style": "openai",
        },
        # MODEL_API_KEY matches Meta's own documented env var name for the
        # Model API, not a fleet-internal choice - see llm_settings_store.KEY_ENV.
        "meta": {
            "label": "Meta (Muse Spark)",
            "base_url": "https://api.meta.ai",
            "models_path": "/v1/models",
            "tag_style": "openai",
        },
    }
    # Curated fallback lists - shown unkeyed (key_missing=True) and used if a
    # keyed live probe fails.
    _cloud_curated_models = {
        "gemini": ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.1-pro-preview"],
        "anthropic": ["claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-5-5"],
        "openai": ["gpt-6-luna", "gpt-6-sol"],
        "deepseek": ["deepseek-flash", "deepseek-v4-pro"],
        "openrouter": [
            "openai/gpt-6-luna",
            "deepseek/deepseek-flash",
            "google/gemini-3.5-flash-lite",
        ],
        # "-contributor" is not a cosmetic suffix: selecting it opts your
        # prompts/completions into Meta's training pipeline in exchange for
        # ~10-20x lower cost (see _call_meta's docstring). Kept as the exact,
        # unmodified API model id here - do not decorate this string, it is
        # sent verbatim as the `model` field. Surface the tradeoff in the UI
        # label, not in the id.
        "meta": ["muse-spark-1.3", "muse-spark-1.3-contributor"],
    }

    def _cloud_auth(provider_id: str, api_key: str) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if provider_id == "anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        elif provider_id == "openrouter":
            headers["Authorization"] = f"Bearer {api_key}"
            headers["HTTP-Referer"] = "http://127.0.0.1:11027/"
            headers["X-Title"] = "inkscape-mcp"
        elif provider_id != "gemini":
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _parse_model_list(tag_style: str, payload: Any) -> list[str]:
        if not isinstance(payload, dict):
            return []
        if tag_style == "gemini":
            models = payload.get("models") or []
            return [
                m["name"].removeprefix("models/")
                for m in models
                if isinstance(m, dict) and m.get("name")
            ]
        data = payload.get("data") or []
        return [m.get("id", "") for m in data if isinstance(m, dict) and m.get("id")]

    async def _live_cloud_models(provider_id: str, api_key: str) -> dict[str, Any]:
        """Model list with source flag - live when keyed and reachable, else
        curated + key_missing=True. api_key overrides the stored/env key for
        this call only (never persisted) so Test can validate a typed key."""
        row = _cloud_providers[provider_id]
        key = (api_key or "").strip() or llm_settings_store.get_key(provider_id) or ""
        if not key:
            return {
                "provider": provider_id,
                "models": list(_cloud_curated_models.get(provider_id, [])),
                "source": "curated",
                "key_missing": True,
                "note": "Save a key for the live list. Curated names still work once keyed.",
            }
        url = row["base_url"] + row["models_path"]
        if provider_id == "gemini":
            url += f"?key={key}"
        headers = _cloud_auth(provider_id, key)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
                models = _parse_model_list(row["tag_style"], r.json())
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            error = (
                f"{row['label']} rejected the key (HTTP {status}) - check the key, then Save and Test again."
                if status in (401, 403)
                else f"{row['label']} HTTP {status}."
            )
            return {
                "provider": provider_id,
                "models": list(_cloud_curated_models.get(provider_id, [])),
                "source": "curated",
                "error": error,
            }
        except Exception as exc:
            logger.warning("live model list for %s failed (%s); curated fallback", provider_id, exc)
            return {
                "provider": provider_id,
                "models": list(_cloud_curated_models.get(provider_id, [])),
                "source": "curated",
            }
        if not models:
            return {
                "provider": provider_id,
                "models": list(_cloud_curated_models.get(provider_id, [])),
                "source": "curated",
            }
        return {"provider": provider_id, "models": models, "source": "live"}

    async def _probe_ollama() -> tuple[bool, list[str]]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as c:
                r = await c.get(f"{_ollama_base()}/api/tags")
                if r.status_code == 200:
                    return True, [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return False, []

    async def _probe_lmstudio() -> tuple[bool, list[str]]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as c:
                r = await c.get("http://127.0.0.1:1234/v1/models")
                if r.status_code == 200:
                    return True, [m["id"] for m in r.json().get("data", [])]
        except Exception:
            pass
        return False, []

    @app.get("/api/llm/providers")
    async def llm_providers() -> dict:
        ollama_ok, ollama_models = await _probe_ollama()
        lm_ok, lm_models = await _probe_lmstudio()
        providers: list[dict] = [
            {
                "id": "ollama",
                "label": "Ollama",
                "kind": "local",
                "base_url": _ollama_base(),
                "needs_key": False,
                "key_env": None,
                "configured": True,
                "detected": ollama_ok,
                "models": ollama_models,
            },
            {
                "id": "lmstudio",
                "label": "LM Studio",
                "kind": "local",
                "base_url": "http://127.0.0.1:1234",
                "needs_key": False,
                "key_env": None,
                "configured": True,
                "detected": lm_ok,
                "models": lm_models,
            },
        ]
        for pid, info in _cloud_providers.items():
            providers.append(
                {
                    "id": pid,
                    "label": info["label"],
                    "kind": "cloud",
                    "base_url": info["base_url"],
                    "needs_key": True,
                    "key_env": llm_settings_store.KEY_ENV.get(pid),
                    "configured": llm_settings_store.has_key(pid),
                    "models": _cloud_curated_models.get(pid, []),
                }
            )
        return {"providers": providers}

    @app.get("/api/llm/models")
    async def llm_models(provider: str = "ollama") -> dict:
        if provider == "ollama":
            _, models = await _probe_ollama()
            return {"provider": provider, "models": models, "source": "live" if models else "none"}
        if provider == "lmstudio":
            _, models = await _probe_lmstudio()
            return {"provider": provider, "models": models, "source": "live" if models else "none"}
        if provider not in _cloud_providers:
            return {"provider": provider, "models": [], "source": "none"}
        return await _live_cloud_models(provider, "")

    @app.post("/api/llm/test")
    async def llm_test(request: Request):
        """Validate a provider without saving anything (mcp-central-docs
        templates/llm/INTEGRATION.md contract). `ok` is true only for a live
        list - curated names without a key come back ok:false + key_missing
        so the UI never reports an unkeyed provider as a successful test
        (BUG-042: giskard-mcp 2026-09-21, "N models found" for no key)."""
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        provider = str(payload.get("provider") or "")
        api_key = str(payload.get("api_key") or "")

        if provider in ("ollama", "lmstudio"):
            _, models = await (_probe_ollama() if provider == "ollama" else _probe_lmstudio())
            return {
                "success": True,
                "ok": bool(models),
                "provider": provider,
                "models": models,
                "source": "live" if models else "none",
            }
        if provider not in _cloud_providers:
            return JSONResponse(
                {"success": False, "error": f"Unknown provider '{provider}'"}, status_code=400
            )
        result = await _live_cloud_models(provider, api_key)
        ok = result.get("source") == "live" and len(result.get("models", [])) > 0
        return {"success": True, "ok": ok, **result}

    @app.get("/api/llm/gpus")
    async def llm_gpus() -> dict:
        return {"gpus": llm_engine.gpu_vram()}

    @app.get("/api/llm/loaded")
    async def llm_loaded(provider: str = "ollama", endpoint: str = "") -> dict:
        if provider != "ollama":
            return {"success": True, "engine": False, "models": []}
        data = await llm_engine.ollama_loaded(endpoint or _ollama_base())
        return {"success": True, **data}

    @app.post("/api/llm/unload")
    async def llm_unload(request: Request) -> dict:
        payload = await request.json()
        provider = str(payload.get("provider") or "ollama")
        endpoint = str(payload.get("endpoint") or "") or _ollama_base()
        if provider != "ollama":
            return {"success": False, "evicted": []}
        result = await llm_engine.switch_ollama_model("", endpoint)
        return {"success": True, "evicted": result["evicted"]}

    @app.get("/api/settings/llm")
    async def get_llm_settings() -> dict:
        data = llm_settings_store.load_settings()
        return {
            "provider": data.get("provider"),
            "endpoint": data.get("endpoint"),
            "model": data.get("model"),
        }

    @app.post("/api/settings/llm", response_model=None)
    async def save_llm_settings(request: Request) -> dict | JSONResponse:
        payload = await request.json()
        provider = str(payload.get("provider") or "").strip()
        model = str(payload.get("model") or "").strip()
        endpoint = payload.get("endpoint")
        api_key = payload.get("api_key")
        # BUG-043 (giskard-mcp 2026-09-21): a card's "Save key" must attach the
        # key to its own provider without hijacking whatever provider/model is
        # currently active. Default true keeps the explicit "pick this as my
        # active pair" flow (Settings' active-pair row) working unchanged.
        select = payload.get("select", True)
        if not provider:
            return JSONResponse({"success": False, "error": "provider required"}, status_code=400)

        key_saved = False
        if api_key:
            llm_settings_store.save_key(provider, str(api_key))
            key_saved = True

        result: dict[str, Any] = {"success": True}
        if key_saved:
            result["key_saved"] = True
        if select:
            llm_settings_store.save_settings(provider, endpoint, model)
            # Save switches VRAM, not just config (SETTINGS_LLM.md rule 4) -
            # only meaningful for the local Ollama engine.
            if provider == "ollama":
                switch = await llm_engine.switch_ollama_model(model, endpoint or _ollama_base())
                result["switch"] = switch
        return result

    @app.delete("/api/settings/llm/key")
    async def delete_llm_key(provider: str) -> dict:
        llm_settings_store.clear_key(provider)
        return {"success": True}

    @app.get("/api/settings/server")
    async def get_server_settings() -> dict:
        """Effective values for the handful of things Settings' old
        "Configure outside this UI" card told users to hand-edit an env var
        for. `source` says where each value actually came from, so the UI
        can show e.g. "env" vs "saved override" vs "default"."""
        saved = server_settings.load()

        inkscape_path = (config.inkscape_executable if config else None) or ""
        inkscape_source = (
            "saved" if saved.get("inkscape_path") else ("detected" if inkscape_path else "none")
        )

        ollama_url_env = _env("OLLAMA_BASE_URL", "")
        ollama_source = (
            "saved" if saved.get("ollama_base_url") else ("env" if ollama_url_env else "default")
        )

        ollama_model_env = _env("OLLAMA_MODEL", "")
        ollama_model_source = (
            "saved" if saved.get("ollama_model") else ("env" if ollama_model_env else "default")
        )

        port_env = _env("MCP_PORT", "")
        return {
            "inkscape_path": {"value": inkscape_path, "source": inkscape_source},
            "ollama_base_url": {"value": _ollama_base(), "source": ollama_source},
            "ollama_model": {"value": _ollama_model(), "source": ollama_model_source},
            "mcp_port": {
                "value": saved.get("mcp_port") or port_env or "11028",
                "source": "saved" if saved.get("mcp_port") else ("env" if port_env else "default"),
                "note": "Takes effect on next restart - this page is itself served on the current port.",
            },
        }

    @app.post("/api/settings/server")
    async def save_server_settings(request: Request):
        """inkscape_path/ollama_base_url/ollama_model take effect immediately
        (mutating the live, shared InkscapeConfig / read fresh by
        _ollama_base/_ollama_model on every call). mcp_port is saved for the
        next start only - restart_required is always true for it."""
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}

        inkscape_path = str(payload.get("inkscape_path") or "").strip()
        if inkscape_path:
            if not Path(inkscape_path).exists():
                return JSONResponse(
                    {"success": False, "error": f"File not found: {inkscape_path}"}, status_code=400
                )
            if config is not None:
                config.inkscape_executable = inkscape_path

        fields: dict[str, Any] = {}
        if "inkscape_path" in payload:
            fields["inkscape_path"] = inkscape_path or None
        if "ollama_base_url" in payload:
            fields["ollama_base_url"] = str(payload.get("ollama_base_url") or "").strip() or None
        if "ollama_model" in payload:
            fields["ollama_model"] = str(payload.get("ollama_model") or "").strip() or None
        if "mcp_port" in payload:
            raw_port = payload.get("mcp_port")
            fields["mcp_port"] = str(int(raw_port)) if raw_port else None

        saved = server_settings.save(**fields)
        return {
            "success": True,
            "saved": saved,
            "restart_required": "mcp_port" in fields and fields["mcp_port"] is not None,
        }

    @app.get("/api/llm/onboarding")
    async def llm_onboarding() -> dict:
        ollama_ok, ollama_models = await _probe_ollama()
        lm_ok, _ = await _probe_lmstudio()
        locals_ = [
            {"id": "ollama", "label": "Ollama", "port": 11434},
            {"id": "lmstudio", "label": "LM Studio", "port": 1234},
        ]
        clouds_configured = [pid for pid in _cloud_providers if llm_settings_store.has_key(pid)]
        if ollama_ok:
            recommendation = {
                "path": "local:ollama",
                "reason": f"Ollama detected with {len(ollama_models)} model(s) - free, local, no key needed.",
            }
        elif lm_ok:
            recommendation = {
                "path": "local:lmstudio",
                "reason": "LM Studio detected - free, local, no key needed.",
            }
        elif clouds_configured:
            recommendation = {
                "path": f"cloud:{clouds_configured[0]}",
                "reason": "A cloud key is already configured.",
            }
        else:
            recommendation = {
                "path": "cloud:gemini",
                "reason": "No local engine detected. Gemini, OpenAI (gpt-6-luna), and DeepSeek all have "
                "cheap instant paths if you'd rather not install anything - pick whichever you already have a key for.",
            }
        return {
            "locals": locals_,
            "clouds_configured": clouds_configured,
            "recommendation": recommendation,
        }

    _install_state: dict[str, dict[str, Any]] = {}

    @app.post("/api/llm/install")
    async def llm_install(request: Request) -> dict:
        payload = await request.json()
        engine = str(payload.get("engine") or "")
        if engine != "ollama":
            return {
                "engine": engine,
                "started": False,
                "reason": "only 'ollama' is installable from here",
            }
        _install_state["ollama"] = {"state": "running", "output": ""}

        async def _run() -> None:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "winget",
                    "install",
                    "-e",
                    "--id",
                    "Ollama.Ollama",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                out, _ = await proc.communicate()
                _install_state["ollama"] = {
                    "state": "done" if proc.returncode == 0 else "error",
                    "output": (out or b"").decode(errors="replace")[-2000:],
                }
            except Exception as exc:
                _install_state["ollama"] = {"state": "error", "output": str(exc)}

        asyncio.create_task(_run())
        return {"engine": engine, "started": True}

    @app.get("/api/llm/install/status")
    async def llm_install_status(engine: str = "ollama") -> dict:
        st = _install_state.get(engine, {"state": "idle", "output": ""})
        return {"engine": engine, **st}

    # ── /api/health ──────────────────────────────────────────────────────────
    @app.get("/api/health")
    async def health() -> dict:
        ollama_ok = False
        models: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=3.0) as c:
                r = await c.get(f"{_ollama_base()}/api/tags")
                if r.status_code == 200:
                    models = [m["name"] for m in r.json().get("models", [])]
                    ollama_ok = True
        except Exception:
            models = []

        inkscape_path = str(inkscape_exe) if inkscape_exe else None
        ink_available = bool(inkscape_exe and Path(inkscape_exe).exists())
        ink_ver_line: str | None = None
        if ink_available and inkscape_path:
            ink_ver_line = await _inkscape_version_line(inkscape_path)
        ver_t = _inkscape_version_tuple(ink_ver_line)
        actions_api_ok = ver_t is not None and (ver_t[0] > 1 or ver_t[1] >= 2)

        # Build tool list and group by category
        tool_list: list[str] = []
        tool_count = 0
        try:
            raw_tools = await mcp.list_tools()
            tool_list = [t.name for t in raw_tools]
            tool_count = len(tool_list)
        except Exception:
            pass

        tool_groups: list[dict[str, Any]] = []
        try:
            from inkscape_mcp.tools import PORTMANTEAU_TOOLS

            for pt in PORTMANTEAU_TOOLS:
                tool_groups.append(
                    {
                        "name": pt["name"],
                        "category": pt.get("category", pt["name"]),
                        "operations": pt.get("operations", []),
                        "op_count": len(pt.get("operations", [])),
                    }
                )
        except Exception:
            pass

        return {
            "status": "ok",
            "server": "inkscape-mcp",
            "version": "2.6.0",
            "description": "AI-powered vector graphics and SVG editing server. Exposes Inkscape's full feature surface through the Model Context Protocol.",
            "uptime_seconds": int((datetime.now(UTC) - _start_time).total_seconds()),
            "backend_port": int(_env("MCP_PORT", "11028")),
            "tool_count": tool_count,
            "tools": tool_list,
            "tool_groups": tool_groups,
            "providers": {
                "ollama": {
                    "available": ollama_ok,
                    "base_url": _ollama_base(),
                    "model": _ollama_model(),
                    "models": models,
                },
                "inkscape": {
                    "available": ink_available,
                    "path": inkscape_path,
                    "version_line": ink_ver_line,
                    "actions_api_recommended": actions_api_ok,
                },
                "gemini_key": bool(_env("GEMINI_API_KEY")),
                "anthropic_key": bool(_env("ANTHROPIC_API_KEY")),
                "openai_key": bool(_env("OPENAI_API_KEY")),
                "deepseek_key": bool(_env("DEEPSEEK_API_KEY")),
                "openrouter_key": bool(_env("OPENROUTER_API_KEY")),
                "meta_key": bool(_env("MODEL_API_KEY")),
            },
        }

    # ── /api/v1/diagnostics (CUA-NSIS smoke testing standard) ────────────────
    @app.get("/api/v1/diagnostics")
    async def diagnostics() -> dict:
        tools = []
        try:
            raw = await mcp.list_tools()
            tools = [{"name": t.name} for t in raw]
        except Exception:
            pass
        return {
            "status": "ok",
            "server": "inkscape-mcp",
            "version": "2.6.0",
            "uptime_seconds": int((datetime.now(UTC) - _start_time).total_seconds()),
            "tool_count": len(tools),
            "tools": tools,
            "system": {"windows": True},
            "errors": [],
        }

    # ── /api/v1/system/info (CUA-NSIS feature smoke test) ────────────────
    @app.get("/api/v1/system/info")
    async def system_info() -> dict:
        tools = []
        try:
            raw = await mcp.list_tools()
            tools = [{"name": t.name} for t in raw]
        except Exception:
            pass
        return {
            "status": "ok",
            "server": "inkscape-mcp",
            "version": "2.6.0",
            "tool_count": len(tools),
            "tools": tools,
            "system": {"windows": True},
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

            svg_xml, model_used = await _generate_svg(description, style, dimensions, quality)

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

    @app.post("/v1/tool")
    async def api_v1_tool(request: Request) -> JSONResponse:
        """Bridge endpoint for webapp Agent Tools to call MCP tools."""
        try:
            payload = await request.json()
        except Exception as exc:
            return JSONResponse(
                {"success": False, "error": f"Invalid request: {exc}", "data": None},
                status_code=400,
            )

        if not isinstance(payload, dict):
            return JSONResponse(
                {"success": False, "error": "Request body must be a JSON object", "data": None},
                status_code=400,
            )

        tool_name = payload.get("tool")
        params = payload.get("params") or {}
        if not tool_name:
            return JSONResponse(
                {"success": False, "error": "Missing tool name", "data": None},
                status_code=400,
            )
        if not isinstance(params, dict):
            return JSONResponse(
                {"success": False, "error": "params must be an object", "data": None},
                status_code=400,
            )

        outcome = await _call_mcp_tool(mcp, str(tool_name), params)
        return JSONResponse(outcome)

    # ── /api/skills ──────────────────────────────────────────────────────────
    @app.get("/api/skills")
    async def list_skills():
        return {
            "skills": [
                {
                    "name": "inkscape",
                    "description": "Inkscape vector graphics skill - SVG creation, editing, analysis, and export",
                },
            ]
        }

    @app.get("/api/skills/{skill_name}")
    async def get_skill(skill_name: str):
        from pathlib import Path as _Path  # noqa: PLC0415

        skill_path = _Path(__file__).parent / "skills" / "SKILL.md"
        if not skill_path.exists():
            return {"ok": False, "error": "not found"}
        content = skill_path.read_text(encoding="utf-8")
        return {"ok": True, "name": skill_name, "content": content}

    # ── /api/fleet/overview ──────────────────────────────────────────────────
    @app.get("/api/fleet/overview")
    async def fleet_overview():
        return {
            "ships": [
                {
                    "name": "inkscape-mcp",
                    "port": 11028,
                    "status": "running",
                    "category": "Graphics",
                },
                {"name": "gimp-mcp", "port": 10772, "status": "unknown", "category": "Graphics"},
                {"name": "blender-mcp", "port": 10848, "status": "unknown", "category": "3D"},
                {"name": "kicad-mcp", "port": 11016, "status": "unknown", "category": "EDA"},
            ],
            "summary": {"total": 4, "running": 1},
        }

    # ── /api/capabilities ────────────────────────────────────────────────────
    @app.get("/api/capabilities")
    async def capabilities() -> dict:
        from inkscape_mcp.agentic import get_inkscape_file_capabilities  # noqa: PLC0415
        from inkscape_mcp.agentic import get_inkscape_heraldic_capabilities  # noqa: PLC0415
        from inkscape_mcp.agentic import get_inkscape_style_capabilities  # noqa: PLC0415
        from inkscape_mcp.agentic import get_inkscape_vector_capabilities  # noqa: PLC0415
        from inkscape_mcp.agentic import get_svg_generation_approach  # noqa: PLC0415

        return {
            "file": get_inkscape_file_capabilities(),
            "vector": get_inkscape_vector_capabilities(),
            "heraldic": get_inkscape_heraldic_capabilities(),
            "style": get_inkscape_style_capabilities(),
            "generation_approach": get_svg_generation_approach(),
        }

    try:
        mcp._additional_http_routes.append(Mount("", app=app))
        logger.info(
            "REST API bridge mounted at /api  [Ollama: %s/%s]",
            _ollama_base(),
            _ollama_model(),
        )
    except Exception as e:
        logger.warning("Failed to mount REST API bridge: %s", e)
