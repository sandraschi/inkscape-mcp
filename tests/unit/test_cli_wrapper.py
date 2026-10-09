"""
Unit tests for Inkscape CLI wrapper module.
"""

import asyncio
import os
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from inkscape_mcp.cli_wrapper import InkscapeCliError
from inkscape_mcp.cli_wrapper import InkscapeCliWrapper
from inkscape_mcp.cli_wrapper import InkscapeExecutionError
from inkscape_mcp.cli_wrapper import InkscapeTimeoutError


class _FakeProcess:
    """Stand-in for the asyncio subprocess object returned by create_subprocess_exec."""

    def __init__(self, returncode: int = 0, stdout: bytes = b"", stderr: bytes = b""):
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
        self.killed = False

    async def communicate(self):
        return self._stdout, self._stderr

    def kill(self):
        self.killed = True

    async def wait(self):
        return None


class TestInkscapeCliWrapper:
    """Test InkscapeCliWrapper class functionality."""

    def test_initialization(self, mock_inkscape_config):
        """Test wrapper initializes correctly."""
        wrapper = InkscapeCliWrapper(mock_inkscape_config)

        assert wrapper.config == mock_inkscape_config
        assert wrapper.config.inkscape_executable.endswith("inkscape.exe")

    def test_initialization_invalid_config(self):
        """Test initialization with invalid config raises InkscapeCliError."""
        with pytest.raises(InkscapeCliError):
            InkscapeCliWrapper(None)

    @pytest.mark.asyncio
    async def test_execute_command_success(self, mock_cli_wrapper):
        """Test successful command execution."""
        fake_process = _FakeProcess(returncode=0, stdout=b"test output", stderr=b"")

        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=fake_process)):
            result = await mock_cli_wrapper._execute_command(["--version"], timeout=5)

        assert result == "test output"

    @pytest.mark.asyncio
    async def test_execute_command_failure(self, mock_cli_wrapper):
        """Test failed command execution raises InkscapeExecutionError."""
        fake_process = _FakeProcess(returncode=1, stdout=b"", stderr=b"Error: bad option")

        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=fake_process)):
            with pytest.raises(InkscapeExecutionError):
                await mock_cli_wrapper._execute_command(["--invalid-option"], timeout=5)

    @pytest.mark.asyncio
    async def test_execute_command_stderr_not_merged_on_success(self, mock_cli_wrapper):
        """Regression test for issue #8: stderr diagnostics must not corrupt query output.

        A fontconfig warning on stderr (non-ASCII install path) previously got
        concatenated onto ``--query-all`` stdout, breaking float parsing.
        """
        fake_process = _FakeProcess(
            returncode=0,
            stdout=b"2908.5\n",
            stderr=b"Fontconfig error: Cannot load default config file",
        )

        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=fake_process)):
            result = await mock_cli_wrapper._execute_command(["--query-all"], timeout=5)

        assert result == "2908.5\n"
        float(result.strip())  # the reporter's parse step must not raise

    @pytest.mark.asyncio
    async def test_execute_command_failure_surfaces_stderr(self, mock_cli_wrapper):
        """On nonzero exit, stderr is surfaced inside the raised error message."""
        fake_process = _FakeProcess(returncode=1, stdout=b"", stderr=b"Error: bad option")

        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=fake_process)):
            with pytest.raises(InkscapeExecutionError) as exc_info:
                await mock_cli_wrapper._execute_command(["--invalid-option"], timeout=5)

        assert "Error: bad option" in str(exc_info.value)

    def test_get_environment_windows_unsets_locale(self, mock_cli_wrapper):
        """Regression test for issue #8: no LANG/LC_ALL forcing on Windows."""
        with (
            patch.object(os, "name", "nt"),
            patch.dict(os.environ, {"LANG": "de_DE.UTF-8", "LC_ALL": "de_DE.UTF-8"}),
        ):
            env = mock_cli_wrapper._get_environment()

        assert "LANG" not in env
        assert "LC_ALL" not in env

    def test_get_environment_posix_forces_utf8(self, mock_cli_wrapper):
        """POSIX behavior unchanged: C.UTF-8 is forced for output parsing."""
        with (
            patch.object(os, "name", "posix"),
            patch.dict(os.environ, {}, clear=False),
        ):
            env = mock_cli_wrapper._get_environment()

        assert env["LANG"] == "C.UTF-8"
        assert env["LC_ALL"] == "C.UTF-8"

    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, mock_cli_wrapper):
        """Test command execution timeout raises InkscapeTimeoutError."""
        fake_process = _FakeProcess(returncode=0)

        with (
            patch("asyncio.create_subprocess_exec", AsyncMock(return_value=fake_process)),
            patch("asyncio.wait_for", AsyncMock(side_effect=TimeoutError)),
        ):
            with pytest.raises(InkscapeTimeoutError):
                await mock_cli_wrapper._execute_command(["--version"], timeout=0.001)

        assert fake_process.killed is True

    @pytest.mark.asyncio
    async def test_execute_actions_success(self, mock_cli_wrapper):
        """Test successful actions execution."""
        mock_cli_wrapper._execute_command = AsyncMock(return_value="Actions executed successfully")

        result = await mock_cli_wrapper.execute_actions(
            input_path="test.svg", actions=["select-all", "export-do"]
        )

        assert result == "Actions executed successfully"
        mock_cli_wrapper._execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_actions_with_export(self, mock_cli_wrapper):
        """Test actions execution appends export-do when output_path is given."""
        mock_cli_wrapper._execute_command = AsyncMock(return_value="")

        await mock_cli_wrapper.execute_actions(
            input_path="test.svg",
            actions=["select-all", "object-to-path"],
            output_path="output.svg",
        )

        cmd_args = mock_cli_wrapper._execute_command.call_args.args[0]
        assert any("--export-filename=" in arg for arg in cmd_args)
        assert any(arg.endswith(";export-do") for arg in cmd_args)

    @pytest.mark.asyncio
    async def test_export_file_success(self, mock_cli_wrapper, temp_file):
        """Test successful file export builds the expected CLI arguments."""
        mock_cli_wrapper._execute_command = AsyncMock(return_value="")

        result = await mock_cli_wrapper.export_file(
            input_path=str(temp_file), output_path="output.png", export_type="png", dpi=300
        )

        assert result == ""
        cmd_args = mock_cli_wrapper._execute_command.call_args.args[0]
        assert "--export-dpi" in cmd_args
        assert "300" in cmd_args
        assert "--export-area-drawing" in cmd_args

    @pytest.mark.asyncio
    async def test_export_file_unknown_format_not_validated(self, mock_cli_wrapper, temp_file):
        """export_file performs no format validation - an unknown type is passed straight through."""
        mock_cli_wrapper._execute_command = AsyncMock(return_value="")

        await mock_cli_wrapper.export_file(
            input_path=str(temp_file), output_path="output.invalid", export_type="invalid"
        )

        cmd_args = mock_cli_wrapper._execute_command.call_args.args[0]
        assert "--export-type" in cmd_args
        assert "invalid" in cmd_args
        # Not a raster format, so no DPI flag is added
        assert "--export-dpi" not in cmd_args

    @pytest.mark.asyncio
    async def test_query_object_success(self, mock_cli_wrapper):
        """Test object querying returns the raw CLI output string (no parsing)."""
        mock_cli_wrapper._execute_command = AsyncMock(return_value="10,20,100,50")

        result = await mock_cli_wrapper.query_object(
            input_path="test.svg", object_id="rect1", query_type="bbox"
        )

        assert result == "10,20,100,50"
        cmd_args = mock_cli_wrapper._execute_command.call_args.args[0]
        assert "--query-id" in cmd_args
        assert "rect1" in cmd_args
        assert "--query-bbox" in cmd_args

    @pytest.mark.asyncio
    async def test_query_object_width_query_type(self, mock_cli_wrapper):
        """Test that query_type='width' selects the --query-width flag."""
        mock_cli_wrapper._execute_command = AsyncMock(return_value="42")

        result = await mock_cli_wrapper.query_object(
            input_path="test.svg", object_id="rect1", query_type="width"
        )

        assert result == "42"
        cmd_args = mock_cli_wrapper._execute_command.call_args.args[0]
        assert "--query-width" in cmd_args


class TestInkscapeCliError:
    """Test custom exception classes."""

    def test_cli_error_creation(self):
        """Test InkscapeCliError creation."""
        error = InkscapeCliError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_timeout_error_creation(self):
        """Test InkscapeTimeoutError creation."""
        error = InkscapeTimeoutError("Timeout occurred")
        assert str(error) == "Timeout occurred"
        assert isinstance(error, InkscapeCliError)

    def test_execution_error_creation(self):
        """Test InkscapeExecutionError creation."""
        error = InkscapeExecutionError("Execution failed")
        assert str(error) == "Execution failed"
        assert isinstance(error, InkscapeCliError)


class TestCliWrapperIntegration:
    """Integration tests for CLI wrapper functionality."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, mock_cli_wrapper, temp_svg_content, temp_file):
        """Test a complete workflow from file creation to querying object dimensions."""
        temp_file.write_text(temp_svg_content)
        mock_cli_wrapper._execute_command = AsyncMock(return_value="10,20,80,80")

        result = await mock_cli_wrapper.query_object(
            input_path=str(temp_file), object_id="rect1", query_type="bbox"
        )

        assert result == "10,20,80,80"

    @pytest.mark.asyncio
    async def test_error_handling_chain(self, mock_cli_wrapper):
        """Test error handling through the call chain."""
        # A missing executable at process-spawn time surfaces as InkscapeExecutionError
        with patch("asyncio.create_subprocess_exec", AsyncMock(side_effect=FileNotFoundError)):
            with pytest.raises(InkscapeExecutionError):
                await mock_cli_wrapper._execute_command(["--version"], timeout=5)

        # A nonzero return code also raises InkscapeExecutionError
        fake_process = _FakeProcess(returncode=1, stdout=b"", stderr=b"Inkscape error")
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=fake_process)):
            with pytest.raises(InkscapeExecutionError):
                await mock_cli_wrapper._execute_command(["--invalid"], timeout=5)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_cli_wrapper):
        """Test concurrent operations don't interfere."""

        async def mock_operation(task_id: int):
            fake_process = _FakeProcess(returncode=0, stdout=f"Task {task_id} completed".encode())
            with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=fake_process)):
                return await mock_cli_wrapper._execute_command(["--version"], timeout=5)

        results = await asyncio.gather(*[mock_operation(i) for i in range(3)])

        assert len(results) == 3
        assert all("completed" in r for r in results)
