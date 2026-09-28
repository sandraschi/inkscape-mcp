"""Tools for discovering and managing local LLM models for Inkscape-MCP."""

import logging
from typing import Any
from typing import Literal

import httpx

from ..services import llm_engine

logger = logging.getLogger(__name__)


async def list_local_models() -> dict[str, Any]:
    """Discover local LLM models from Ollama and LM Studio."""
    models = {"ollama": [], "lm_studio": [], "errors": []}

    # Discover Ollama models
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                models["ollama"] = [m["name"] for m in data.get("models", [])]
    except Exception as e:
        logger.debug(f"Ollama discovery failed: {e}")
        models["errors"].append(f"Ollama: {str(e)}")

    # Discover LM Studio models
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:1234/v1/models", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                models["lm_studio"] = [m["id"] for m in data.get("data", [])]
    except Exception as e:
        logger.debug(f"LM Studio discovery failed: {e}")
        models["errors"].append(f"LM Studio: {str(e)}")

    return {
        "success": True,
        "operation": "list_local_models",
        "summary": f"Discovered {len(models['ollama'])} Ollama and {len(models['lm_studio'])} LM Studio models",
        "result": models,
    }


async def llm_ops(
    operation: Literal["list_models", "loaded", "switch_model", "unload_all", "vram"],
    provider: str = "ollama",
    model: str = "",
    endpoint: str = "",
) -> dict[str, Any]:
    """Manage the local LLM engine - shared by both MCP transports and the
    webapp's /v1/tool bridge (services/llm_engine.py), so UI and agents cannot
    drift onto two different switch/evict implementations.

    Ops: list_models (Ollama + LM Studio model IDs) | loaded (Ollama residents
    + VRAM) | switch_model (make `model` the only resident: evict rest, warm
    it) | unload_all (evict everything) | vram (per-GPU telemetry). Only
    Ollama supports loaded/switch/unload - it is the only engine with a
    load/unload API.
    """
    if operation == "list_models":
        data = await list_local_models()
        return {"success": True, "operation": operation, **data.get("result", {})}
    if operation == "vram":
        return {"success": True, "operation": operation, "gpus": llm_engine.gpu_vram()}
    if provider != "ollama":
        return {
            "success": False,
            "message": f"Operation '{operation}' needs the ollama engine.",
            "error": f"unsupported provider '{provider}'",
            "error_type": "ValueError",
            "operation": operation,
            "recovery_options": ["Use provider 'ollama' (local engine)."],
        }
    base = endpoint.rstrip("/") if endpoint else "http://localhost:11434"
    if operation == "loaded":
        data = await llm_engine.ollama_loaded(base)
        return {"success": True, "operation": operation, "provider": provider, **data}
    if operation == "switch_model":
        if not model.strip():
            return {
                "success": False,
                "message": "switch_model needs a model name.",
                "error": "empty model",
                "error_type": "ValueError",
                "operation": operation,
                "recovery_options": [
                    "Call list_models first, then switch to a name from that list."
                ],
            }
        switch = await llm_engine.switch_ollama_model(model.strip(), base)
        return {
            "success": True,
            "operation": operation,
            "provider": provider,
            "model": model.strip(),
            **switch,
        }
    # unload_all
    switch = await llm_engine.switch_ollama_model("", base)
    return {"success": True, "operation": operation, "provider": provider, **switch}
