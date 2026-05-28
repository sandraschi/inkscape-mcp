"""Phase 1 Agent Lab tool tests (inkscape_render + execution_mode)."""

from unittest.mock import AsyncMock, patch

import pytest

from inkscape_mcp.config import InkscapeConfig
from inkscape_mcp.tools.render_tools import inkscape_render
from inkscape_mcp.tools.system import inkscape_system
from inkscape_mcp.utils.execution_mode import describe_execution_mode


class TestInkscapeRenderTool:
    """Tests for inkscape_render portmanteau."""

    @pytest.fixture
    def mock_wrapper(self):
        wrapper = AsyncMock()
        wrapper._execute_actions = AsyncMock(return_value=(0, "ok", ""))
        wrapper._execute_command = AsyncMock(return_value="800.0")
        return wrapper

    @pytest.fixture
    def mock_config(self, tmp_path):
        config = InkscapeConfig()
        config.inkscape_executable = "mock_inkscape"
        config.process_timeout = 30
        config.temp_directory = str(tmp_path)
        return config

    @pytest.mark.asyncio
    async def test_export_preview_success(
        self, mock_wrapper, mock_config, sample_svg_file, tmp_path
    ):
        output = tmp_path / "preview.png"
        result = await inkscape_render(
            operation="export_preview",
            input_path=str(sample_svg_file),
            output_path=str(output),
            dpi=192,
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert result["operation"] == "export_preview"
        assert result["data"]["dpi"] == 192
        assert result["data"]["agent_vision"] is True
        mock_wrapper._execute_actions.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_preview_missing_input(self, mock_wrapper, mock_config):
        result = await inkscape_render(
            operation="export_preview",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is False
        assert "input_path" in result["message"]

    @pytest.mark.asyncio
    async def test_export_multi_dpi(self, mock_wrapper, mock_config, sample_svg_file, tmp_path):
        result = await inkscape_render(
            operation="export_multi_dpi",
            input_path=str(sample_svg_file),
            output_path=str(tmp_path / "multi.png"),
            dpi_list="96,128",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert len(result["data"]["exports"]) == 2
        assert mock_wrapper._execute_actions.call_count == 2

    @pytest.mark.asyncio
    async def test_get_document_summary(self, mock_wrapper, mock_config, sample_svg_file):
        result = await inkscape_render(
            operation="get_document_summary",
            input_path=str(sample_svg_file),
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "statistics" in result["data"]
        assert "validation" in result["data"]
        assert "recommended_next" in result["data"]


class TestExecutionMode:
    """Tests for Hands-In vs Hands-Off guidance."""

    @pytest.mark.asyncio
    async def test_hands_off_by_default(self):
        wrapper = AsyncMock()
        wrapper._execute_command = AsyncMock(return_value="Inkscape 1.3")
        config = InkscapeConfig()
        config.inkscape_executable = "mock_inkscape"

        with patch(
            "inkscape_mcp.utils.execution_mode.detect_inkscape_gui_process",
            return_value=False,
        ):
            result = await describe_execution_mode(cli_wrapper=wrapper, config=config)

        assert result["mode"] == "hands_off"
        assert result["cli_available"] is True

    @pytest.mark.asyncio
    async def test_hands_in_when_gui_watch(self):
        wrapper = AsyncMock()
        wrapper._execute_command = AsyncMock(return_value="Inkscape 1.3")

        with patch.dict("os.environ", {"INKSCAPE_GUI_WATCH": "1"}):
            result = await describe_execution_mode(cli_wrapper=wrapper, config=InkscapeConfig())

        assert result["mode"] == "hands_in"
        assert result["gui_watch"] is True

    @pytest.mark.asyncio
    async def test_system_execution_mode_operation(self):
        wrapper = AsyncMock()
        wrapper._execute_command = AsyncMock(return_value="Inkscape 1.3")
        config = InkscapeConfig()
        config.inkscape_executable = "mock_inkscape"

        with patch(
            "inkscape_mcp.utils.execution_mode.detect_inkscape_gui_process",
            return_value=False,
        ):
            result = await inkscape_system(
                operation="execution_mode",
                cli_wrapper=wrapper,
                config=config,
            )

        assert result["success"] is True
        assert result["operation"] == "execution_mode"
        assert result["data"]["mode"] == "hands_off"

    @pytest.mark.asyncio
    async def test_system_status_includes_render_tool(self):
        wrapper = AsyncMock()
        wrapper._execute_command = AsyncMock(return_value="Inkscape 1.3")
        config = InkscapeConfig()
        config.inkscape_executable = "mock_inkscape"

        result = await inkscape_system(
            operation="status",
            cli_wrapper=wrapper,
            config=config,
        )

        assert result["success"] is True
        assert result["data"]["tools"]["render"] == "available"
        assert result["data"]["server"]["agent_lab_phase"] == 6
