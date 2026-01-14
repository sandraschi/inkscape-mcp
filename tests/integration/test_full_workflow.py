"""
Integration tests for complete Inkscape MCP workflows.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from inkscape_mcp.tools import inkscape_file, inkscape_vector, inkscape_analysis, inkscape_system
from inkscape_mcp.config import InkscapeConfig
from inkscape_mcp.cli_wrapper import InkscapeCliWrapper


@pytest.mark.integration
class TestCompleteWorkflows:
    """Test complete end-to-end workflows using real components."""

    @pytest.fixture
    def real_config(self, integration_config):
        """Use real config for integration tests."""
        return integration_config

    @pytest.fixture
    async def real_wrapper(self, real_config):
        """Use real CLI wrapper for integration tests."""
        wrapper = InkscapeCliWrapper(real_config)
        yield wrapper

    @pytest.mark.asyncio
    async def test_file_operations_workflow(
        self, real_wrapper, real_config, temp_file, temp_svg_content
    ):
        """Test complete file operations workflow."""
        # Create test SVG
        temp_file.write_text(temp_svg_content)

        # Test file info
        result = await inkscape_file(
            operation="get_svg_info",
            input_path=str(temp_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is True
        assert "file_info" in result["data"]

        # Test file validation
        result = await inkscape_file(
            operation="validate_svg",
            input_path=str(temp_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is True
        assert "valid" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_vector_operations_workflow(self, real_wrapper, real_config, sample_svg_file):
        """Test complete vector operations workflow."""
        # First analyze the SVG to get object IDs
        analysis_result = await inkscape_analysis(
            operation="objects",
            input_path=str(sample_svg_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert analysis_result["success"] is True

        # If we have objects, test vector operations
        objects = analysis_result.get("data", {}).get("objects", [])
        if objects:
            first_object = objects[0]

            # Measure the object
            measure_result = await inkscape_vector(
                operation="measure_object",
                input_path=str(sample_svg_file),
                object_id=first_object["id"],
                cli_wrapper=real_wrapper,
                config=real_config,
            )

            assert measure_result["success"] is True
            assert "dimensions" in measure_result["data"]

    @pytest.mark.asyncio
    async def test_analysis_workflow(self, real_wrapper, real_config, sample_svg_file):
        """Test complete analysis workflow."""
        # Get comprehensive analysis
        result = await inkscape_analysis(
            operation="objects",
            input_path=str(sample_svg_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is True
        assert "objects" in result["data"]

        # Test document info
        doc_result = await inkscape_analysis(
            operation="document_info",
            input_path=str(sample_svg_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert doc_result["success"] is True

    @pytest.mark.asyncio
    async def test_system_operations_workflow(self, real_wrapper, real_config):
        """Test system operations workflow."""
        # Test status
        result = await inkscape_system(
            operation="status", cli_wrapper=real_wrapper, config=real_config
        )

        assert result["success"] is True
        assert "inkscape_version" in result["data"]

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, real_wrapper, real_config):
        """Test error handling and recovery."""
        # Test with invalid file
        result = await inkscape_file(
            operation="get_svg_info",
            input_path="/nonexistent/file.svg",
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is False
        assert "error" in result

        # Test with invalid operation
        result = await inkscape_vector(
            operation="invalid_operation", cli_wrapper=real_wrapper, config=real_config
        )

        assert result["success"] is False
        assert "Unsupported operation" in result["message"]


@pytest.mark.integration
class TestPerformanceWorkflows:
    """Test performance characteristics of workflows."""

    @pytest.fixture
    def performance_config(self):
        """Config optimized for performance testing."""
        config = InkscapeConfig()
        config.max_concurrent_processes = 1  # Sequential for accurate timing
        config.process_timeout = 60.0
        return config

    @pytest.fixture
    async def perf_wrapper(self, performance_config):
        """Wrapper for performance testing."""
        wrapper = InkscapeCliWrapper(performance_config)
        yield wrapper

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(
        self, perf_wrapper, performance_config, benchmark_data
    ):
        """Test performance of concurrent operations."""
        # This would test multiple operations running concurrently
        # For now, just test sequential performance
        svg_file = benchmark_data["small_svg"]

        import time

        start_time = time.time()

        # Run multiple operations
        tasks = []
        for i in range(3):
            task = inkscape_analysis(
                operation="objects",
                input_path=str(svg_file),
                cli_wrapper=perf_wrapper,
                config=performance_config,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # All should succeed
        assert all(r["success"] for r in results)

        # Should complete within reasonable time
        duration = end_time - start_time
        assert duration < 10.0  # Should be fast

    @pytest.mark.asyncio
    async def test_memory_usage_workflow(self, perf_wrapper, performance_config, benchmark_data):
        """Test memory usage during operations."""
        # This would monitor memory usage during operations
        # For now, just run operations and ensure they complete
        svg_file = benchmark_data["medium_svg"]

        result = await inkscape_analysis(
            operation="objects",
            input_path=str(svg_file),
            cli_wrapper=perf_wrapper,
            config=performance_config,
        )

        assert result["success"] is True


@pytest.mark.integration
class TestCrossPlatformWorkflows:
    """Test workflows across different platforms."""

    @pytest.mark.asyncio
    async def test_file_path_handling(self, real_wrapper, real_config, temp_file):
        """Test file path handling across platforms."""
        # Create test file
        test_content = '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/></svg>'
        temp_file.write_text(test_content)

        # Test with different path formats
        result = await inkscape_file(
            operation="validate_svg",
            input_path=str(temp_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_unicode_filename_handling(self, real_wrapper, real_config):
        """Test handling of Unicode filenames."""
        # Create file with Unicode name
        unicode_name = "测试_svg_файл.svg"
        test_path = Path(tempfile.gettempdir()) / unicode_name

        try:
            test_content = '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40"/></svg>'
            test_path.write_text(test_content)

            result = await inkscape_file(
                operation="get_svg_info",
                input_path=str(test_path),
                cli_wrapper=real_wrapper,
                config=real_config,
            )

            assert result["success"] is True

        finally:
            if test_path.exists():
                test_path.unlink()


@pytest.mark.integration
class TestRealInkscapeOperations:
    """Test operations using real Inkscape if available."""

    @pytest.fixture
    def inkscape_available(self, integration_config):
        """Check if Inkscape is actually available."""
        from inkscape_mcp.inkscape_detector import InkscapeDetector

        detector = InkscapeDetector()
        return detector.detect_inkscape_installation() is not None

    @pytest.mark.skipif("not inkscape_available")
    @pytest.mark.asyncio
    async def test_real_inkscape_version(self, real_wrapper, real_config):
        """Test getting real Inkscape version."""
        result = await inkscape_system(
            operation="status", cli_wrapper=real_wrapper, config=real_config
        )

        assert result["success"] is True
        assert "inkscape_version" in result["data"]
        assert result["data"]["inkscape_version"].startswith("Inkscape")

    @pytest.mark.skipif("not inkscape_available")
    @pytest.mark.asyncio
    async def test_real_svg_processing(self, real_wrapper, real_config, sample_svg_file):
        """Test real SVG processing operations."""
        # Test document info
        result = await inkscape_analysis(
            operation="document_info",
            input_path=str(sample_svg_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is True
        assert "document_info" in result["data"]

        # Test object analysis
        result = await inkscape_analysis(
            operation="objects",
            input_path=str(sample_svg_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is True
        # May or may not have objects, but should not error
