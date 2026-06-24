"""Inkscape CLI availability helpers."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Any

logger = logging.getLogger(__name__)


def gui_watch_enabled() -> bool:
    """True when INKSCAPE_GUI_WATCH env requests Hands-In guidance."""
    return os.getenv("INKSCAPE_GUI_WATCH", "").strip().lower() in ("1", "true", "yes")


def detect_inkscape_gui_process() -> bool:
    """Best-effort detection of a running Inkscape GUI (non-batch) process."""
    try:
        if sys.platform == "win32":
            completed = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq inkscape.exe", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return "inkscape.exe" in completed.stdout.lower()
        if sys.platform == "darwin":
            completed = subprocess.run(
                ["pgrep", "-x", "Inkscape"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return completed.returncode == 0
        completed = subprocess.run(
            ["pgrep", "-x", "inkscape"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return completed.returncode == 0
    except Exception as exc:
        logger.warning("Inkscape GUI process detection failed: %s", exc)
        return False


async def cli_available(cli_wrapper: Any, config: Any) -> bool:
    """Return True when Inkscape CLI responds to --version."""
    if cli_wrapper is None or config is None or not config.inkscape_executable:
        return False
    try:
        result = await cli_wrapper._execute_command(
            [str(config.inkscape_executable), "--version"],
            config.process_timeout,
        )
        return bool(result and str(result).strip())
    except Exception as exc:
        logger.warning("Inkscape CLI availability check failed: %s", exc)
        return False
