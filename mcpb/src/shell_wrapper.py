"""
Inkscape Shell Mode Wrapper — persistent Inkscape process for fast multi-step operations.

Inkscape 1.x supports `inkscape --shell` which opens an interactive action REPL.
Instead of spawning a fresh process per operation (500–1500ms overhead each),
the ShellModeWrapper keeps ONE Inkscape process alive and feeds it action strings
line-by-line — dropping per-operation cost to ~20–80ms.

Protocol:
    - Input:  one action string per line, e.g. "file-open:/tmp/foo.svg\\n"
    - Output: Inkscape prints ">" as a prompt after processing each command
    - Multi-step: join with ";" separator, send as ONE line

Usage:
    async with ShellModeWrapper(inkscape_exe) as shell:
        await shell.run_actions("file-open:/tmp/in.svg")
        await shell.run_actions(
            "select-all",
            "path-union",
            f"export-filename:/tmp/out.svg",
            "export-do",
        )
        svg_xml = await shell.run_actions_and_read(output_path="/tmp/out.svg",
            "select-all", "path-union",
            "export-filename:/tmp/out.svg", "export-do"
        )

Thread safety: NOT thread-safe. Use one wrapper per concurrent workflow,
or wrap usage in an asyncio.Lock.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

_SHELL_PROMPT = b">"
_DEFAULT_TIMEOUT = 30.0


class ShellModeError(Exception):
    """Raised when the Inkscape shell session fails."""


class ShellModeWrapper:
    """
    Persistent Inkscape --shell process wrapper.

    Acts as an async context manager:
        async with ShellModeWrapper(exe) as shell:
            await shell.run_actions("select-all", "path-union", ...)
    """

    def __init__(
        self,
        inkscape_exe: str,
        timeout: float = _DEFAULT_TIMEOUT,
        startup_timeout: float = 10.0,
    ) -> None:
        if not Path(inkscape_exe).exists():
            raise ShellModeError(f"Inkscape executable not found: {inkscape_exe}")
        self._exe = inkscape_exe
        self._timeout = timeout
        self._startup_timeout = startup_timeout
        self._proc: Optional[asyncio.subprocess.Process] = None

    # ── lifecycle ────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Launch the Inkscape --shell process and wait for initial prompt."""
        if self._proc and self._proc.returncode is None:
            return  # already running

        logger.info("Starting Inkscape shell: %s --shell", self._exe)
        self._proc = await asyncio.create_subprocess_exec(
            self._exe,
            "--shell",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Wait for the initial ">" prompt
        try:
            await asyncio.wait_for(self._read_until_prompt(), timeout=self._startup_timeout)
        except asyncio.TimeoutError:
            await self.close()
            raise ShellModeError(
                f"Inkscape shell did not produce initial prompt within {self._startup_timeout}s. "
                "Inkscape 1.0+ required."
            )
        logger.info("Inkscape shell ready (pid=%s)", self._proc.pid)

    async def close(self) -> None:
        """Shutdown the Inkscape shell process cleanly."""
        if not self._proc:
            return
        try:
            if self._proc.returncode is None:
                self._proc.stdin.write(b"quit\n")
                await self._proc.stdin.drain()
                await asyncio.wait_for(self._proc.wait(), timeout=5.0)
        except Exception:
            pass
        finally:
            if self._proc.returncode is None:
                self._proc.kill()
            self._proc = None
            logger.info("Inkscape shell closed")

    async def __aenter__(self) -> "ShellModeWrapper":
        await self.start()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    # ── public API ───────────────────────────────────────────────────────────

    async def run_actions(self, *actions: str) -> str:
        """
        Send one or more Inkscape actions to the shell in a single line.

        Actions are joined with ';' and sent as one command.
        Returns Inkscape's stdout response between the last two prompts.

        Example:
            await shell.run_actions(
                "file-open:/tmp/drawing.svg",
                "select-all",
                "path-union",
                "export-filename:/tmp/out.svg",
                "export-do",
            )
        """
        self._ensure_running()
        command = ";".join(a.strip() for a in actions if a.strip()) + "\n"
        logger.debug("Shell → %r", command.rstrip())
        self._proc.stdin.write(command.encode())
        await self._proc.stdin.drain()

        try:
            response = await asyncio.wait_for(self._read_until_prompt(), timeout=self._timeout)
        except asyncio.TimeoutError:
            raise ShellModeError(f"Inkscape shell timed out ({self._timeout}s) on: {command!r}")
        logger.debug("Shell ← %r", response[:120])
        return response

    async def open_file(self, path: str) -> str:
        """Open an SVG file in the shell session."""
        return await self.run_actions(f"file-open:{path}")

    async def save_file(self, output_path: str, plain_svg: bool = True) -> str:
        """Export the current document to output_path."""
        actions: List[str] = [f"export-filename:{output_path}"]
        if plain_svg:
            actions.append("export-plain-svg")
        actions.append("export-do")
        return await self.run_actions(*actions)

    async def select_all(self) -> str:
        return await self.run_actions("select-all")

    async def path_union(self) -> str:
        return await self.run_actions("select-all", "path-union")

    async def path_difference(self) -> str:
        return await self.run_actions("select-all", "path-difference")

    async def path_intersection(self) -> str:
        return await self.run_actions("select-all", "path-intersection")

    async def path_simplify(self, threshold: float = 1.0) -> str:
        return await self.run_actions("select-all", f"selection-simplify:{threshold}")

    async def text_to_path(self) -> str:
        return await self.run_actions("select-all", "object-to-path")

    async def fit_canvas_to_drawing(self) -> str:
        return await self.run_actions("fit-canvas-to-drawing")

    async def vacuum_defs(self) -> str:
        return await self.run_actions("vacuum-defs")

    async def run_action_sequence(self, actions: List[str]) -> str:
        """Run a pre-built list of action strings as one command."""
        return await self.run_actions(*actions)

    async def run_full_pipeline(
        self,
        input_path: str,
        output_path: str,
        actions: List[str],
    ) -> str:
        """
        Convenience: open file, run actions, save. All in one shell session.

        Returns Inkscape output from the final save step.
        """
        await self.open_file(input_path)
        if actions:
            await self.run_actions(*actions)
        return await self.save_file(output_path)

    # ── internal ─────────────────────────────────────────────────────────────

    def _ensure_running(self) -> None:
        if not self._proc or self._proc.returncode is not None:
            raise ShellModeError(
                "Inkscape shell is not running. "
                "Use 'async with ShellModeWrapper(exe) as shell:' or call .start() first."
            )

    async def _read_until_prompt(self) -> str:
        """
        Read stdout bytes until we see the '>' prompt character on its own.
        Returns everything read up to (but not including) the prompt.
        """
        buf = bytearray()
        assert self._proc is not None
        while True:
            chunk = await self._proc.stdout.read(256)
            if not chunk:
                raise ShellModeError("Inkscape shell process closed unexpectedly")
            buf.extend(chunk)
            # The shell prints "> " or just ">" — look for a lone > at end of buffer
            if buf.rstrip(b" \t\r\n").endswith(b">"):
                break
        # Strip the trailing prompt and decode
        text = buf.decode("utf-8", errors="replace")
        # Remove trailing "> " prompt
        text = text.rstrip()
        if text.endswith(">"):
            text = text[:-1].rstrip()
        return text

    @property
    def is_running(self) -> bool:
        return bool(self._proc and self._proc.returncode is None)

    @property
    def pid(self) -> Optional[int]:
        return self._proc.pid if self._proc else None


# ── pool for concurrent use ───────────────────────────────────────────────────


class ShellModePool:
    """
    Simple pool of ShellModeWrapper instances for concurrent agentic workflows.
    Each caller gets its own shell session (Inkscape shell is single-document).

    Usage:
        pool = ShellModePool(inkscape_exe, size=3)
        await pool.start()
        async with pool.acquire() as shell:
            await shell.run_full_pipeline(...)
        await pool.close()
    """

    def __init__(self, inkscape_exe: str, size: int = 3) -> None:
        self._exe = inkscape_exe
        self._size = size
        self._wrappers: List[ShellModeWrapper] = []
        self._sem = asyncio.Semaphore(size)

    async def start(self) -> None:
        self._wrappers = [ShellModeWrapper(self._exe) for _ in range(self._size)]
        await asyncio.gather(*(w.start() for w in self._wrappers))
        logger.info("ShellModePool started (%d sessions)", self._size)

    async def close(self) -> None:
        await asyncio.gather(*(w.close() for w in self._wrappers), return_exceptions=True)
        self._wrappers.clear()

    def acquire(self) -> "ShellModePool._AcquiredShell":
        return ShellModePool._AcquiredShell(self)

    class _AcquiredShell:
        def __init__(self, pool: "ShellModePool") -> None:
            self._pool = pool
            self._wrapper: Optional[ShellModeWrapper] = None
            self._idx = 0

        async def __aenter__(self) -> ShellModeWrapper:
            await self._pool._sem.acquire()
            # Find a running wrapper
            for i, w in enumerate(self._pool._wrappers):
                if w.is_running:
                    self._wrapper = w
                    self._idx = i
                    return w
            # All crashed — restart one
            w = ShellModeWrapper(self._pool._exe)
            await w.start()
            self._pool._wrappers[0] = w
            self._wrapper = w
            return w

        async def __aexit__(self, *args) -> None:
            self._pool._sem.release()
