"""Real integration with Inkscape's own online extension gallery
(inkscape.org/gallery/=extension/), not just local .inx scanning.

The gallery has no documented public API, so this mirrors the actual,
canonical client - Inkscape's own GTK Extension Manager
(gitlab.com/inkscape/extras/extension-manager, inkman/remote.py +
inkman/package.py) - read directly from its source rather than guessed:
GET https://inkscape.org/gallery/={category}/json/?q=<query>&tags=&checked=1
returns {"items": [...]}, each item exposing id/name/author/license/tags/
summary/version/stats/verified/links.file (zip download)/links.html and an
"Inkscape Version" compatibility list.

Only `verified` (Inkscape-reviewed) packages install without an explicit
override - the same gate the real Extension Manager applies - because this
downloads and unpacks third-party code that Inkscape will later execute.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import zipfile
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GALLERY_URL = "https://inkscape.org/gallery/=extension/json/"
_MANAGED_MARKER = ".inkscape_mcp_managed.json"


def extensions_dir() -> Path:
    """The user-writable extensions directory to install into - the same
    directories inkscape_system.list_extensions already scans, honoring
    INKSCAPE_EXTENSIONS (the real Extension Manager's own override var) first.
    """
    override = os.environ.get("INKSCAPE_EXTENSIONS")
    if override:
        return Path(override)
    system = platform.system()
    if system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "inkscape" / "extensions"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "org.inkscape.Inkscape" / "config" / "inkscape" / "extensions"
    return Path.home() / ".config" / "inkscape" / "extensions"


def _normalize_item(info: dict[str, Any]) -> dict[str, Any] | None:
    """PackageItem's field mapping (inkman/package.py), minus install state."""
    required = ("name", "author", "verified", "links", "summary")
    if not all(field in info for field in required):
        return None
    stats = info.get("stats") or {}
    version = info.get("version")
    if version is None:
        revisions = stats.get("revisions")
        version = str(int(revisions) + 1) if revisions is not None else "?"
    return {
        "id": info.get("id"),
        "name": info.get("name") or "Unnamed",
        "author": info.get("author"),
        "license": info.get("license") or "",
        "tags": info.get("tags") or [],
        "summary": (info.get("summary") or "No summary")[:200],
        "version": str(version),
        "stars": stats.get("liked", 0),
        "downloads": stats.get("downloaded", 0),
        "verified": bool(info.get("verified")),
        "targets": info.get("Inkscape Version") or [],
        "download_url": (info.get("links") or {}).get("file", ""),
        "page_url": (info.get("links") or {}).get("html", ""),
    }


async def search_gallery(query: str = "", limit: int = 20) -> dict[str, Any]:
    """Search (or browse, if query is empty) the live extension gallery."""
    params: dict[str, Any] = {"checked": 1}
    if query:
        params["q"] = query
    else:
        params["limit"] = limit
        params["order"] = "extra_status"

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(GALLERY_URL, params=params)
        r.raise_for_status()
        payload = r.json()

    items = []
    for raw in payload.get("items", []):
        item = _normalize_item(raw)
        if item is not None:
            items.append(item)
    return {"query": query, "count": len(items[:limit]), "items": items[:limit]}


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> list[str]:
    """Extract with zip-slip protection: every member must resolve inside
    `dest`. Refuses the whole archive rather than partially extracting an
    unsafe one."""
    dest = dest.resolve()
    resolved: dict[str, Path] = {}
    for name in zf.namelist():
        target = (dest / name).resolve()
        if target != dest and dest not in target.parents:
            raise ValueError(f"Unsafe path in archive, refusing to install: {name}")
        resolved[name] = target
    dest.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, target in resolved.items():
        if name.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(name) as src, target.open("wb") as out:
            out.write(src.read())
        written.append(str(target.relative_to(dest)))
    return written


async def install_extension(
    extension_id: str,
    name: str,
    download_url: str,
    verified: bool = False,
    targets: list[str] | None = None,
    inkscape_version: str = "",
    allow_unverified: bool = False,
) -> dict[str, Any]:
    """Download and unpack one gallery item into the local extensions dir.

    Callers get id/name/download_url/verified/targets from search_gallery's
    results - this never re-queries the gallery by id (the API has no such
    lookup, confirmed from the reference client's source).
    """
    if not download_url:
        raise ValueError("download_url is required (from a prior search_gallery result)")
    if not verified and not allow_unverified:
        raise PermissionError(
            f"'{name}' is not a reviewed/verified extension. Installing unreviewed "
            "third-party code that Inkscape will execute is not done by default - "
            "pass allow_unverified=true if you've reviewed it yourself."
        )
    if inkscape_version and targets and inkscape_version not in targets:
        logger.warning(
            "Installing %s despite no listed compatibility with Inkscape %s (targets: %s)",
            name,
            inkscape_version,
            targets,
        )

    dest_root = extensions_dir()
    pkg_dir = dest_root / extension_id

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        r = await client.get(download_url)
        r.raise_for_status()
        archive_bytes = r.content

    tmp_zip = dest_root / f".{extension_id}.download.zip"
    dest_root.mkdir(parents=True, exist_ok=True)
    tmp_zip.write_bytes(archive_bytes)
    try:
        with zipfile.ZipFile(tmp_zip) as zf:
            files = _safe_extract(zf, pkg_dir)
    finally:
        tmp_zip.unlink(missing_ok=True)

    marker = dest_root / _MANAGED_MARKER
    managed = json.loads(marker.read_text(encoding="utf-8")) if marker.exists() else {}
    managed[extension_id] = {"name": name, "download_url": download_url, "files": files, "dir": str(pkg_dir)}
    marker.write_text(json.dumps(managed, indent=2), encoding="utf-8")

    return {
        "id": extension_id,
        "name": name,
        "installed_to": str(pkg_dir),
        "files": files,
        "restart_required": True,
    }


async def uninstall_extension(extension_id: str) -> dict[str, Any]:
    """Remove a previously install_extension'd package. Only removes what
    this server itself installed (tracked in the managed-marker file) - never
    touches manually-installed or bundled extensions."""
    dest_root = extensions_dir()
    marker = dest_root / _MANAGED_MARKER
    managed = json.loads(marker.read_text(encoding="utf-8")) if marker.exists() else {}
    entry = managed.pop(extension_id, None)
    if entry is None:
        raise KeyError(f"'{extension_id}' was not installed by this server (not in the managed list)")

    pkg_dir = Path(entry["dir"])
    removed = []
    if pkg_dir.is_dir():
        for f in sorted(pkg_dir.rglob("*"), reverse=True):
            if f.is_file():
                f.unlink()
                removed.append(str(f))
        for d in sorted(pkg_dir.rglob("*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        if pkg_dir.is_dir() and not any(pkg_dir.iterdir()):
            pkg_dir.rmdir()

    marker.write_text(json.dumps(managed, indent=2), encoding="utf-8")
    return {"id": extension_id, "removed_files": removed, "restart_required": True}


def list_managed_extensions() -> dict[str, Any]:
    """Extensions this server itself installed via install_extension."""
    marker = extensions_dir() / _MANAGED_MARKER
    if not marker.exists():
        return {"extensions": []}
    managed = json.loads(marker.read_text(encoding="utf-8"))
    return {"extensions": [{"id": k, **v} for k, v in managed.items()]}
