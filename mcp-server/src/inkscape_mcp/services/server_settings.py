"""Persisted overrides for a few things that otherwise require an env var
edit + restart: INKSCAPE_PATH, OLLAMA_BASE_URL, OLLAMA_MODEL, MCP_PORT.

Same JSON-under-config-dir pattern as llm_settings_store.py. inkscape_path
and the two ollama fields take effect immediately (see app.py's
_ollama_base/_ollama_model and the /api/settings/server POST handler,
which mutates the live, shared InkscapeConfig object). mcp_port cannot -
it is the currently-bound listen port of the process serving this very
request - so it is stored for the *next* start only, and callers must
say so rather than imply it is live.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()
_SETTINGS_PATH = Path.home() / ".config" / "inkscape-mcp" / "server_settings.json"


def _read() -> dict[str, Any]:
    try:
        return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load() -> dict[str, Any]:
    """{inkscape_path?, ollama_base_url?, ollama_model?, mcp_port?}"""
    with _LOCK:
        return _read()


def save(**fields: Any) -> dict[str, Any]:
    """Merge the given fields (None values are removed) and persist."""
    with _LOCK:
        data = _read()
        for key, value in fields.items():
            if value is None or value == "":
                data.pop(key, None)
            else:
                data[key] = value
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
