"""
Unit tests for Inkscape vector operations tool.
"""

from unittest.mock import AsyncMock
import pytest

from inkscape_mcp.tools.vector_operations import inkscape_vector
from inkscape_mcp.config import InkscapeConfig
from inkscape_mcp.cli_wrapper import InkscapeCliWrapper


class TestInkscapeVectorTool:
    """Test the inkscape_vector portmanteau tool."""

    @pytest.fixture
    def mock_wrapper(self):
        """Create a mock CLI wrapper."""
        wrapper = AsyncMock(spec=InkscapeCliWrapper)
        return wrapper

    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = AsyncMock(spec=InkscapeConfig)
        config.inkscape_executable = "mock_inkscape"
        return config

    @pytest.mark.asyncio
    async def test_trace_bitmap_success(self, mock_wrapper, mock_config, temp_file):
        """Test successful bitmap tracing."""
        # Setup mock
        mock_wrapper._execute_actions.return_value = (0, "Tracing completed", "")

        result = await inkscape_vector(
            operation="trace_bitmap",
            input_path=str(temp_file),
            output_path="output.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "traced successfully" in result["message"]
        mock_wrapper._execute_actions.assert_called_once()

    @pytest.mark.asyncio
    async def test_trace_bitmap_failure(self, mock_wrapper, mock_config, temp_file):
        """Test bitmap tracing failure."""
        mock_wrapper._execute_actions.return_value = (1, "", "Error: Invalid image")

        result = await inkscape_vector(
            operation="trace_bitmap",
            input_path=str(temp_file),
            output_path="output.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is False
        assert "Failed to trace bitmap" in result["message"]

    @pytest.mark.asyncio
    async def test_apply_boolean_union(self, mock_wrapper, mock_config, temp_file):
        """Test boolean union operation."""
        mock_wrapper._execute_actions.return_value = (0, "Union completed", "")

        result = await inkscape_vector(
            operation="apply_boolean",
            boolean_type="union",
            input_path=str(temp_file),
            output_path="output.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "union" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_apply_boolean_difference(self, mock_wrapper, mock_config, temp_file):
        """Test boolean difference operation."""
        mock_wrapper._execute_actions.return_value = (0, "Difference completed", "")

        result = await inkscape_vector(
            operation="apply_boolean",
            boolean_type="difference",
            input_path=str(temp_file),
            output_path="output.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "difference" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_measure_object_success(self, mock_wrapper, mock_config, temp_file):
        """Test successful object measurement."""
        mock_wrapper.query_object.return_value = {
            "x": 10.0,
            "y": 20.0,
            "width": 100.0,
            "height": 50.0,
        }

        result = await inkscape_vector(
            operation="measure_object",
            input_path=str(temp_file),
            object_id="rect1",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert result["data"]["x"] == 10.0
        assert result["data"]["width"] == 100.0

    @pytest.mark.asyncio
    async def test_measure_object_not_found(self, mock_wrapper, mock_config, temp_file):
        """Test measurement when object not found."""
        mock_wrapper.query_object.return_value = {}

        result = await inkscape_vector(
            operation="measure_object",
            input_path=str(temp_file),
            object_id="nonexistent",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is False
        assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_generate_barcode_qr(self, mock_wrapper, mock_config, temp_file):
        """Test QR code generation."""
        mock_wrapper._execute_actions.return_value = (0, "QR generated", "")

        result = await inkscape_vector(
            operation="generate_barcode_qr",
            output_path=str(temp_file),
            barcode_data="test data",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "generated successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_generate_laser_dot(self, mock_wrapper, mock_config, temp_file):
        """Test laser dot generation (Easter egg)."""
        mock_wrapper._execute_actions.return_value = (0, "Laser dot created", "")

        result = await inkscape_vector(
            operation="generate_laser_dot",
            output_path=str(temp_file),
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "laser dot" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_construct_svg_from_description(self, mock_wrapper, mock_config, temp_file):
        """Test SVG construction from text description."""
        mock_wrapper._execute_actions.return_value = (0, "SVG constructed", "")

        result = await inkscape_vector(
            operation="construct_svg",
            output_path=str(temp_file),
            description="A blue circle with red border",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "constructed successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_optimize_svg_simplify(self, mock_wrapper, mock_config, temp_file):
        """Test SVG simplification optimization."""
        mock_wrapper._execute_actions.return_value = (0, "SVG simplified", "")

        result = await inkscape_vector(
            operation="optimize_svg",
            optimization_type="simplify",
            input_path=str(temp_file),
            output_path="optimized.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "simplified" in result["message"]

    @pytest.mark.asyncio
    async def test_optimize_svg_scour(self, mock_wrapper, mock_config, temp_file):
        """Test SVG scour optimization."""
        mock_wrapper._execute_actions.return_value = (0, "SVG scoured", "")

        result = await inkscape_vector(
            operation="optimize_svg",
            optimization_type="scour",
            input_path=str(temp_file),
            output_path="optimized.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "optimized" in result["message"]

    @pytest.mark.asyncio
    async def test_path_operations_union(self, mock_wrapper, mock_config, temp_file):
        """Test path union operation."""
        mock_wrapper._execute_actions.return_value = (0, "Paths united", "")

        result = await inkscape_vector(
            operation="path_operations",
            path_operation="union",
            input_path=str(temp_file),
            output_path="result.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "union" in result["message"]

    @pytest.mark.asyncio
    async def test_count_nodes(self, mock_wrapper, mock_config, temp_file):
        """Test node counting."""
        mock_wrapper._execute_command.return_value = (0, "42", "")

        result = await inkscape_vector(
            operation="count_nodes",
            input_path=str(temp_file),
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert result["data"]["node_count"] == 42

    @pytest.mark.asyncio
    async def test_export_dxf(self, mock_wrapper, mock_config, temp_file):
        """Test DXF export."""
        mock_wrapper._execute_actions.return_value = (0, "DXF exported", "")

        result = await inkscape_vector(
            operation="export_dxf",
            input_path=str(temp_file),
            output_path="output.dxf",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "exported successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_layers_to_files(self, mock_wrapper, mock_config, temp_file):
        """Test layer separation."""
        mock_wrapper._execute_actions.return_value = (0, "Layers separated", "")

        result = await inkscape_vector(
            operation="layers_to_files",
            input_path=str(temp_file),
            output_directory="output_dir",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "separated successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_fit_canvas_to_drawing(self, mock_wrapper, mock_config, temp_file):
        """Test canvas fitting."""
        mock_wrapper._execute_actions.return_value = (0, "Canvas fitted", "")

        result = await inkscape_vector(
            operation="fit_canvas_to_drawing",
            input_path=str(temp_file),
            output_path="fitted.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "fitted successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_object_raise(self, mock_wrapper, mock_config, temp_file):
        """Test object raising (Z-order)."""
        mock_wrapper._execute_actions.return_value = (0, "Object raised", "")

        result = await inkscape_vector(
            operation="object_raise",
            input_path=str(temp_file),
            object_id="rect1",
            output_path="raised.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "raised successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_object_lower(self, mock_wrapper, mock_config, temp_file):
        """Test object lowering (Z-order)."""
        mock_wrapper._execute_actions.return_value = (0, "Object lowered", "")

        result = await inkscape_vector(
            operation="object_lower",
            input_path=str(temp_file),
            object_id="rect1",
            output_path="lowered.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "lowered successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_set_document_units(self, mock_wrapper, mock_config, temp_file):
        """Test document units setting."""
        mock_wrapper._execute_actions.return_value = (0, "Units set", "")

        result = await inkscape_vector(
            operation="set_document_units",
            input_path=str(temp_file),
            units="mm",
            output_path="units_set.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is True
        assert "units set successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_invalid_operation(self, mock_wrapper, mock_config):
        """Test invalid operation handling."""
        result = await inkscape_vector(
            operation="invalid_operation", cli_wrapper=mock_wrapper, config=mock_config
        )

        assert result["success"] is False
        assert "Unsupported operation" in result["message"]

    @pytest.mark.asyncio
    async def test_missing_required_params(self, mock_wrapper, mock_config):
        """Test missing required parameters."""
        result = await inkscape_vector(
            operation="trace_bitmap",
            # Missing input_path and output_path
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is False
        assert "Missing required parameter" in result["message"]


class TestVectorOperationsErrorHandling:
    """Test error handling in vector operations."""

    @pytest.mark.asyncio
    async def test_wrapper_not_provided(self):
        """Test when CLI wrapper is not provided."""
        result = await inkscape_vector(operation="trace_bitmap")

        assert result["success"] is False
        assert "CLI wrapper required" in result["message"]

    @pytest.mark.asyncio
    async def test_config_not_provided(self):
        """Test when config is not provided."""
        mock_wrapper = AsyncMock()
        result = await inkscape_vector(operation="trace_bitmap", cli_wrapper=mock_wrapper)

        assert result["success"] is False
        assert "Config required" in result["message"]

    @pytest.mark.asyncio
    async def test_file_not_found(self, mock_wrapper, mock_config):
        """Test file not found error."""
        mock_wrapper._execute_actions.side_effect = FileNotFoundError("File not found")

        result = await inkscape_vector(
            operation="trace_bitmap",
            input_path="/nonexistent/file.png",
            output_path="output.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )

        assert result["success"] is False
        assert "File not found" in result["message"]


class TestVectorOperationsIntegration:
    """Integration tests for vector operations."""

    @pytest.mark.asyncio
    async def test_workflow_chain(self, mock_wrapper, mock_config, temp_file, sample_svg_file):
        """Test a complete workflow chain."""
        # Setup successful mock responses
        mock_wrapper._execute_actions.return_value = (0, "Operation successful", "")
        mock_wrapper.query_object.return_value = {"x": 10, "y": 20, "width": 100, "height": 50}

        # Step 1: Measure object
        measure_result = await inkscape_vector(
            operation="measure_object",
            input_path=str(sample_svg_file),
            object_id="rect1",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )
        assert measure_result["success"] is True

        # Step 2: Apply boolean operation
        boolean_result = await inkscape_vector(
            operation="apply_boolean",
            boolean_type="union",
            input_path=str(sample_svg_file),
            output_path="union_result.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )
        assert boolean_result["success"] is True

        # Step 3: Optimize result
        optimize_result = await inkscape_vector(
            operation="optimize_svg",
            optimization_type="simplify",
            input_path="union_result.svg",
            output_path="optimized.svg",
            cli_wrapper=mock_wrapper,
            config=mock_config,
        )
        assert optimize_result["success"] is True

        # Verify all operations were called
        assert mock_wrapper._execute_actions.call_count >= 2  # boolean + optimize
        assert mock_wrapper.query_object.call_count == 1  # measure
