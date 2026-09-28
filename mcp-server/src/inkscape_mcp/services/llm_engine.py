"""Local LLM engine lifecycle (APPS_PAGE_STANDARD-adjacent fleet template).

Vendored from arxiv-mcp (proven live against Ollama 0.33): make a selected
model the only VRAM resident, evict everything, list residents, read GPU VRAM.

Zero repo dependencies: stdlib + httpx only. Drop into any `<pkg>/services/`
(or a shared lib) and call from REST endpoints AND MCP tools alike — agents
and web UI must share one engine path, never two implementations.

Provided:
  switch_ollama_model(keep, base_url) — evict all residents except `keep`,
      then warm `keep` (1-token generate). Empty `keep` evicts everything.
  ollama_loaded(base_url) — residents: name + VRAM MB + expiry (for KPIs).
  gpu_vram() — per-GPU used/total/free via nvidia-smi ([] when unavailable).

All failures are non-fatal dicts (engine=False), never raises: callers decide
whether to report (Settings save message) or fail loudly (explicit kick button
returns 502 when the engine is down).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger("llm_engine")

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_KEEP_ALIVE = "10m"
WARM_TIMEOUT = 180.0
PROBE_TIMEOUT = 15.0


def _same_model(a: str, b: str) -> bool:
    """Loose tag equality: an untagged name matches any tag of the same repo."""
    if a == b:
        return True
    a_repo, _, a_tag = a.partition(":")
    b_repo, _, b_tag = b.partition(":")
    if a_repo != b_repo:
        return False
    return not a_tag or not b_tag or a_tag == b_tag


def _parse_nvidia_smi(stdout: str) -> list[dict[str, Any]]:
    """Parse `nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free
    --format=csv,noheader,nounits`. Never raises: garbage lines are skipped."""
    gpus: list[dict[str, Any]] = []
    for line in (stdout or "").splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        try:
            gpus.append(
                {
                    "index": int(parts[0]),
                    "name": ",".join(parts[1:-3]).strip(),
                    "total_mb": int(parts[-3]),
                    "used_mb": int(parts[-2]),
                    "free_mb": int(parts[-1]),
                }
            )
        except ValueError:
            continue
    return gpus


def gpu_vram() -> list[dict[str, Any]]:
    """Live per-GPU VRAM via nvidia-smi. Empty list when unavailable."""
    import subprocess

    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError) as exc:
        logger.debug("nvidia-smi unavailable (%s)", exc)
        return []
    if proc.returncode != 0:
        return []
    return _parse_nvidia_smi(proc.stdout)


async def ollama_loaded(base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    """Residents on the Ollama engine (`/api/ps`): name + VRAM + expiry."""
    result: dict[str, Any] = {"engine": False, "models": []}
    base = (base_url or "").rstrip("/") or DEFAULT_BASE_URL
    try:
        async with httpx.AsyncClient(timeout=PROBE_TIMEOUT) as client:
            ps = await client.get(base + "/api/ps")
            if ps.status_code != 200:
                return result
            result["engine"] = True
            try:
                items = ps.json().get("models") or []
            except Exception:
                items = []
            for m in items:
                if not isinstance(m, dict) or not m.get("name"):
                    continue
                result["models"].append(
                    {
                        "name": m["name"],
                        "size_vram_mb": round((m.get("size_vram") or 0) / 1048576),
                        "expires_at": m.get("expires_at") or "",
                    }
                )
    except Exception as exc:
        logger.debug("ollama loaded probe failed (%s)", exc)
    return result


async def switch_ollama_model(keep: str, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    """Make `keep` the only loaded Ollama model: evict the rest, warm `keep`.

    Empty `keep` evicts everything and warms nothing (full VRAM release).
    Selecting a model must switch VRAM, not just write config — otherwise a
    20 GB hog keeps squatting while the new choice can't fit.
    """
    result: dict[str, Any] = {"evicted": [], "warmed": False, "engine": False}
    keep = (keep or "").strip()
    base = (base_url or "").rstrip("/") or DEFAULT_BASE_URL
    try:
        async with httpx.AsyncClient(timeout=PROBE_TIMEOUT) as client:
            ps = await client.get(base + "/api/ps")
            if ps.status_code != 200:
                return result
            result["engine"] = True
            try:
                loaded = [
                    m.get("name", "")
                    for m in (ps.json().get("models") or [])
                    if isinstance(m, dict) and m.get("name")
                ]
            except Exception:
                loaded = []
            if keep and any(_same_model(keep, name) for name in loaded):
                result["warmed"] = True
            for name in loaded:
                if keep and _same_model(keep, name):
                    continue
                try:
                    await client.post(base + "/api/generate", json={"model": name, "keep_alive": 0})
                    result["evicted"].append(name)
                except Exception as exc:
                    logger.warning("ollama evict %s failed (%s)", name, exc)
            if keep and not result["warmed"]:
                try:
                    async with httpx.AsyncClient(timeout=WARM_TIMEOUT) as warm_client:
                        warm = await warm_client.post(
                            base + "/api/generate",
                            json={
                                "model": keep,
                                "prompt": " ",
                                "keep_alive": DEFAULT_KEEP_ALIVE,
                                "options": {"num_predict": 1},
                            },
                        )
                        result["warmed"] = warm.status_code == 200
                except Exception as exc:
                    logger.warning("ollama warm %s failed (%s)", keep, exc)
    except Exception as exc:
        logger.warning("ollama switch failed (%s)", exc)
    return result
