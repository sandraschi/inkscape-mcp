"""Sync MCPB source tree and run Anthropic mcpb pack -> dist/*.mcpb.

Requires Node.js and npx on PATH (`npx -y @anthropic-ai/mcpb`).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path


def _npx_argv(extra: list[str]) -> list[str]:
    """Invoke npx via node + npx-cli.js (works when `npx` is not a real Win32 executable)."""
    node = shutil.which("node")
    if not node:
        raise FileNotFoundError("Node.js not found on PATH. Install Node.js to run mcpb pack.")
    node_dir = Path(node).resolve().parent
    npx_cli = node_dir / "node_modules" / "npm" / "bin" / "npx-cli.js"
    if not npx_cli.is_file():
        raise FileNotFoundError(f"Expected npx-cli.js at {npx_cli}")
    return [node, str(npx_cli), *extra]


def _read_version(pyproject: Path) -> str:
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        raise ValueError("Could not parse version from pyproject.toml")
    return m.group(1)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    pyproject = repo / "pyproject.toml"
    mcp_root = repo / "mcp-server"
    dist_dir = repo / "dist"

    sync = subprocess.run(
        [sys.executable, str(repo / "tools" / "sync_mcpb_src.py")],
        cwd=repo,
        check=False,
    )
    if sync.returncode != 0:
        return sync.returncode

    # MCPB_PACKAGING_STANDARDS.md "Pack-root .mcpbignore gotcha": mcpb pack
    # reads .mcpbignore from the pack root (mcp-server/), not the repo root -
    # without this copy it silently ignores nothing and ships whatever the
    # sync step dragged in.
    root_ignore = repo / ".mcpbignore"
    if root_ignore.is_file():
        shutil.copy2(root_ignore, mcp_root / ".mcpbignore")

    version = _read_version(pyproject)
    out_name = f"inkscape-mcp-v{version}.mcpb"
    dist_dir.mkdir(parents=True, exist_ok=True)
    out_path = dist_dir / out_name

    cmd = _npx_argv(
        [
            "-y",
            "@anthropic-ai/mcpb@latest",
            "pack",
            str(mcp_root),
            str(out_path),
        ]
    )
    print("Running:", " ".join(cmd))
    r = subprocess.run(cmd, cwd=repo)
    if r.returncode == 0:
        print(f"Wrote {out_path}")
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
