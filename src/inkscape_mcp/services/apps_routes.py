"""Fleet Apps hub REST endpoints (APPS_PAGE_STANDARD.md v3).

Vendored module — do not hand-edit per-repo copies. Fix here (or in the
git-github-mcp reference impl) and re-vendor via
mcp-central-docs/scripts/vendor-apps-page.ps1.

Wire with one line in your REST module (FastAPI APIRouter or full app —
both expose .get/.post):

    from <pkg>.services.apps_routes import register_apps_routes
    register_apps_routes(router)

Provides: GET /apps, GET /apps/health?port=, POST /apps/ensure. Reads the same fleet-registry.json the fleet_ops MCP
tools read, so UI and agents cannot drift.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import Query
from pydantic import BaseModel

from .fleet_catalog import load_registry

logger = logging.getLogger("apps_routes")


def _read_pyproject_desc(repo_path: Path) -> str | None:
    """Plain project description from pyproject (no marketing hype)."""
    p = repo_path / "pyproject.toml"
    if not p.is_file():
        return None
    try:
        import tomllib

        data = tomllib.loads(p.read_text(encoding="utf-8"))
        desc = str(data.get("project", {}).get("description") or "").strip()
        if desc and len(desc) >= 10 and "hardened substrate" not in desc.lower():
            return desc
    except Exception:
        pass
    try:
        import re

        txt = p.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'description\s*=\s*["\']([^"\']+)["\']', txt)
        if m:
            d = m.group(1).strip()
            if len(d) >= 10 and "hardened substrate" not in d.lower():
                return d
    except Exception:
        pass
    return None


def _is_hype(desc: str) -> bool:
    low = desc.lower()
    return (
        any(k in low for k in ["industrial-grade", "agentic revolution", "hardened substrate"])
        or len(desc.strip()) < 12
    )


def _enriched_apps() -> tuple[list[dict[str, Any]], int]:
    rows = load_registry()
    apps: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id") or "")
        port = int(row.get("frontend_port") or row.get("port") or 0)
        if port <= 0:
            continue
        raw_desc = str(row.get("description") or "")
        cat = str(row.get("category") or "mcp")
        repo_path = Path(str(row.get("repo_path") or f"D:/Dev/repos/{rid}"))
        desc = raw_desc
        if _is_hype(raw_desc) or not raw_desc.strip():
            py_desc = _read_pyproject_desc(repo_path)
            if py_desc:
                desc = py_desc
            elif cat and cat.lower() != "mcp":
                desc = cat
            else:
                desc = raw_desc or "Fleet MCP — local webapp"
        has_tauri = (repo_path / "native" / "tauri.conf.json").is_file() or (
            repo_path / "src-tauri" / "tauri.conf.json"
        ).is_file()
        has_tauri_installed = False
        if has_tauri:
            for cand in [
                Path.home() / "AppData" / "Local" / "Programs" / rid / f"{rid}.exe",
                repo_path / "native" / "target" / "release" / f"{rid}.exe",
            ]:
                if cand.is_file():
                    has_tauri_installed = True
                    break
        gh_owner = str(row.get("github_owner") or "sandraschi")
        gh_repo = str(row.get("github_repo") or rid)
        apps.append(
            {
                "id": rid,
                "name": str(row.get("name") or rid),
                "description": desc,
                "port": port,
                "backend_port": int(row.get("port") or 0),
                "category": cat,
                "url": f"http://127.0.0.1:{port}",
                "gh_url": f"https://github.com/{gh_owner}/{gh_repo}",
                "repo_path": str(repo_path),
                "has_tauri": has_tauri,
                "has_tauri_installed": has_tauri_installed,
                "last_commit": None,
            }
        )
    apps.sort(key=lambda a: a["port"])
    return apps, len(rows)


def _check_port_health_sync(port: int, timeout: float = 1.2) -> dict[str, Any]:
    """TCP connect + health-endpoint probe. Sync: callers run it in a thread."""
    import socket

    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            pass
    except Exception as e:
        return {
            "port": port,
            "alive": False,
            "reason": f"tcp refused: {e}",
            "health_url": f"http://127.0.0.1:{port}/health",
        }
    for path in (
        "/health",
        "/api/health",
        "/api/status",
        "/api/capabilities",
        "/api/v1/health",
        "/api/capabilities/health",
    ):
        try:
            import httpx

            with httpx.Client(timeout=timeout) as c:
                r = c.get(f"http://127.0.0.1:{port}{path}")
                if 200 <= r.status_code < 500:
                    return {
                        "port": port,
                        "alive": True,
                        "status_code": r.status_code,
                        "health_url": f"http://127.0.0.1:{port}{path}",
                        "reason": "http ok",
                    }
        except Exception:
            continue
    return {
        "port": port,
        "alive": True,
        "reason": "tcp open but health 404",
        "health_url": f"http://127.0.0.1:{port}/health",
    }


def _is_process_running(name: str) -> list[int]:
    import subprocess

    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {name}.exe"],
            capture_output=True,
            text=True,
            timeout=4,
        )
        pids: list[int] = []
        for line in out.stdout.splitlines():
            if name.lower() in line.lower() and ".exe" in line.lower():
                for p in line.split():
                    if p.isdigit():
                        try:
                            pid = int(p)
                            if pid > 4:
                                pids.append(pid)
                        except Exception:
                            pass
        return pids
    except Exception:
        return []


def _bring_to_foreground(pids: list[int]) -> bool:
    import subprocess

    if not pids:
        return False
    pid = pids[0]
    ps = f"""
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Win {{ [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow); }}
'@
$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue
if ($p) {{
  $h = $p.MainWindowHandle
  if ($h -eq 0) {{ $h = $p.Handle }}
  [Win]::ShowWindow($h, 9) | Out-Null
  [Win]::SetForegroundWindow($h) | Out-Null
  exit 0
}}
exit 1
"""
    try:
        r = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps], timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def _find_starts_for_id(app_id: str) -> list[str]:
    candidates: list[str] = []

    def _try_ids(base_id: str) -> list[str]:
        ids_to_try = [base_id]
        if base_id.endswith("-mcp"):
            ids_to_try.append(base_id[:-4])
            ids_to_try.append(base_id[:-4].replace("-mcp", ""))
        return ids_to_try

    for cand_id in _try_ids(app_id):
        mcd = Path(r"D:\Dev\repos\mcp-central-docs\starts") / f"{cand_id}-start.bat"
        if mcd.exists() and str(mcd) not in candidates:
            candidates.append(str(mcd))
    for cand_id in _try_ids(app_id):
        repo_ps1 = Path(r"D:\Dev\repos") / cand_id / "start.ps1"
        if repo_ps1.exists() and str(repo_ps1) not in candidates:
            candidates.append(str(repo_ps1))
        repo_bat = Path(r"D:\Dev\repos") / cand_id / "start.bat"
        if repo_bat.exists() and str(repo_bat) not in candidates:
            candidates.append(str(repo_bat))
    for p in [
        Path.home() / "AppData" / "Local" / "Programs" / app_id / f"{app_id}.exe",
        Path.home() / "AppData" / "Local" / app_id / f"{app_id}.exe",
        Path(r"D:\Dev\repos") / app_id / "native" / "target" / "release" / f"{app_id}.exe",
    ]:
        if p.exists():
            candidates.append(str(p))
    return candidates


class AppsEnsureIn(BaseModel):
    id: str = ""
    app_id: str = ""
    port: int = 0


def _resolve_id_port(app_id: str, port: int) -> tuple[str, int]:
    if not app_id and port:
        for row in load_registry():
            if int(row.get("frontend_port") or row.get("port") or 0) == port:
                app_id = str(row.get("id") or "")
                break
    if not port and app_id:
        for row in load_registry():
            if str(row.get("id")) == app_id:
                port = int(row.get("frontend_port") or row.get("port") or 0)
                break
    return app_id, port


def register_apps_routes(router: Any) -> None:
    """Attach GET /apps, GET /apps/health, POST /apps/ensure to a router."""

    @router.get("/apps")
    async def api_apps() -> dict[str, Any]:
        """Fleet apps hub — registry entries with webapp ports (enriched)."""
        apps, fleet_total = _enriched_apps()
        logger.info("apps hub listed %d entries", len(apps))
        return {"apps": apps, "fleet_total": fleet_total}

    @router.get("/apps/health")
    async def api_apps_health(port: int = Query(...)) -> dict[str, Any]:
        """Health-dot backend proxy (avoids CORS)."""
        import asyncio

        return await asyncio.to_thread(_check_port_health_sync, int(port))

    @router.post("/apps/ensure")
    async def api_apps_ensure(body: AppsEnsureIn) -> dict[str, Any]:
        """Click-to-open: health first, foreground Tauri, else start detached."""
        import asyncio

        app_id, port = _resolve_id_port((body.id or body.app_id).strip(), int(body.port or 0))
        if not port:
            return {"success": False, "error": "port or id required", "alive": False}
        health = await asyncio.to_thread(_check_port_health_sync, port)
        if not health.get("alive") and app_id:
            try:
                for row in load_registry():
                    if str(row.get("id")) == app_id:
                        bport = int(row.get("port") or 0)
                        fport = int(row.get("frontend_port") or 0)
                        cand = (
                            bport
                            if bport != port and bport > 0
                            else (fport if fport != port and fport > 0 else 0)
                        )
                        if cand:
                            h2 = await asyncio.to_thread(_check_port_health_sync, cand)
                            if h2.get("alive"):
                                health = h2
                                port = cand
                        break
            except Exception:
                pass
        if health.get("alive"):
            if app_id:
                pids = await asyncio.to_thread(_is_process_running, app_id)
                if pids:
                    await asyncio.to_thread(_bring_to_foreground, pids)
                    return {
                        "success": True,
                        "status": "brought_to_foreground",
                        "alive": True,
                        "url": f"http://127.0.0.1:{port}",
                        "pids": pids,
                        "port": port,
                        "id": app_id,
                    }
            return {
                "success": True,
                "status": "already_running",
                "alive": True,
                "url": f"http://127.0.0.1:{port}",
                "port": port,
                "id": app_id,
            }
        if app_id:
            pids = await asyncio.to_thread(_is_process_running, app_id)
            if not pids:
                pids = await asyncio.to_thread(_is_process_running, f"{app_id}-native")
            if pids:
                ok = await asyncio.to_thread(_bring_to_foreground, pids)
                health2 = await asyncio.to_thread(_check_port_health_sync, port)
                return {
                    "success": True,
                    "status": "brought_to_foreground" if ok else "found_process",
                    "alive": bool(health2.get("alive")),
                    "url": f"http://127.0.0.1:{port}",
                    "pids": pids,
                    "port": port,
                    "id": app_id,
                }
        if app_id:
            candidates = await asyncio.to_thread(_find_starts_for_id, app_id)
            start_cmd = None
            for c in candidates:
                if c.lower().endswith("-start.bat") or c.lower().endswith("start.ps1"):
                    start_cmd = c
                    break
            if start_cmd:
                try:
                    import subprocess

                    if start_cmd.lower().endswith(".ps1"):
                        subprocess.Popen(
                            [
                                "powershell.exe",
                                "-NoProfile",
                                "-ExecutionPolicy",
                                "Bypass",
                                "-File",
                                start_cmd,
                            ],
                            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
                        )
                    else:
                        subprocess.Popen(
                            ["cmd.exe", "/c", start_cmd],
                            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
                        )
                    for _ in range(12):
                        await asyncio.sleep(1)
                        h = await asyncio.to_thread(_check_port_health_sync, port)
                        if h.get("alive"):
                            return {
                                "success": True,
                                "status": "started",
                                "alive": True,
                                "url": f"http://127.0.0.1:{port}",
                                "port": port,
                                "id": app_id,
                                "via": start_cmd,
                            }
                    return {
                        "success": True,
                        "status": "start_initiated",
                        "alive": False,
                        "url": f"http://127.0.0.1:{port}",
                        "port": port,
                        "id": app_id,
                        "via": start_cmd,
                        "note": "started but health not yet ok - wait a few seconds and retry",
                    }
                except Exception as e:
                    return {"success": False, "error": str(e), "port": port, "id": app_id}
            for c in candidates:
                if c.lower().endswith(".exe") and "setup" not in c.lower():
                    try:
                        import subprocess

                        subprocess.Popen(
                            [c],
                            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
                        )
                        return {
                            "success": True,
                            "status": "tauri_started",
                            "alive": False,
                            "url": f"http://127.0.0.1:{port}",
                            "port": port,
                            "id": app_id,
                            "via": c,
                        }
                    except Exception as e:
                        return {"success": False, "error": str(e), "port": port, "id": app_id}
            return {
                "success": False,
                "error": f"no start entry found for {app_id} (checked {candidates})",
                "port": port,
                "id": app_id,
            }
        return {"success": False, "error": "could not start - no id", "port": port}
