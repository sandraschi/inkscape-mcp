"""Shared fleet helpers — repo lists, registry paths, HTTP posts."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("inkscape-mcp.fleet_common")

_SLUG_RE = re.compile(r"^([\w.-]+)/([\w.-]+)$")
_DEFAULT_STATE_DIR = Path(os.getenv("LOCALAPPDATA", Path.home())) / "inkscape-mcp"
DEFAULT_FLEET_OWNER = os.getenv("GIT_GITHUB_FLEET_OWNER", "sandraschi").strip() or "sandraschi"
DEFAULT_REGISTRY_PATH = Path(
    os.getenv("FLEET_REGISTRY_PATH", "D:/Dev/repos/mcp-central-docs/operations/fleet-registry.json")
)
DEFAULT_WEBAPP_PORTS_PATH = Path(
    os.getenv("FLEET_WEBAPP_PORTS_PATH", "D:/Dev/repos/mcp-central-docs/operations/WEBAPP_PORTS.md")
)
DEFAULT_REPOS_ROOT = Path(os.getenv("FLEET_REPOS_ROOT", "D:/Dev/repos"))


def parse_fleet_repos(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for line in text.splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        m = _SLUG_RE.match(t)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def default_fleet_repos_file() -> Path:
    env = os.getenv("GIT_GITHUB_FLEET_REPOS_FILE", "").strip()
    if env:
        return Path(env)
    repo_cfg = Path(__file__).resolve().parents[3] / "config" / "fleet-repos.txt"
    if repo_cfg.is_file():
        return repo_cfg
    return _DEFAULT_STATE_DIR / "fleet-repos.txt"


def load_fleet_repos(
    *, fleet_repos: str | None = None, fleet_repos_file: str | None = None
) -> list[tuple[str, str]]:
    if fleet_repos and fleet_repos.strip():
        repos = parse_fleet_repos(fleet_repos)
        if repos:
            return repos
    path = Path(fleet_repos_file) if fleet_repos_file else default_fleet_repos_file()
    if path.is_file():
        return parse_fleet_repos(path.read_text(encoding="utf-8"))
    return []


def fleet_repos_to_text(repos: list[tuple[str, str]]) -> str:
    return "\n".join(f"{o}/{r}" for o, r in repos)


def parse_iso(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def days_since(iso: str | None) -> int | None:
    dt = parse_iso(iso)
    if not dt:
        return None
    now = datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return max(0, int((now - dt).total_seconds() // 86400))


def state_dir() -> Path:
    custom = os.getenv("GIT_GITHUB_MCP_STATE_DIR", "").strip()
    base = Path(custom) if custom else _DEFAULT_STATE_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base


def post_json(
    url: str, body: dict[str, Any] | None = None, *, timeout: float = 12.0
) -> tuple[bool, str]:
    try:
        resp = httpx.post(url, json=body or {}, timeout=timeout)
        return True, resp.text[:8000]
    except httpx.HTTPError as exc:
        return False, str(exc)


def get_json(url: str, *, timeout: float = 12.0) -> tuple[bool, Any, str]:
    try:
        resp = httpx.get(url, timeout=timeout)
        raw = resp.text
        return True, json.loads(raw) if raw.strip() else {}, ""
    except httpx.HTTPError as exc:
        return False, None, str(exc)
    except json.JSONDecodeError as exc:
        return False, None, str(exc)


def run_git(args: list[str], cwd: Path, timeout: int = 30) -> tuple[bool, str, str]:
    git_exe = shutil.which("git") or "git"
    _subprocess_run = subprocess.run
    try:
        result = _subprocess_run(
            [git_exe, *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
        return result.returncode == 0, result.stdout or "", result.stderr or ""
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return False, "", str(exc)


def read_pyproject_version(repo_path: Path) -> str | None:
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.is_file():
        return None
    try:
        import tomllib

        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        project = data.get("project") or {}
        version = project.get("version")
        return str(version) if version else None
    except Exception:
        text = pyproject.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        return m.group(1) if m else None
