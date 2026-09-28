"""Fleet catalog — registry load, port audit, docs gate, quarantine."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..utils.gh_cli import run_gh
from ..utils.response import error_response
from ..utils.response import success_response
from .fleet_common import DEFAULT_FLEET_OWNER
from .fleet_common import DEFAULT_REGISTRY_PATH
from .fleet_common import DEFAULT_REPOS_ROOT
from .fleet_common import DEFAULT_WEBAPP_PORTS_PATH
from .fleet_common import fleet_repos_to_text
from .fleet_common import run_git

_STARTER_PATHS = (
    "start.ps1",
    "webapp/start.ps1",
    "web_sota/start.ps1",
)
_DOC_PATHS = ("AGENTS.md", "CLAUDE.md")
_INSTALL_PATHS = ("INSTALL.md",)


def load_registry(path: Path | None = None) -> list[dict[str, Any]]:
    reg_path = path or DEFAULT_REGISTRY_PATH
    if not reg_path.is_file():
        return []
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    fleet = data.get("fleet") or data.get("servers") or []
    return fleet if isinstance(fleet, list) else []


def registry_to_github_slugs(
    entries: list[dict[str, Any]] | None = None,
    *,
    owner: str = DEFAULT_FLEET_OWNER,
    active_only: bool = True,
    skip_quarantined: bool = True,
) -> list[tuple[str, str]]:
    rows = entries if entries is not None else load_registry()
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or "active").lower()
        if active_only and status in ("quarantined", "deprecated", "retired"):
            continue
        if skip_quarantined and status == "quarantined":
            continue
        repo_id = str(row.get("id") or row.get("name") or "").strip()
        if not repo_id or repo_id in seen:
            continue
        seen.add(repo_id)
        gh_owner = str(row.get("github_owner") or owner)
        gh_repo = str(row.get("github_repo") or repo_id)
        out.append((gh_owner, gh_repo))
    return out


def op_registry_load(
    *,
    registry_path: str | None = None,
    owner: str = DEFAULT_FLEET_OWNER,
    active_only: bool = True,
) -> dict[str, Any]:
    path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
    if not path.is_file():
        return error_response(
            "registry_load",
            f"Registry not found: {path}",
            recovery_options=["Set FLEET_REGISTRY_PATH", "Clone mcp-central-docs"],
        )
    entries = load_registry(path)
    slugs = registry_to_github_slugs(entries, owner=owner, active_only=active_only)
    return success_response(
        {
            "registry_path": str(path),
            "entry_count": len(entries),
            "github_repos": [f"{o}/{r}" for o, r in slugs],
            "fleet_repos_text": fleet_repos_to_text(slugs),
            "entries": entries,
        },
        "registry_load",
        message=f"Loaded {len(slugs)} GitHub repos from fleet registry",
    )


def _parse_webapp_ports_md(path: Path) -> dict[str, list[int]]:
    """Map repo id/name -> ports listed in WEBAPP_PORTS.md table."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    by_repo: dict[str, list[int]] = defaultdict(list)
    for line in text.splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([\w.-]+)\s*\|", line.strip())
        if m:
            port = int(m.group(1))
            repo = m.group(2).lower()
            by_repo[repo].append(port)
    return dict(by_repo)


def op_port_audit(*, registry_path: str | None = None, webapp_ports_path: str | None = None) -> dict[str, Any]:
    reg_path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
    ports_path = Path(webapp_ports_path) if webapp_ports_path else DEFAULT_WEBAPP_PORTS_PATH
    entries = load_registry(reg_path)
    doc_ports = _parse_webapp_ports_md(ports_path)

    port_to_ids: dict[int, list[str]] = defaultdict(list)
    mismatches: list[dict[str, Any]] = []
    collisions: list[dict[str, Any]] = []

    for row in entries:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id") or "")
        port = int(row.get("port") or 0)
        fport = int(row.get("frontend_port") or 0)
        for p in (port, fport):
            if p > 0:
                port_to_ids[p].append(rid)
        doc_list = doc_ports.get(rid.lower(), [])
        if port > 0 and doc_list and port not in doc_list:
            mismatches.append({"id": rid, "registry_port": port, "webapp_ports_doc": doc_list, "kind": "backend"})
        if fport > 0 and doc_list and fport not in doc_list:
            mismatches.append({"id": rid, "registry_port": fport, "webapp_ports_doc": doc_list, "kind": "frontend"})

    for p, ids in port_to_ids.items():
        if len(ids) > 1:
            collisions.append({"port": p, "repos": ids})

    return success_response(
        {
            "registry_path": str(reg_path),
            "webapp_ports_path": str(ports_path),
            "collision_count": len(collisions),
            "mismatch_count": len(mismatches),
            "collisions": collisions,
            "mismatches": mismatches,
        },
        "port_audit",
        message=f"{len(collisions)} port collisions, {len(mismatches)} doc mismatches",
    )


def _docs_present(repo_path: Path) -> dict[str, bool]:
    return {
        "agents_or_claude": any((repo_path / p).is_file() for p in _DOC_PATHS),
        "install": any((repo_path / p).is_file() for p in _INSTALL_PATHS),
        "starter": any((repo_path / p).is_file() for p in _STARTER_PATHS),
    }


def op_docs_gate(*, registry_path: str | None = None, repos_root: str | None = None) -> dict[str, Any]:
    entries = load_registry(Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH)
    root = Path(repos_root) if repos_root else DEFAULT_REPOS_ROOT
    results: list[dict[str, Any]] = []
    missing_total = 0
    for row in entries:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or "active").lower()
        if status in ("quarantined", "deprecated", "retired"):
            continue
        rid = str(row.get("id") or "")
        repo_path = Path(str(row.get("repo_path") or root / rid))
        if not repo_path.is_dir():
            results.append({"id": rid, "repo_path": str(repo_path), "exists": False, "missing": ["repo_path"]})
            missing_total += 1
            continue
        checks = _docs_present(repo_path)
        missing = [k for k, ok in checks.items() if not ok]
        if missing:
            missing_total += 1
        results.append(
            {
                "id": rid,
                "repo_path": str(repo_path),
                "exists": True,
                **checks,
                "missing": missing,
                "compliant": len(missing) == 0,
            }
        )
    non_compliant = [r for r in results if not r.get("compliant", False)]
    return success_response(
        {
            "checked": len(results),
            "non_compliant_count": len(non_compliant),
            "repos": results,
            "non_compliant": non_compliant,
        },
        "docs_gate",
        message=f"{len(non_compliant)} repos missing fleet doc/launcher files",
    )


def op_quarantine_report(*, registry_path: str | None = None, owner: str = DEFAULT_FLEET_OWNER) -> dict[str, Any]:
    entries = load_registry(Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH)
    quarantined = [r for r in entries if isinstance(r, dict) and str(r.get("status") or "").lower() == "quarantined"]
    report: list[dict[str, Any]] = []
    for row in quarantined:
        rid = str(row.get("id") or "")
        gh_repo = str(row.get("github_repo") or rid)
        slug = f"{owner}/{gh_repo}"
        open_prs = 0
        open_issues = 0
        last_push = None
        ok, out, _ = run_gh(["api", f"repos/{slug}", "-q", "{pushedAt, openIssuesCount, openPullsCount, htmlUrl}"])
        if ok and out.strip():
            try:
                meta = json.loads(out) if out.strip().startswith("{") else {}
            except json.JSONDecodeError:
                meta = {}
            if isinstance(meta, dict):
                open_issues = int(meta.get("openIssuesCount") or 0)
                open_prs = int(meta.get("openPullsCount") or 0)
                last_push = meta.get("pushedAt")
        repo_path = Path(str(row.get("repo_path") or DEFAULT_REPOS_ROOT / rid))
        if repo_path.is_dir():
            ok2, log_out, _ = run_git(["log", "-1", "--format=%ci"], repo_path)
            if ok2:
                last_push = last_push or log_out.strip()
        report.append(
            {
                "id": rid,
                "slug": slug,
                "superseded_by": row.get("superseded_by"),
                "description": row.get("description"),
                "open_prs": open_prs,
                "open_issues": open_issues,
                "last_activity": last_push,
                "repo_path": str(repo_path),
            }
        )
    return success_response(
        {"count": len(report), "repos": report},
        "quarantine_report",
        message=f"{len(report)} quarantined hulls in registry",
    )
