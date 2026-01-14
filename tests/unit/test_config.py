"""
Unit tests for Inkscape MCP configuration module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch


from inkscape_mcp.config import InkscapeConfig, load_config


class TestInkscapeConfig:
    """Test InkscapeConfig class functionality."""

    def test_default_initialization(self):
        """Test config initializes with sensible defaults."""
        config = InkscapeConfig()

        assert config.inkscape_executable == ""
        assert config.max_concurrent_processes == 4
        assert config.process_timeout == 30.0
        assert config.enable_gpu_acceleration is False
        assert config.temp_directory == ""

    def test_custom_initialization(self):
        """Test config with custom values."""
        config = InkscapeConfig()
        config.inkscape_executable = "/usr/bin/inkscape"
        config.max_concurrent_processes = 2
        config.process_timeout = 60.0

        assert config.inkscape_executable == "/usr/bin/inkscape"
        assert config.max_concurrent_processes == 2
        assert config.process_timeout == 60.0

    @patch.dict(os.environ, {"INKSCAPE_EXECUTABLE": "/custom/path/inkscape"})
    def test_load_from_environment(self):
        """Test loading config from environment variables."""
        config = InkscapeConfig()
        config.load_from_environment()

        assert config.inkscape_executable == "/custom/path/inkscape"

    @patch.dict(
        os.environ,
        {"INKSCAPE_MAX_CONCURRENT": "8", "INKSCAPE_TIMEOUT": "120", "INKSCAPE_GPU": "true"},
    )
    def test_load_all_env_vars(self):
        """Test loading all environment variables."""
        config = InkscapeConfig()
        config.load_from_environment()

        assert config.max_concurrent_processes == 8
        assert config.process_timeout == 120.0
        assert config.enable_gpu_acceleration is True

    def test_invalid_env_values(self):
        """Test handling of invalid environment variable values."""
        with patch.dict(
            os.environ, {"INKSCAPE_MAX_CONCURRENT": "invalid", "INKSCAPE_TIMEOUT": "not_a_number"}
        ):
            config = InkscapeConfig()
            config.load_from_environment()

            # Should keep defaults on invalid values
            assert config.max_concurrent_processes == 4
            assert config.process_timeout == 30.0

    def test_save_and_load_config_file(self):
        """Test saving and loading config from file."""
        config = InkscapeConfig()
        config.inkscape_executable = "/test/path/inkscape"
        config.max_concurrent_processes = 6

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Save config
            config.save_to_file(str(temp_path))

            # Load config
            new_config = InkscapeConfig()
            new_config.load_from_file(str(temp_path))

            assert new_config.inkscape_executable == "/test/path/inkscape"
            assert new_config.max_concurrent_processes == 6

        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_from_nonexistent_file(self):
        """Test loading from nonexistent file returns defaults."""
        config = InkscapeConfig()
        config.load_from_file("/nonexistent/config.json")

        # Should keep defaults
        assert config.inkscape_executable == ""
        assert config.max_concurrent_processes == 4

    def test_invalid_json_file(self):
        """Test loading invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
            f.write("invalid json content {")
            temp_path = Path(f.name)

        try:
            config = InkscapeConfig()
            config.load_from_file(str(temp_path))

            # Should keep defaults on invalid JSON
            assert config.inkscape_executable == ""

        finally:
            temp_path.unlink(missing_ok=True)

    def test_config_validation(self):
        """Test config value validation."""
        config = InkscapeConfig()

        # Test negative values are rejected
        config.max_concurrent_processes = -1
        assert config.max_concurrent_processes >= 1

        config.process_timeout = 0
        assert config.process_timeout > 0

    def test_get_config_summary(self):
        """Test config summary generation."""
        config = InkscapeConfig()
        config.inkscape_executable = "/usr/bin/inkscape"
        config.max_concurrent_processes = 2

        summary = config.get_summary()
        assert isinstance(summary, dict)
        assert "inkscape_executable" in summary
        assert "max_concurrent_processes" in summary
        assert summary["inkscape_executable"] == "/usr/bin/inkscape"
        assert summary["max_concurrent_processes"] == 2


class TestLoadConfig:
    """Test the load_config function."""

    @patch("inkscape_mcp.config.InkscapeConfig.load_from_file")
    @patch("inkscape_mcp.config.InkscapeConfig.load_from_environment")
    def test_load_config_success(self, mock_env, mock_file):
        """Test successful config loading."""
        config = load_config()

        assert isinstance(config, InkscapeConfig)
        mock_env.assert_called_once()
        mock_file.assert_called_once()

    @patch("inkscape_mcp.config.InkscapeConfig.load_from_file")
    @patch("inkscape_mcp.config.InkscapeConfig.load_from_environment")
    def test_load_config_with_path(self, mock_env, mock_file):
        """Test loading config with custom path."""
        config_path = "/custom/config.json"
        config = load_config(config_path)

        assert isinstance(config, InkscapeConfig)
        mock_file.assert_called_once_with(config_path)
        mock_env.assert_called_once()


class TestConfigIntegration:
    """Integration tests for config functionality."""

    def test_config_file_roundtrip(self):
        """Test that config can be saved and loaded identically."""
        original = InkscapeConfig()
        original.inkscape_executable = "/test/inkscape"
        original.max_concurrent_processes = 3
        original.process_timeout = 45.0
        original.enable_gpu_acceleration = True

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Save and reload
            original.save_to_file(str(temp_path))
            loaded = InkscapeConfig()
            loaded.load_from_file(str(temp_path))

            # Verify all values match
            assert loaded.inkscape_executable == original.inkscape_executable
            assert loaded.max_concurrent_processes == original.max_concurrent_processes
            assert loaded.process_timeout == original.process_timeout
            assert loaded.enable_gpu_acceleration == original.enable_gpu_acceleration

        finally:
            temp_path.unlink(missing_ok=True)

    @patch.dict(
        os.environ, {"INKSCAPE_EXECUTABLE": "/env/inkscape", "INKSCAPE_MAX_CONCURRENT": "5"}
    )
    def test_env_overrides_defaults(self):
        """Test that environment variables override defaults."""
        config = InkscapeConfig()
        config.load_from_environment()

        assert config.inkscape_executable == "/env/inkscape"
        assert config.max_concurrent_processes == 5
        # Other values should remain defaults
        assert config.process_timeout == 30.0
        assert config.enable_gpu_acceleration is False
