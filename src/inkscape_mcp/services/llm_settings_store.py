"""LLM settings persistence (SETTINGS_LLM.md rule 1: backend file is the
single truth; the frontend's localStorage is a fast-boot mirror only).

Two files under the user's config dir:
  llm_settings.json - {provider, endpoint, model} - the active selection
  llm_keys.json      - {provider: api_key}         - cloud keys, never sent
                        back to the frontend as bytes

Not encrypted at rest (matches other fleet dev-tool key stores); the files
live under the user's own profile, same trust boundary as .env.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()
_SETTINGS_DIR = Path.home() / ".config" / "inkscape-mcp"
_SETTINGS_PATH = _SETTINGS_DIR / "llm_settings.json"
_KEYS_PATH = _SETTINGS_DIR / "llm_keys.json"

# provider id -> env var fallback (checked when no key is saved in the store)
KEY_ENV: dict[str, str] = {
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "meta": "META_API_KEY",
}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_settings() -> dict[str, Any]:
    """{provider?, endpoint?, model?} - never includes key bytes."""
    with _LOCK:
        return _read_json(_SETTINGS_PATH)


def save_settings(provider: str, endpoint: str | None, model: str) -> None:
    with _LOCK:
        data = _read_json(_SETTINGS_PATH)
        data["provider"] = provider
        if endpoint:
            data["endpoint"] = endpoint
        data["model"] = model
        _write_json(_SETTINGS_PATH, data)


def save_key(provider: str, api_key: str) -> None:
    with _LOCK:
        keys = _read_json(_KEYS_PATH)
        keys[provider] = api_key
        _write_json(_KEYS_PATH, keys)


def clear_key(provider: str) -> None:
    with _LOCK:
        keys = _read_json(_KEYS_PATH)
        if keys.pop(provider, None) is not None:
            _write_json(_KEYS_PATH, keys)


def get_key(provider: str) -> str | None:
    """Saved key first, then the provider's env var fallback."""
    with _LOCK:
        keys = _read_json(_KEYS_PATH)
    stored = keys.get(provider)
    if stored:
        return stored
    import os

    env_name = KEY_ENV.get(provider)
    return os.environ.get(env_name) if env_name else None


def has_key(provider: str) -> bool:
    return bool(get_key(provider))
