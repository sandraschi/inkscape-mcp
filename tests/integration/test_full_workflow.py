"""
Integration tests for complete Inkscape MCP workflows.
"""

import asyncio
import tempfile
import time
from pathlib import Path

import pytest
import pytest_asyncio

from inkscape_mcp.cli_wrapper import InkscapeCliWrapper
from inkscape_mcp.config import InkscapeConfig
from inkscape_mcp.tools import inkscape_analysis
from inkscape_mcp.tools import inkscape_file
from inkscape_mcp.tools import inkscape_system
from inkscape_mcp.tools import inkscape_vector


@pytest.fixture(scope="session")
def real_config(integration_config):
    """Use real config for integration tests. Session-scoped fixture skips if Inkscape isn't found."""
    return integration_config


@pytest_asyncio.fixture
async def real_wrapper(real_config):
    """Use a real CLI wrapper for integration tests.

    Must be a pytest_asyncio.fixture (not a bare @pytest.fixture) - this project's pytest.ini
    has an invalid [tool:pytest] section header (should be [pytest]) so its asyncio_mode=auto
    setting is silently never applied and pytest-asyncio runs in strict mode, where an
    `async def` fixture decorated with plain @pytest.fixture is never awaited and is handed to
    tests as a raw async_generator object instead of the yielded InkscapeCliWrapper.
    """
    wrapper = InkscapeCliWrapper(real_config)
    yield wrapper


@pytest.mark.integration
class TestCompleteWorkflows:
    """Test complete end-to-end workflows using real components."""

    @pytest.mark.asyncio
    async def test_file_operations_workflow(
        self, real_wrapper, real_config, temp_file, temp_svg_content
    ):
        """Test complete file operations workflow."""
        # Create test SVG
        temp_file.write_text(temp_svg_content)

        # Test file info (the real operation name is "info", not "get_svg_info")
        result = await inkscape_file(
            operation="info",
            input_path=str(temp_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is True
        assert "width" in result["data"]

        # Test file validation (the real operation name is "validate", not "validate_svg")
        result = await inkscape_file(
            operation="validate",
            input_path=str(temp_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is True
        assert result["data"]["valid"] is True

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
            assert "width" in measure_result["data"]

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

        # Test document statistics (the real operation name is "statistics", not "document_info")
        doc_result = await inkscape_analysis(
            operation="statistics",
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
        # Inkscape version info is nested under data["inkscape"], not a top-level
        # "inkscape_version" key.
        assert result["data"]["inkscape"]["available"] is True

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, real_wrapper, real_config):
        """Test error handling and recovery."""
        # Test with invalid file
        result = await inkscape_file(
            operation="info",
            input_path="/nonexistent/file.svg",
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is False
        assert "error" in result

        # Test with invalid operation - real message is "not yet implemented",
        # not "Unsupported operation".
        result = await inkscape_vector(
            operation="invalid_operation", cli_wrapper=real_wrapper, config=real_config
        )

        assert result["success"] is False
        assert "not yet implemented" in result["message"]


@pytest.mark.integration
class TestPerformanceWorkflows:
    """Test performance characteristics of workflows."""

    @pytest.fixture
    def performance_config(self, real_config):
        """Config optimized for performance testing, reusing the detected Inkscape executable."""
        return InkscapeConfig(
            inkscape_executable=real_config.inkscape_executable,
            max_concurrent_processes=1,  # Sequential for accurate timing
            process_timeout=60,
        )

    @pytest_asyncio.fixture
    async def perf_wrapper(self, performance_config):
        """Wrapper for performance testing."""
        wrapper = InkscapeCliWrapper(performance_config)
        yield wrapper

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(
        self, perf_wrapper, performance_config, benchmark_data, tmp_path
    ):
        """Test performance of concurrent operations."""
        # benchmark_data holds SVG content strings, not file paths - write one to disk first.
        svg_file = tmp_path / "small.svg"
        svg_file.write_text(benchmark_data["small_svg"])

        start_time = time.time()

        # Run multiple operations
        tasks = [
            inkscape_analysis(
                operation="objects",
                input_path=str(svg_file),
                cli_wrapper=perf_wrapper,
                config=performance_config,
            )
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # All should succeed
        assert all(r["success"] for r in results)

        # Should complete within reasonable time
        duration = end_time - start_time
        assert duration < 10.0  # Should be fast

    @pytest.mark.asyncio
    async def test_memory_usage_workflow(
        self, perf_wrapper, performance_config, benchmark_data, tmp_path
    ):
        """Test memory usage during operations."""
        svg_file = tmp_path / "medium.svg"
        svg_file.write_text(benchmark_data["medium_svg"])

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
            operation="validate",
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
        # Use the configured temp dir, not tempfile.gettempdir() directly: a
        # snap-confined Inkscape can't read the system temp dir on Linux (see
        # inkscape_mcp.config._default_temp_directory).
        test_path = Path(real_config.temp_directory) / unicode_name

        try:
            test_content = '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40"/></svg>'
            test_path.write_text(test_content)

            result = await inkscape_file(
                operation="info",
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
    """Test operations using real Inkscape.

    No skipif is needed here: the module-level `real_config` fixture (via `integration_config`
    in conftest.py) already calls pytest.skip() at fixture setup if no Inkscape installation is
    detected, so every test in this class is skipped automatically when Inkscape is absent. The
    previous `@pytest.mark.skipif("not inkscape_available")` never worked - skipif string
    conditions are evaluated without fixture values in scope, so `inkscape_available` was always
    a NameError.
    """

    @pytest.mark.asyncio
    async def test_real_inkscape_version(self, real_wrapper, real_config):
        """Test getting real Inkscape version."""
        result = await inkscape_system(
            operation="status", cli_wrapper=real_wrapper, config=real_config
        )

        assert result["success"] is True
        assert result["data"]["inkscape"]["version"].startswith("Inkscape")

    @pytest.mark.asyncio
    async def test_real_svg_processing(self, real_wrapper, real_config, sample_svg_file):
        """Test real SVG processing operations."""
        # Test document statistics (the real operation name is "statistics")
        result = await inkscape_analysis(
            operation="statistics",
            input_path=str(sample_svg_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is True

        # Test object analysis
        result = await inkscape_analysis(
            operation="objects",
            input_path=str(sample_svg_file),
            cli_wrapper=real_wrapper,
            config=real_config,
        )

        assert result["success"] is True
        # May or may not have objects, but should not error
