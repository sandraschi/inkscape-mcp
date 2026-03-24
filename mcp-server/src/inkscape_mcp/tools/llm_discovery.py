"""Tool for discovering local LLM models for Inkscape-MCP."""

import logging
from typing import Any
import httpx

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
