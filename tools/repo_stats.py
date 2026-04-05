#!/usr/bin/env python3
"""Print repository statistics (Markdown, tools/, MCP tools, FastMCP). Run from repo root.

Vendored across fleet justfiles — keep self-contained (stdlib only).
"""

from __future__ import annotations

import importlib.metadata
import os
import re
import subprocess
import sys
from pathlib import Path

# Directory name segments to skip when walking source trees
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".env",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "htmlcov",
        "dist",
        "build",
        ".tox",
        ".eggs",
        "site-packages",
        ".cursor",
    }
)


def _parse_fastmcp_from_pyproject(text: str) -> str | None:
    patterns = (
        r"fastmcp\s*(?:\[[^\]]*\])?\s*(?:>=|==|~=)\s*[\"']?([\d.]+)",
        r"(?m)^\s*fastmcp\s*=\s*[\"']?\^?([\d.]+)",
    )
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _parse_name_version_requires(pyproject: Path) -> tuple[str | None, str | None, str | None]:
    if not pyproject.is_file():
        return None, None, None
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return None, None, None
    name_m = re.search(r'(?m)^name\s*=\s*["\']([^"\']+)["\']', text)
    ver_m = re.search(r'(?m)^version\s*=\s*["\']([^"\']+)["\']', text)
    req_m = re.search(r'(?m)^requires-python\s*=\s*["\']([^"\']+)["\']', text)
    return (
        name_m.group(1) if name_m else None,
        ver_m.group(1) if ver_m else None,
        req_m.group(1) if req_m else None,
    )


def _git_short(root: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _git_branch(root: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            b = r.stdout.strip()
            return b if b else None
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _should_skip_dir(name: str) -> bool:
    if name in SKIP_DIR_NAMES:
        return True
    if name.endswith(".egg-info"):
        return True
    return False


def _iter_files(root: Path, suffix: str) -> list[Path]:
    """All files with suffix under root, skipping junk dirs (walks into not-mcp-related for doc totals)."""
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dp = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]
        for fn in filenames:
            if not fn.endswith(suffix):
                continue
            p = dp / fn
            rel = p.relative_to(root)
            if any(_should_skip_dir(part) for part in rel.parts):
                continue
            out.append(p)
    return out


# FastMCP: @mcp.tool() or @docs_mcp.tool() / @server_name.tool()
MCP_TOOL_RE = re.compile(r"@\w+\.tool\s*\(")


def _count_mcp_tools(py_files: list[Path]) -> int:
    n = 0
    for p in py_files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        n += len(MCP_TOOL_RE.findall(text))
    return n


def _py_files_for_mcp_count(root: Path) -> list[Path]:
    """Python files likely to register MCP tools (src/ or top-level package, excluding tests/archived)."""
    candidates: list[Path] = []
    src = root / "src"
    if src.is_dir():
        candidates.extend(_iter_files(src, ".py"))
    else:
        candidates.extend(_iter_files(root, ".py"))
    return [
        p
        for p in candidates
        if "not-mcp-related" not in p.parts
        and "test" not in p.parts
        and not p.name.startswith("test_")
        and p.name != "conftest.py"
    ]


def main() -> None:
    root = Path.cwd().resolve()
    pyproject = root / "pyproject.toml"

    name, version, requires_py = _parse_name_version_requires(pyproject)
    folder = root.name

    fastmcp_decl: str | None = None
    if pyproject.is_file():
        try:
            txt = pyproject.read_text(encoding="utf-8")
            fastmcp_decl = _parse_fastmcp_from_pyproject(txt)
        except OSError:
            pass

    fastmcp_installed: str | None = None
    try:
        fastmcp_installed = importlib.metadata.version("fastmcp")
    except importlib.metadata.PackageNotFoundError:
        pass

    md_all = _iter_files(root, ".md")
    md_archived = sum(1 for p in md_all if "not-mcp-related" in p.relative_to(root).parts)
    md_active = len(md_all) - md_archived

    tools_dir = root / "tools"
    scripts_dir = root / "scripts"
    n_tools_py = len(list(tools_dir.glob("*.py"))) if tools_dir.is_dir() else 0
    n_scripts_py = len(list(scripts_dir.glob("*.py"))) if scripts_dir.is_dir() else 0

    py_for_mcp = _py_files_for_mcp_count(root)
    mcp_tool_decorators = _count_mcp_tools(py_for_mcp)

    skill_md: list[Path] = []
    for p in root.rglob("SKILL.md"):
        if any(part in SKIP_DIR_NAMES for part in p.parts):
            continue
        if "not-mcp-related" in p.parts:
            continue
        skill_md.append(p)

    lines = [
        f"=== Repo stats: {name or '?'} ({folder}) ===",
        f"pyproject: {name or '(no name)'}  {version or ''}  |  Python {requires_py or '(unknown)'}",
        f"FastMCP (declared in pyproject): {fastmcp_decl or '—'}",
        f"FastMCP (installed in current env): {fastmcp_installed or '—'}",
        f"Markdown files: {len(md_all)} total  |  active (excl. not-mcp-related): {md_active}"
        + (f"  |  archived: {md_archived}" if md_archived else ""),
        f"tools/*.py: {n_tools_py}  |  scripts/*.py: {n_scripts_py}",
        f"MCP tools (FastMCP @*.tool(); approx.): {mcp_tool_decorators}",
        f"SKILL.md files: {len(skill_md)}",
    ]

    gh = _git_short(root)
    br = _git_branch(root)
    if gh:
        lines.append(f"Git: {gh}" + (f" ({br})" if br else ""))
    else:
        lines.append("Git: —")

    out = "\n".join(lines) + "\n"
    sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
