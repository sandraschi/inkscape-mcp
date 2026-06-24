"""
Inkscape Installation Detection and Validation.

This module handles cross-platform detection of Inkscape installations,
version validation, and executable path resolution.
"""

import logging
import os
import platform
import re
import subprocess
from pathlib import Path

if platform.system() == "Windows":
    import winreg

logger = logging.getLogger(__name__)


class InkscapeDetector:
    """
    Cross-platform Inkscape installation detector and validator.
    """

    def __init__(self):
        self.system = platform.system().lower()
        self.logger = logging.getLogger(__name__)

    def detect_inkscape_installation(self) -> str | None:
        """
        Detect Inkscape installation across different platforms.

        Returns:
            Optional[str]: Path to Inkscape executable if found, None otherwise
        """
        self.logger.info(f"Detecting Inkscape installation on {self.system}")

        # Honor explicit override first
        env_path = os.environ.get("INKSCAPE_PATH", "").strip()
        if env_path and self._validate_executable(env_path):
            self.logger.info(f"Using INKSCAPE_PATH from environment: {env_path}")
            return env_path

        if self.system == "windows":
            return self._detect_windows()
        elif self.system == "darwin":  # macOS
            return self._detect_macos()
        elif self.system == "linux":
            return self._detect_linux()
        else:
            self.logger.warning(f"Unsupported platform: {self.system}")
            return None

    def _detect_windows(self) -> str | None:
        """
        Detect Inkscape on Windows using registry and common paths.

        Returns:
            Optional[str]: Path to Inkscape executable
        """
        # Try registry first
        registry_path = self._check_windows_registry()
        if registry_path and self._validate_executable(registry_path):
            return registry_path

        # Try common installation paths
        username = os.environ.get("USERNAME", "")
        common_paths = [
            r"C:\Program Files\Inkscape\bin\inkscape.exe",
            r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe",
            rf"C:\Users\{username}\AppData\Local\Programs\Inkscape\bin\inkscape.exe",
            rf"C:\Users\{username}\AppData\Local\Microsoft\WindowsApps\inkscape.exe",
        ]

        # Check for Microsoft Store version
        store_path = rf"C:\Users\{username}\AppData\Local\Packages\25415Inkscape.Inkscape_9waqn51p1ttv2\LocalState\bin\inkscape.exe"
        common_paths.append(store_path)

        for path in common_paths:
            if self._validate_executable(path):
                return path

        # Try PATH environment
        path_executable = self._check_path_environment(["inkscape.exe", "inkscape"])
        if path_executable:
            return path_executable

        return None

    def _check_windows_registry(self) -> str | None:
        """
        Check Windows registry for Inkscape installation.

        Returns:
            Optional[str]: Path from registry if found
        """
        try:
            # Check HKEY_LOCAL_MACHINE
            registry_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inkscape",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inkscape",
            ]

            for key_path in registry_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        install_location, _ = winreg.QueryValueEx(key, "InstallLocation")

                        # Look for executable in bin directory
                        bin_dir = Path(install_location) / "bin"
                        for exe_name in ["inkscape.exe"]:
                            exe_path = bin_dir / exe_name
                            if exe_path.exists():
                                return str(exe_path)

                except (FileNotFoundError, OSError):
                    continue

        except ImportError:
            # winreg not available (non-Windows)
            pass
        except Exception as e:
            self.logger.debug(f"Registry check failed: {e}")

        return None

    def _detect_macos(self) -> str | None:
        """
        Detect Inkscape on macOS.

        Returns:
            Optional[str]: Path to Inkscape executable
        """
        common_paths = [
            "/Applications/Inkscape.app/Contents/MacOS/inkscape",
            "/usr/local/bin/inkscape",
            "/opt/homebrew/bin/inkscape",
        ]

        for path in common_paths:
            if self._validate_executable(path):
                return path

        # Try PATH environment
        path_executable = self._check_path_environment(["inkscape"])
        if path_executable:
            return path_executable

        return None

    def _detect_linux(self) -> str | None:
        """
        Detect Inkscape on Linux.

        Returns:
            Optional[str]: Path to Inkscape executable
        """
        # Try PATH first (most common)
        path_executable = self._check_path_environment(["inkscape"])
        if path_executable:
            return path_executable

        # Try common installation paths
        common_paths = [
            "/usr/bin/inkscape",
            "/usr/local/bin/inkscape",
            "/snap/bin/inkscape",
            "/flatpak/app/org.inkscape.Inkscape/current/active/export/bin/inkscape",
            "~/.local/bin/inkscape",
        ]

        for path in common_paths:
            expanded_path = Path(path).expanduser()
            if self._validate_executable(expanded_path):
                return expanded_path

        return None

    def _check_path_environment(self, executable_names: list[str]) -> str | None:
        """
        Check if Inkscape is available in PATH environment.

        Args:
            executable_names: List of possible executable names

        Returns:
            Optional[str]: Full path to executable if found in PATH
        """
        for exe_name in executable_names:
            try:
                # Use 'where' on Windows, 'which' on Unix-like systems
                cmd = "where" if self.system == "windows" else "which"
                result = subprocess.run([cmd, exe_name], capture_output=True, text=True, timeout=10)

                if result.returncode == 0 and result.stdout.strip():
                    path = result.stdout.strip().split("\n")[0]  # Take first result
                    if self._validate_executable(path):
                        return path

            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                continue

        return None

    def _validate_executable(self, path: str) -> bool:
        """
        Validate that the given path is a valid Inkscape executable.

        Args:
            path: Path to validate

        Returns:
            bool: True if valid executable
        """
        if not path:
            return False

        try:
            path_obj = Path(path)

            # Check if file exists and is executable
            if not path_obj.exists() or not os.access(path, os.X_OK):
                return False

            # Quick validation by checking if it's likely an Inkscape executable
            path_str = str(path_obj).lower()
            if "inkscape" not in path_str:
                return False

            return True

        except Exception as e:
            self.logger.debug(f"Validation failed for {path}: {e}")
            return False

    def validate_inkscape_version(self, executable_path: str) -> str:
        """
        Validate Inkscape version and check compatibility.

        Args:
            executable_path: Path to Inkscape executable

        Returns:
            str: Version string

        Raises:
            RuntimeError: If version check fails or version is incompatible
        """
        try:
            # Run Inkscape with version flag
            result = subprocess.run(
                [executable_path, "--version"], capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"Inkscape version check failed: {result.stderr}")

            # Parse version from output (e.g., "Inkscape 1.3.2 (1.3.2, 2023-11-25)")
            version_match = re.search(r"Inkscape\s+(\d+\.\d+(?:\.\d+)?)", result.stdout)
            if not version_match:
                raise RuntimeError(f"Could not parse Inkscape version from: {result.stdout}")

            version = version_match.group(1)
            major, minor, *_ = version.split(".")
            major, minor = int(major), int(minor)

            # Check minimum version requirements
            if major < 1:
                raise RuntimeError(
                    f"Inkscape version {version} is too old. "
                    "Please install Inkscape 1.0+"
                )

            self.logger.info(f"Validated Inkscape version: {version}")
            return version

        except subprocess.TimeoutExpired as te:
            raise RuntimeError("Inkscape version check timed out") from te
        except Exception as e:
            raise RuntimeError(f"Inkscape version validation failed: {e}") from e

    def get_default_paths(self) -> list[str]:
        """
        Get platform-specific default installation paths.

        Returns:
            List[str]: List of default paths to check
        """
        if self.system == "windows":
            return [
                r"C:\Program Files\Inkscape\bin\inkscape.exe",
                r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe",
            ]
        elif self.system == "darwin":
            return [
                "/Applications/Inkscape.app/Contents/MacOS/inkscape",
                "/usr/local/bin/inkscape",
                "/opt/homebrew/bin/inkscape",
            ]
        elif self.system == "linux":
            return [
                "/usr/bin/inkscape",
                "/usr/local/bin/inkscape",
                "/snap/bin/inkscape",
            ]
        else:
            return []
