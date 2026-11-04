"""
Unit tests for Inkscape detector module.
"""

import logging
import os
import platform
import sys
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from inkscape_mcp.inkscape_detector import InkscapeDetector


class TestInkscapeDetector:
    """Test InkscapeDetector class functionality."""

    def test_initialization(self):
        """Test detector initializes correctly."""
        detector = InkscapeDetector()
        assert detector is not None
        assert hasattr(detector, "detect_inkscape_installation")

    @patch("platform.system")
    def test_detect_on_windows(self, mock_platform):
        """Test detection on Windows."""
        mock_platform.return_value = "Windows"
        detector = InkscapeDetector()

        with patch.object(
            detector, "_detect_windows", return_value=Path("C:/Program Files/Inkscape/inkscape.exe")
        ):
            result = detector.detect_inkscape_installation()
            assert result == Path("C:/Program Files/Inkscape/inkscape.exe")

    @patch("platform.system")
    def test_detect_on_linux(self, mock_platform):
        """Test detection on Linux."""
        mock_platform.return_value = "Linux"
        detector = InkscapeDetector()

        with patch.object(detector, "_detect_linux", return_value=Path("/usr/bin/inkscape")):
            result = detector.detect_inkscape_installation()
            assert result == Path("/usr/bin/inkscape")

    @patch("platform.system")
    def test_detect_on_macos(self, mock_platform):
        """Test detection on macOS."""
        mock_platform.return_value = "Darwin"
        detector = InkscapeDetector()

        with patch.object(
            detector,
            "_detect_macos",
            return_value=Path("/Applications/Inkscape.app/Contents/MacOS/inkscape"),
        ):
            result = detector.detect_inkscape_installation()
            assert result == Path("/Applications/Inkscape.app/Contents/MacOS/inkscape")

    @patch("platform.system")
    def test_detect_unsupported_platform(self, mock_platform):
        """Test detection on unsupported platform."""
        mock_platform.return_value = "UnsupportedOS"
        detector = InkscapeDetector()

        result = detector.detect_inkscape_installation()
        assert result is None

    def test_windows_detection_paths(self):
        """Test Windows detection searches common installation paths when nothing is found."""
        detector = InkscapeDetector()

        with (
            patch.object(detector, "_check_windows_registry", return_value=None),
            patch.object(detector, "_validate_executable", return_value=False) as mock_validate,
            patch.object(detector, "_check_path_environment", return_value=None),
        ):
            result = detector._detect_windows()
            assert result is None

            # Verify it checked some expected paths
            calls = [str(call.args[0]) for call in mock_validate.call_args_list]
            assert any("Program Files" in call for call in calls)

    @pytest.mark.skipif(sys.platform != "win32", reason="winreg is Windows-only")
    def test_windows_registry_search(self):
        """Test Windows registry search for Inkscape."""
        detector = InkscapeDetector()

        # Mock winreg operations
        mock_key = Mock()
        mock_key.__enter__ = Mock(return_value=Mock())
        mock_key.__exit__ = Mock(return_value=None)

        with (
            patch("winreg.OpenKey", return_value=mock_key),
            patch("winreg.QueryValueEx", return_value=("C:\\Program Files\\Inkscape", 1)),
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = detector._check_windows_registry()
            assert result == str(Path("C:\\Program Files\\Inkscape") / "bin" / "inkscape.exe")

    @pytest.mark.skipif(sys.platform != "win32", reason="winreg is Windows-only")
    def test_windows_registry_not_found(self):
        """Test Windows registry search when Inkscape not found."""
        detector = InkscapeDetector()

        with (
            patch("winreg.OpenKey", side_effect=FileNotFoundError),
            patch("pathlib.Path.exists", return_value=False),
            patch.object(detector, "_check_path_environment", return_value=None),
        ):
            result = detector._detect_windows()
            assert result is None

    def test_linux_detection_paths(self):
        """Test Linux detection tries PATH first, then falls back to common paths."""
        detector = InkscapeDetector()

        with (
            patch.object(detector, "_check_path_environment", return_value=None),
            patch.object(detector, "_validate_executable", return_value=False),
        ):
            result = detector._detect_linux()
            assert result is None

        # Test successful detection via PATH
        with patch.object(detector, "_check_path_environment", return_value="/usr/bin/inkscape"):
            result = detector._detect_linux()
            assert result == "/usr/bin/inkscape"

    def test_macos_detection_paths(self):
        """Test macOS detection checks common paths, then falls back to PATH."""
        detector = InkscapeDetector()

        with (
            patch.object(detector, "_validate_executable", return_value=False),
            patch.object(
                detector, "_check_path_environment", return_value="/opt/homebrew/bin/inkscape"
            ),
        ):
            result = detector._detect_macos()
            assert result == "/opt/homebrew/bin/inkscape"

    def test_path_environment_check(self):
        """Test PATH environment variable checking via 'where'/'which' subprocess."""
        detector = InkscapeDetector()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/usr/bin/inkscape\n"

        with (
            patch("subprocess.run", return_value=mock_result),
            patch.object(detector, "_validate_executable", return_value=True),
        ):
            result = detector._check_path_environment(["inkscape"])
            assert result == "/usr/bin/inkscape"

        mock_result.returncode = 1
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            result = detector._check_path_environment(["inkscape"])
            assert result is None

    def test_validate_executable(self):
        """Test executable validation checks existence, access, and name - not a subprocess call."""
        detector = InkscapeDetector()

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("os.access", return_value=True),
        ):
            assert detector._validate_executable("/usr/bin/inkscape") is True
            # Name must contain "inkscape" even if the path exists and is executable
            assert detector._validate_executable("/usr/bin/other") is False

        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("os.access", return_value=True),
        ):
            assert detector._validate_executable("/invalid/inkscape") is False

    def test_validate_executable_timeout(self):
        """Test executable validation with timeout."""
        detector = InkscapeDetector()

        with patch("subprocess.run", side_effect=TimeoutError):
            result = detector._validate_executable(Path("/usr/bin/inkscape"))
            assert result is False

    def test_validate_executable_exception(self):
        """Test executable validation with exception."""
        detector = InkscapeDetector()

        with patch("subprocess.run", side_effect=Exception("Test error")):
            result = detector._validate_executable(Path("/usr/bin/inkscape"))
            assert result is False


class TestDetectorIntegration:
    """Integration tests for detector functionality."""

    def test_full_detection_workflow(self):
        """Test complete detection workflow."""
        detector = InkscapeDetector()

        # This will use the actual detection logic
        result = detector.detect_inkscape_installation()

        # Result should be either a valid executable path (str) or None
        if result is not None:
            assert isinstance(result, str)
            assert Path(result).exists()
            assert Path(result).is_file()
        else:
            assert result is None

    def test_cross_platform_compatibility(self):
        """Test that detector works on current platform."""
        detector = InkscapeDetector()
        current_platform = platform.system()

        # Should not raise exceptions regardless of platform
        try:
            result = detector.detect_inkscape_installation()
            assert isinstance(result, (str, type(None)))
        except Exception as e:
            pytest.fail(f"Detection failed on {current_platform}: {e}")

    @patch.dict(os.environ, {"PATH": "/custom/bin:/usr/bin:/bin"})
    def test_custom_path_detection(self):
        """Test detection with custom PATH."""
        detector = InkscapeDetector()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/custom/bin/inkscape\n"

        with (
            patch("subprocess.run", return_value=mock_result),
            patch.object(detector, "_validate_executable", return_value=True),
        ):
            result = detector._check_path_environment(["inkscape"])
            assert result == "/custom/bin/inkscape"


class TestDetectorLogging:
    """Test detector logging functionality."""

    def test_detection_logging(self, caplog):
        """Test that detection operations are logged."""
        detector = InkscapeDetector()
        caplog.set_level(logging.INFO)

        with patch.object(detector, "_detect_windows", return_value=None):
            with patch("platform.system", return_value="Windows"):
                detector.detect_inkscape_installation()

                # Should log detection attempts
                assert any("Detecting Inkscape" in record.message for record in caplog.records)

    def test_validation_logging(self, caplog):
        """Test that a validation failure due to an unexpected error is logged at debug level."""
        detector = InkscapeDetector()
        caplog.set_level(logging.DEBUG)

        with patch("pathlib.Path.exists", side_effect=OSError("boom")):
            result = detector._validate_executable("/test/inkscape")

        assert result is False
        assert any("Validation failed" in record.message for record in caplog.records)
