"""
Unit tests for Inkscape CLI wrapper module.
"""

import asyncio
from unittest.mock import Mock, patch

import pytest

from inkscape_mcp.cli_wrapper import (
    InkscapeCliWrapper,
    InkscapeCliError,
    InkscapeTimeoutError,
    InkscapeExecutionError,
)


class TestInkscapeCliWrapper:
    """Test InkscapeCliWrapper class functionality."""

    def test_initialization(self, mock_inkscape_config):
        """Test wrapper initializes correctly."""
        wrapper = InkscapeCliWrapper(mock_inkscape_config)

        assert wrapper.config == mock_inkscape_config
        assert wrapper.config.inkscape_executable.endswith("inkscape.exe")

    def test_initialization_invalid_config(self):
        """Test initialization with invalid config raises error."""
        with pytest.raises(AttributeError):
            InkscapeCliWrapper(None)

    @pytest.mark.asyncio
    async def test_execute_command_success(self, mock_cli_wrapper, mock_successful_inkscape_run):
        """Test successful command execution."""
        with patch("subprocess.run", side_effect=mock_successful_inkscape_run):
            returncode, stdout, stderr = await mock_cli_wrapper._execute_command(["--version"])

            assert returncode == 0
            assert stdout == '{"success": true, "data": "test output"}'
            assert stderr == ""

    @pytest.mark.asyncio
    async def test_execute_command_failure(self, mock_cli_wrapper, mock_failed_inkscape_run):
        """Test failed command execution."""
        with patch("subprocess.run", side_effect=mock_failed_inkscape_run):
            with pytest.raises(InkscapeExecutionError):
                await mock_cli_wrapper._execute_command(["--invalid-option"])

    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, mock_cli_wrapper):
        """Test command execution timeout."""
        with patch("subprocess.run", side_effect=asyncio.TimeoutError):
            with pytest.raises(InkscapeTimeoutError):
                await mock_cli_wrapper._execute_command(["--version"], timeout=0.001)

    @pytest.mark.asyncio
    async def test_execute_actions_success(self, mock_cli_wrapper):
        """Test successful actions execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Actions executed successfully"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            returncode, stdout, stderr = await mock_cli_wrapper._execute_actions(
                "select-all;export-do", input_path="test.svg"
            )

            assert returncode == 0
            assert "Actions executed successfully" in stdout

    @pytest.mark.asyncio
    async def test_execute_actions_with_export(self, mock_cli_wrapper):
        """Test actions execution with export filename."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            returncode, stdout, stderr = await mock_cli_wrapper._execute_actions(
                "select-all;object-to-path", input_path="test.svg", output_path="output.svg"
            )

            assert returncode == 0

    @pytest.mark.asyncio
    async def test_export_file_success(self, mock_cli_wrapper, temp_file):
        """Test successful file export."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            success, message = await mock_cli_wrapper.export_file(
                input_path=str(temp_file), output_path="output.png", format="png", dpi=300
            )

            assert success is True
            assert "exported successfully" in message

    @pytest.mark.asyncio
    async def test_export_file_invalid_format(self, mock_cli_wrapper, temp_file):
        """Test export with invalid format."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            await mock_cli_wrapper.export_file(
                input_path=str(temp_file), output_path="output.invalid", format="invalid"
            )

    @pytest.mark.asyncio
    async def test_query_object_success(self, mock_cli_wrapper):
        """Test successful object querying."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "10,20,100,50"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = await mock_cli_wrapper.query_object(
                input_path="test.svg", object_id="rect1", properties=["x", "y", "width", "height"]
            )

            assert "x" in result
            assert "y" in result
            assert result["x"] == 10
            assert result["y"] == 20

    @pytest.mark.asyncio
    async def test_query_object_invalid_output(self, mock_cli_wrapper):
        """Test object query with invalid output."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid,output,format"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = await mock_cli_wrapper.query_object(
                input_path="test.svg", object_id="rect1", properties=["x"]
            )

            # Should handle gracefully
            assert isinstance(result, dict)

    def test_build_command_base(self, mock_cli_wrapper):
        """Test basic command building."""
        cmd = mock_cli_wrapper._build_command_base("test.svg")
        expected = [str(mock_cli_wrapper.config.inkscape_executable), "--batch-process", "test.svg"]
        assert cmd == expected

    def test_build_command_with_actions(self, mock_cli_wrapper):
        """Test command building with actions."""
        cmd = mock_cli_wrapper._build_command_with_actions(
            "select-all;export-do", "test.svg", "output.svg"
        )
        assert "--actions" in cmd
        assert "select-all;export-do" in cmd
        assert "export-filename:output.svg" in cmd

    def test_validate_input_path(self, mock_cli_wrapper, temp_file):
        """Test input path validation."""
        # Should not raise for existing file
        mock_cli_wrapper._validate_input_path(str(temp_file))

        # Should raise for nonexistent file
        with pytest.raises(FileNotFoundError):
            mock_cli_wrapper._validate_input_path("/nonexistent/file.svg")

    def test_validate_output_path(self, mock_cli_wrapper, temp_dir):
        """Test output path validation."""
        output_path = temp_dir / "output.svg"

        # Should create parent directories
        mock_cli_wrapper._validate_output_path(str(output_path))
        assert output_path.parent.exists()

    def test_parse_query_output(self, mock_cli_wrapper):
        """Test parsing of query command output."""
        # Test valid output
        output = "10,20,100,50"
        result = mock_cli_wrapper._parse_query_output(output, ["x", "y", "width", "height"])
        assert result == {"x": 10, "y": 20, "width": 100, "height": 50}

        # Test invalid output
        result = mock_cli_wrapper._parse_query_output("invalid", ["x"])
        assert result == {"x": None}

        # Test mismatched lengths
        result = mock_cli_wrapper._parse_query_output("10,20", ["x", "y", "width"])
        assert result == {"x": 10, "y": 20, "width": None}


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
        """Test a complete workflow from file creation to processing."""
        # Create test SVG file
        temp_file.write_text(temp_svg_content)

        # Mock successful operations
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "10,20,80,80"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            # Query object dimensions
            result = await mock_cli_wrapper.query_object(
                input_path=str(temp_file),
                object_id="rect1",
                properties=["x", "y", "width", "height"],
            )

            assert result["x"] == 10
            assert result["y"] == 20
            assert result["width"] == 80
            assert result["height"] == 80

    @pytest.mark.asyncio
    async def test_error_handling_chain(self, mock_cli_wrapper):
        """Test error handling through the call chain."""
        # Test file not found
        with pytest.raises(FileNotFoundError):
            await mock_cli_wrapper.export_file(
                input_path="/nonexistent/file.svg", output_path="output.png"
            )

        # Test subprocess failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Inkscape error"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(InkscapeExecutionError):
                await mock_cli_wrapper._execute_command(["--invalid"])

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_cli_wrapper):
        """Test concurrent operations don't interfere."""

        async def mock_operation(task_id: int):
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = f"Task {task_id} completed"
            mock_result.stderr = ""

            with patch("subprocess.run", return_value=mock_result):
                returncode, stdout, stderr = await mock_cli_wrapper._execute_command(["--version"])
                return returncode, stdout

        # Run multiple operations concurrently
        tasks = [mock_operation(i) for i in range(3)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(returncode == 0 for returncode, _ in results)
        assert len(results) == 3
