"""
Comprehensive test configuration and fixtures for Inkscape MCP Server.

This conftest.py provides shared fixtures for unit and integration testing,
including mocks, test data, and environment setup.
"""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

import pytest

# Import the modules we're testing
from inkscape_mcp.config import InkscapeConfig
from inkscape_mcp.cli_wrapper import InkscapeCliWrapper
from inkscape_mcp.inkscape_detector import InkscapeDetector


# ===== FIXTURE SCOPE DEFINITIONS =====


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for the entire test session."""
    temp_path = Path(tempfile.mkdtemp(prefix="inkscape_mcp_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_file():
    """Create a temporary file that gets cleaned up after each test."""
    fd, path = tempfile.mkstemp(suffix=".svg")
    file_path = Path(path)
    os.close(fd)  # Close the file descriptor

    yield file_path

    if file_path.exists():
        file_path.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def temp_svg_content():
    """Return sample SVG content for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="80" height="80" fill="blue"/>
</svg>"""


@pytest.fixture(scope="function")
def sample_svg_file(temp_file, temp_svg_content):
    """Create a temporary SVG file with sample content."""
    temp_file.write_text(temp_svg_content)
    return temp_file


# ===== MOCK FIXTURES =====


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for testing CLI operations."""
    with patch("subprocess.run") as mock_run:
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Mock Inkscape output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        yield mock_run


@pytest.fixture
def mock_inkscape_path():
    """Mock Inkscape executable path."""
    return Path("C:/Program Files/Inkscape/bin/inkscape.exe")


@pytest.fixture
def mock_inkscape_config(mock_inkscape_path):
    """Create a mock InkscapeConfig for testing."""
    config = InkscapeConfig()
    config.inkscape_executable = str(mock_inkscape_path)
    config.max_concurrent_processes = 2
    config.process_timeout = 30.0
    return config


@pytest.fixture
def mock_cli_wrapper(mock_inkscape_config):
    """Create a mock InkscapeCliWrapper for testing."""
    wrapper = InkscapeCliWrapper(mock_inkscape_config)
    return wrapper


@pytest.fixture
def mock_inkscape_detector():
    """Create a mock InkscapeDetector."""
    detector = InkscapeDetector()
    return detector


@pytest.fixture
def mock_successful_inkscape_run():
    """Mock a successful Inkscape execution."""

    def _mock_run(cmd_args, **kwargs):
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"success": true, "data": "test output"}'
        mock_result.stderr = ""
        return mock_result

    return _mock_run


@pytest.fixture
def mock_failed_inkscape_run():
    """Mock a failed Inkscape execution."""

    def _mock_run(cmd_args, **kwargs):
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: File not found"
        return mock_result

    return _mock_run


# ===== ASYNC FIXTURES =====


@pytest.fixture
async def async_mock_cli_wrapper(mock_inkscape_config):
    """Create an async mock CLI wrapper."""
    wrapper = InkscapeCliWrapper(mock_inkscape_config)

    # Mock the async methods
    wrapper._execute_command = AsyncMock(return_value=(0, "success", ""))
    wrapper._execute_actions = AsyncMock(return_value=(0, "actions executed", ""))

    return wrapper


@pytest.fixture
async def async_mock_config():
    """Create an async mock config."""
    config = Mock(spec=InkscapeConfig)
    config.inkscape_executable = "mock_inkscape"
    config.max_concurrent_processes = 2
    config.process_timeout = 30.0
    return config


# ===== TEST DATA FIXTURES =====


@pytest.fixture
def test_svg_data():
    """Return comprehensive test SVG data."""
    return {
        "minimal": """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/></svg>""",
        "with_objects": """<?xml version="1.0"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect id="rect1" x="10" y="10" width="50" height="50" fill="red"/>
  <circle id="circle1" cx="100" cy="100" r="30" fill="blue"/>
  <path id="path1" d="M150 150 L180 180 L120 180 Z" fill="green"/>
</svg>""",
        "complex": """<?xml version="1.0"?>
<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:red"/>
      <stop offset="100%" style="stop-color:blue"/>
    </linearGradient>
  </defs>
  <g id="group1">
    <rect x="20" y="20" width="100" height="100" fill="url(#grad1)"/>
    <text x="50" y="50" font-family="Arial" font-size="14">Test</text>
  </g>
</svg>""",
    }


@pytest.fixture
def inkscape_actions_test_data():
    """Test data for Inkscape actions."""
    return {
        "select_all_union": "select-all;selection-union;export-filename:test.svg;export-do",
        "trace_bitmap": "select-all;object-to-path;export-filename:test.svg;export-do",
        "boolean_operations": "select-by-id:rect1;select-by-id:rect2;selection-union;export-filename:test.svg;export-do",
        "measure_object": "select-by-id:rect1;query-x;query-y;query-width;query-height",
        "generate_qr": "select-all;object-to-path;export-filename:qr.svg;export-do",
    }


@pytest.fixture
def expected_cli_outputs():
    """Expected CLI output formats for different operations."""
    return {
        "query_dimensions": "10,20,100,50",
        "query_objects": """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <rect id="rect1" x="10" y="20" width="100" height="50"/>
</svg>""",
        "version_info": "Inkscape 1.3 (1:1.3+202307231459+0~ubuntu0.22.04.1)",
        "export_success": "",  # Empty stdout on successful export
        "error_file_not_found": "Error: File not found or not readable",
    }


# ===== ENVIRONMENT FIXTURES =====


@pytest.fixture
def clean_env():
    """Provide a clean environment for testing."""
    original_env = os.environ.copy()

    # Remove any inkscape-related environment variables
    inkscape_vars = [k for k in os.environ.keys() if "inkscape" in k.lower()]
    for var in inkscape_vars:
        del os.environ[var]

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_inkscape_env(mock_inkscape_path):
    """Set up environment with mock Inkscape path."""
    original_path = os.environ.get("PATH", "")
    mock_inkscape_dir = str(mock_inkscape_path.parent)

    # Add mock inkscape to PATH
    os.environ["PATH"] = f"{mock_inkscape_dir}{os.pathsep}{original_path}"

    yield

    # Restore original PATH
    os.environ["PATH"] = original_path


# ===== PERFORMANCE TESTING FIXTURES =====


@pytest.fixture
def performance_config():
    """Configuration optimized for performance testing."""
    config = InkscapeConfig()
    config.max_concurrent_processes = 1  # Sequential for accurate timing
    config.process_timeout = 60.0  # Longer timeout for performance tests
    return config


@pytest.fixture
def benchmark_data():
    """Generate benchmark test data."""
    return {
        "small_svg": create_test_svg(100, 100, 5),  # 5 objects
        "medium_svg": create_test_svg(500, 500, 50),  # 50 objects
        "large_svg": create_test_svg(1000, 1000, 200),  # 200 objects
    }


def create_test_svg(width: int, height: int, num_objects: int) -> str:
    """Create a test SVG with specified dimensions and object count."""
    svg_parts = [
        f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'''
    ]

    for i in range(num_objects):
        x = (i * width) // num_objects
        y = (i * height) // num_objects
        size = min(width, height) // (num_objects * 2) or 10
        svg_parts.append(
            f'  <rect id="obj{i}" x="{x}" y="{y}" width="{size}" height="{size}" fill="blue"/>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


# ===== ERROR CONDITION FIXTURES =====


@pytest.fixture
def error_conditions():
    """Common error conditions for testing."""
    return {
        "timeout": {"timeout": 0.001, "expected_error": "TimeoutError"},
        "file_not_found": {
            "input_path": "/nonexistent/file.svg",
            "expected_error": "FileNotFoundError",
        },
        "invalid_svg": {"content": "<invalid xml>", "expected_error": "ValueError"},
        "inkscape_not_found": {
            "executable": "/nonexistent/inkscape",
            "expected_error": "FileNotFoundError",
        },
        "permission_denied": {
            "output_path": "/root/forbidden.svg",
            "expected_error": "PermissionError",
        },
    }


# ===== INTEGRATION TEST FIXTURES =====


@pytest.fixture(scope="session")
def integration_config():
    """Configuration for integration tests."""
    config = InkscapeConfig()
    config.max_concurrent_processes = 2
    config.process_timeout = 30.0

    # Use real inkscape if available, otherwise skip integration tests
    detector = InkscapeDetector()
    inkscape_path = detector.detect_inkscape_installation()
    if inkscape_path:
        config.inkscape_executable = str(inkscape_path)
    else:
        pytest.skip("Inkscape not found - skipping integration tests")

    return config


@pytest.fixture(scope="session")
async def integration_wrapper(integration_config):
    """Real CLI wrapper for integration tests."""
    wrapper = InkscapeCliWrapper(integration_config)
    yield wrapper


# ===== UTILITY FIXTURES =====


@pytest.fixture
def assert_success():
    """Assertion helper for successful operations."""

    def _assert_success(result: Dict[str, Any], operation: str = ""):
        assert isinstance(result, dict), f"Result should be dict, got {type(result)}"
        assert result.get("success") is True, (
            f"Operation {operation} should succeed: {result.get('message', 'No message')}"
        )
        assert "result" in result or "data" in result, f"Operation {operation} should return data"

    return _assert_success


@pytest.fixture
def assert_error():
    """Assertion helper for error conditions."""

    def _assert_error(result: Dict[str, Any], expected_error_type: Optional[str] = None):
        assert isinstance(result, dict), f"Result should be dict, got {type(result)}"
        assert result.get("success") is False, f"Operation should fail: {result}"

        if expected_error_type:
            error_msg = result.get("error", "").lower()
            assert expected_error_type.lower() in error_msg, (
                f"Expected {expected_error_type} in error: {error_msg}"
            )

    return _assert_error


# ===== ASYNC CONTEXT MANAGERS =====


@pytest.fixture
async def temp_async_file():
    """Create a temporary file for async operations."""
    fd, path = tempfile.mkstemp(suffix=".svg")
    file_path = Path(path)
    os.close(fd)

    yield file_path

    if file_path.exists():
        file_path.unlink(missing_ok=True)
