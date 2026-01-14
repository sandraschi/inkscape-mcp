"""
Unit tests for Inkscape detector module.
"""

import os
import platform
from pathlib import Path
from unittest.mock import patch, Mock

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
        """Test Windows detection searches correct paths."""
        detector = InkscapeDetector()

        # Mock os.path.exists and check the paths it would check
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            result = detector._detect_windows()
            assert result is None

            # Verify it checked some expected paths
            calls = [str(call[0][0]) for call in mock_exists.call_args_list]
            assert any("Program Files" in call for call in calls)

    def test_windows_registry_search(self):
        """Test Windows registry search for Inkscape."""
        detector = InkscapeDetector()

        # Mock winreg operations
        mock_key = Mock()
        mock_key.__enter__ = Mock(return_value=Mock())
        mock_key.__exit__ = Mock(return_value=None)

        with (
            patch("winreg.OpenKey", return_value=mock_key),
            patch(
                "winreg.QueryValueEx", return_value=("C:\\Program Files\\Inkscape\\inkscape.exe", 1)
            ),
            patch("os.path.exists", return_value=True),
        ):
            result = detector._detect_windows()
            assert result == Path("C:/Program Files/Inkscape/inkscape.exe")

    def test_windows_registry_not_found(self):
        """Test Windows registry search when Inkscape not found."""
        detector = InkscapeDetector()

        with (
            patch("winreg.OpenKey", side_effect=FileNotFoundError),
            patch("os.path.exists", return_value=False),
        ):
            result = detector._detect_windows()
            assert result is None

    def test_linux_detection_paths(self):
        """Test Linux detection searches correct paths."""
        detector = InkscapeDetector()


        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            result = detector._detect_linux()
            assert result is None

            # Test successful detection
            mock_which.return_value = "/usr/bin/inkscape"
            result = detector._detect_linux()
            assert result == Path("/usr/bin/inkscape")

    def test_macos_detection_paths(self):
        """Test macOS detection searches correct paths."""
        detector = InkscapeDetector()

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None

            # Mock subprocess for brew detection
            with patch("subprocess.run") as mock_run:
                mock_proc = Mock()
                mock_proc.returncode = 0
                mock_proc.stdout = "/Applications/Inkscape.app/Contents/MacOS/inkscape"
                mock_run.return_value = mock_proc

                result = detector._detect_macos()
                assert result == Path("/Applications/Inkscape.app/Contents/MacOS/inkscape")

    def test_path_environment_check(self):
        """Test PATH environment variable checking."""
        detector = InkscapeDetector()

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/inkscape"
            result = detector._check_path_environment()
            assert result == Path("/usr/bin/inkscape")

            mock_which.return_value = None
            result = detector._check_path_environment()
            assert result is None

    def test_validate_executable(self):
        """Test executable validation."""
        detector = InkscapeDetector()

        # Test with valid executable
        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 0
            mock_proc.stdout = "Inkscape 1.3"
            mock_run.return_value = mock_proc

            result = detector._validate_executable(Path("/usr/bin/inkscape"))
            assert result is True

        # Test with invalid executable
        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 1
            mock_run.return_value = mock_proc

            result = detector._validate_executable(Path("/invalid/path"))
            assert result is False

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

        # Result should be either a valid path or None
        if result is not None:
            assert isinstance(result, Path)
            assert result.exists()
            assert result.is_file()
        else:
            assert result is None

    def test_cross_platform_compatibility(self):
        """Test that detector works on current platform."""
        detector = InkscapeDetector()
        current_platform = platform.system()

        # Should not raise exceptions regardless of platform
        try:
            result = detector.detect_inkscape_installation()
            assert isinstance(result, (Path, type(None)))
        except Exception as e:
            pytest.fail(f"Detection failed on {current_platform}: {e}")

    @patch.dict(os.environ, {"PATH": "/custom/bin:/usr/bin:/bin"})
    def test_custom_path_detection(self):
        """Test detection with custom PATH."""
        detector = InkscapeDetector()

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/custom/bin/inkscape"
            result = detector._check_path_environment()
            assert result == Path("/custom/bin/inkscape")


class TestDetectorLogging:
    """Test detector logging functionality."""

    def test_detection_logging(self, caplog):
        """Test that detection operations are logged."""
        detector = InkscapeDetector()

        with patch.object(detector, "_detect_windows", return_value=None):
            with patch("platform.system", return_value="Windows"):
                detector.detect_inkscape_installation()

                # Should log detection attempts
                assert any("Detecting Inkscape" in record.message for record in caplog.records)

    def test_validation_logging(self, caplog):
        """Test validation logging."""
        detector = InkscapeDetector()

        with patch("subprocess.run") as mock_run:
            mock_proc = Mock()
            mock_proc.returncode = 0
            mock_proc.stdout = "Inkscape 1.3"
            mock_run.return_value = mock_proc

            detector._validate_executable(Path("/test/inkscape"))

            # Should log validation
            assert any("Validating executable" in record.message for record in caplog.records)
