"""
Unit tests for Inkscape MCP configuration module.
"""

import tempfile
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from inkscape_mcp.config import InkscapeConfig
from inkscape_mcp.config import create_default_config_file
from inkscape_mcp.config import load_config


class TestInkscapeConfig:
    """Test InkscapeConfig class functionality."""

    def test_default_initialization(self):
        """Test config initializes with sensible defaults."""
        config = InkscapeConfig()

        assert config.inkscape_executable is None
        assert config.max_concurrent_processes == 3
        assert config.process_timeout == 30
        assert config.temp_directory == tempfile.gettempdir()
        assert config.max_file_size_mb == 100
        assert config.default_quality == 95
        assert config.default_interpolation == "lanczos"
        assert config.log_level == "INFO"
        assert "svg" in config.supported_formats

    def test_custom_initialization(self):
        """Test config with custom values passed to the constructor."""
        config = InkscapeConfig(
            inkscape_executable="/usr/bin/inkscape",
            max_concurrent_processes=2,
            process_timeout=60,
        )

        assert config.inkscape_executable == "/usr/bin/inkscape"
        assert config.max_concurrent_processes == 2
        assert config.process_timeout == 60

    def test_max_concurrent_processes_out_of_range_rejected(self):
        """Test that out-of-range values are rejected by field validation."""
        with pytest.raises(ValidationError):
            InkscapeConfig(max_concurrent_processes=0)

        with pytest.raises(ValidationError):
            InkscapeConfig(max_concurrent_processes=11)

    def test_process_timeout_out_of_range_rejected(self):
        """Test that an out-of-range process_timeout is rejected."""
        with pytest.raises(ValidationError):
            InkscapeConfig(process_timeout=0)

    def test_invalid_interpolation_rejected(self):
        """Test that an unsupported interpolation method is rejected."""
        with pytest.raises(ValidationError):
            InkscapeConfig(default_interpolation="bogus")

    def test_interpolation_normalized_to_lowercase(self):
        """Test that a valid interpolation method is normalized to lowercase."""
        config = InkscapeConfig(default_interpolation="LANCZOS")
        assert config.default_interpolation == "lanczos"

    def test_invalid_log_level_rejected(self):
        """Test that an unsupported log level is rejected."""
        with pytest.raises(ValidationError):
            InkscapeConfig(log_level="TRACE")

    def test_log_level_normalized_to_uppercase(self):
        """Test that a valid log level is normalized to uppercase."""
        config = InkscapeConfig(log_level="debug")
        assert config.log_level == "DEBUG"

    def test_temp_directory_created(self, tmp_path):
        """Test that a nonexistent temp_directory is created on validation."""
        target = tmp_path / "does" / "not" / "exist" / "yet"
        config = InkscapeConfig(temp_directory=str(target))

        assert target.exists()
        assert config.temp_directory == str(target)

    def test_save_and_load_config_file(self, tmp_path):
        """Test saving and loading config from a YAML file."""
        config = InkscapeConfig(
            inkscape_executable="/test/path/inkscape",
            max_concurrent_processes=6,
        )

        config_path = tmp_path / "config.yaml"
        config.save_to_file(config_path)

        loaded = InkscapeConfig.load_from_file(config_path)

        assert loaded.inkscape_executable == "/test/path/inkscape"
        assert loaded.max_concurrent_processes == 6

    def test_load_from_nonexistent_file(self):
        """Test loading from a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            InkscapeConfig.load_from_file("/nonexistent/config.yaml")

    def test_invalid_yaml_file(self, tmp_path):
        """Test loading an invalid YAML file raises ValueError."""
        config_path = tmp_path / "bad.yaml"
        config_path.write_text("key: [unclosed", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid YAML"):
            InkscapeConfig.load_from_file(config_path)

    def test_load_from_empty_file_uses_defaults(self, tmp_path):
        """Test that an empty config file loads as all-default config."""
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("", encoding="utf-8")

        config = InkscapeConfig.load_from_file(config_path)
        assert config.inkscape_executable is None
        assert config.max_concurrent_processes == 3

    def test_is_format_supported(self):
        """Test format support checking is case-insensitive."""
        config = InkscapeConfig()
        assert config.is_format_supported("SVG") is True
        assert config.is_format_supported("png") is True
        assert config.is_format_supported("docx") is False

    def test_get_temp_file_path(self, tmp_path):
        """Test unique temp file path generation."""
        config = InkscapeConfig(temp_directory=str(tmp_path))
        path = config.get_temp_file_path(suffix=".svg")

        assert path.parent == tmp_path
        assert path.suffix == ".svg"
        assert path.name.startswith("inkscape_mcp_")

    def test_validate_file_size(self, tmp_path):
        """Test file size validation against configured limits."""
        config = InkscapeConfig(max_file_size_mb=1)

        small_file = tmp_path / "small.svg"
        small_file.write_bytes(b"x" * 100)
        assert config.validate_file_size(small_file) is True

        assert config.validate_file_size(tmp_path / "missing.svg") is False

    def test_create_temp_subdirectory(self, tmp_path):
        """Test creating a subdirectory under temp_directory."""
        config = InkscapeConfig(temp_directory=str(tmp_path))
        subdir = config.create_temp_subdirectory("batch1")

        assert subdir == tmp_path / "batch1"
        assert subdir.exists()


class TestLoadConfig:
    """Test the load_config function."""

    def test_load_config_creates_default_when_missing(self, tmp_path):
        """Test that load_config creates a default config file if it doesn't exist."""
        config_path = tmp_path / "config.yaml"
        assert not config_path.exists()

        config = load_config(config_path)

        assert isinstance(config, InkscapeConfig)
        assert config_path.exists()
        assert config.max_concurrent_processes == 3

    def test_load_config_with_existing_file(self, tmp_path):
        """Test loading config from an already-existing file."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"max_concurrent_processes": 7}), encoding="utf-8")

        config = load_config(config_path)

        assert isinstance(config, InkscapeConfig)
        assert config.max_concurrent_processes == 7

    def test_load_config_falls_back_to_default_on_invalid_file(self, tmp_path):
        """Test that an invalid config file falls back to InkscapeConfig.load_default()."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("key: [unclosed", encoding="utf-8")

        with patch(
            "inkscape_mcp.config.InkscapeConfig.load_default",
            return_value=InkscapeConfig(),
        ) as mock_default:
            config = load_config(config_path)

        mock_default.assert_called_once()
        assert isinstance(config, InkscapeConfig)


class TestCreateDefaultConfigFile:
    """Test the create_default_config_file function."""

    def test_creates_file_with_expected_defaults(self, tmp_path):
        """Test that the generated default config file parses into expected defaults."""
        config_path = tmp_path / "nested" / "config.yaml"
        create_default_config_file(config_path)

        assert config_path.exists()

        config = InkscapeConfig.load_from_file(config_path)
        assert config.max_concurrent_processes == 3
        assert config.process_timeout == 30
        assert config.log_level == "INFO"


class TestConfigIntegration:
    """Integration tests for config functionality."""

    def test_config_file_roundtrip(self, tmp_path):
        """Test that config can be saved and loaded identically."""
        original = InkscapeConfig(
            inkscape_executable="/test/inkscape",
            max_concurrent_processes=3,
            process_timeout=45,
        )

        config_path = tmp_path / "roundtrip.yaml"
        original.save_to_file(config_path)
        loaded = InkscapeConfig.load_from_file(config_path)

        assert loaded.inkscape_executable == original.inkscape_executable
        assert loaded.max_concurrent_processes == original.max_concurrent_processes
        assert loaded.process_timeout == original.process_timeout

    def test_detect_inkscape_executable_honors_env_override(self, tmp_path, monkeypatch):
        """Test that INKSCAPE_PATH env var is honored by auto-detection."""
        fake_exe = tmp_path / "inkscape.exe"
        fake_exe.write_text("")
        monkeypatch.setenv("INKSCAPE_PATH", str(fake_exe))

        detected = InkscapeConfig._detect_inkscape_executable()
        assert detected == str(fake_exe)
