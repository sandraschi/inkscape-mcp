"""
Configuration management for Inkscape MCP Server.

This module handles loading, validation, and management of server configuration
including Inkscape settings, performance tuning, and user preferences.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

class InkscapeConfig(BaseModel):
    """
    Configuration model for Inkscape MCP Server.
    """

    # Inkscape Configuration
    inkscape_executable: Optional[str] = Field(
        default=None,
        description="Path to Inkscape executable (auto-detected if None)"
    )
    
    # Performance Settings
    max_concurrent_processes: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of concurrent Inkscape processes"
    )

    process_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Timeout for Inkscape operations in seconds"
    )
    
    # File Handling
    temp_directory: str = Field(
        default_factory=lambda: tempfile.gettempdir(),
        description="Directory for temporary files"
    )
    
    max_file_size_mb: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum file size in MB"
    )
    
    preserve_metadata: bool = Field(
        default=True,
        description="Preserve EXIF and other metadata when possible"
    )
    
    auto_cleanup: bool = Field(
        default=True,
        description="Automatically clean up temporary files"
    )
    
    cleanup_interval: int = Field(
        default=3600,
        ge=60,
        description="Cleanup interval in seconds"
    )
    
    # Image Processing Defaults
    default_quality: int = Field(
        default=95,
        ge=1,
        le=100,
        description="Default JPEG quality (1-100)"
    )
    
    default_interpolation: str = Field(
        default="lanczos",
        description="Default interpolation method for resizing"
    )
    
    supported_formats: List[str] = Field(
        default_factory=lambda: [
            "jpeg", "jpg", "png", "webp", "tiff", "tif", 
            "bmp", "gif", "xcf", "psd", "svg", "pdf"
        ],
        description="List of supported image formats"
    )
    
    # Batch Processing
    enable_batch_operations: bool = Field(
        default=True,
        description="Enable batch processing capabilities"
    )
    
    # Plugin System
    enable_plugins: bool = Field(
        default=True,
        description="Enable plugin system"
    )
    
    plugin_dirs: List[str] = Field(
        default_factory=list,
        description="List of directories to search for plugins"
    )
    
    disabled_plugins: List[str] = Field(
        default_factory=list,
        description="List of plugin names to disable"
    )
    
    plugin_config: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Plugin-specific configuration"
    )
    
    batch_size_limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of files in a single batch"
    )
    
    # Logging and Debug
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    enable_performance_logging: bool = Field(
        default=False,
        description="Enable detailed performance logging"
    )
    
    # Security Settings
    enable_file_validation: bool = Field(
        default=True,
        description="Enable file type validation"
    )
    
    allowed_directories: List[str] = Field(
        default_factory=list,
        description="List of allowed directories for file operations"
    )
    
    @field_validator('temp_directory')
    @classmethod
    def validate_temp_directory(cls, v: str) -> str:
        """Validate and create temp directory if needed."""
        path = Path(v)
        try:
            path.mkdir(parents=True, exist_ok=True)
            if not os.access(path, os.W_OK):
                raise ValueError(f"Temp directory not writable: {v}")
        except Exception as e:
            raise ValueError(f"Invalid temp directory: {v} - {e}")
        return str(path)
    
    @field_validator('default_interpolation')
    @classmethod
    def validate_interpolation(cls, v: str) -> str:
        """Validate interpolation method."""
        valid_methods = ["none", "linear", "cubic", "lanczos"]
        if v.lower() not in valid_methods:
            raise ValueError(f"Invalid interpolation method: {v}. Must be one of {valid_methods}")
        return v.lower()
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    @classmethod
    def load_from_file(cls, config_path: Union[str, Path]) -> 'InkscapeConfig':
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            InkscapeConfig: Loaded configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                config_data = {}
                
            return cls(**config_data)
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load config: {e}")
    
    @classmethod
    def load_default(cls) -> 'InkscapeConfig':
        """
        Load default configuration with auto-detection.
        
        Returns:
            InkscapeConfig: Default configuration
        """
        # Look for config file in common locations
        config_paths = [
            Path.cwd() / "config.yaml",
            Path.cwd() / "gimp-mcp.yaml",
            Path.home() / ".gimp-mcp" / "config.yaml",
            Path.home() / ".config" / "gimp-mcp" / "config.yaml",
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                logger.info(f"Loading configuration from: {config_path}")
                try:
                    return cls.load_from_file(config_path)
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")
        
        logger.info("Using default configuration")
        return cls()
    
    def save_to_file(self, config_path: Union[str, Path]) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config_path: Path to save configuration
        """
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and remove None values
        config_dict = self.dict(exclude_none=True)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    config_dict,
                    f,
                    default_flow_style=False,
                    sort_keys=True,
                    indent=2
                )
            logger.info(f"Configuration saved to: {path}")
            
        except Exception as e:
            logger.error(f"Failed to save config to {path}: {e}")
            raise
    
    def create_temp_subdirectory(self, name: str) -> Path:
        """
        Create a subdirectory in the temp directory.
        
        Args:
            name: Subdirectory name
            
        Returns:
            Path: Path to created subdirectory
        """
        subdir = Path(self.temp_directory) / name
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir
    
    def is_format_supported(self, format_name: str) -> bool:
        """
        Check if an image format is supported.
        
        Args:
            format_name: Format name to check
            
        Returns:
            bool: True if format is supported
        """
        return format_name.lower() in [fmt.lower() for fmt in self.supported_formats]
    
    def get_temp_file_path(self, suffix: str = "") -> Path:
        """
        Generate a unique temporary file path.
        
        Args:
            suffix: File suffix/extension
            
        Returns:
            Path: Unique temporary file path
        """
        import uuid
        filename = f"gimp_mcp_{uuid.uuid4().hex[:8]}{suffix}"
        return Path(self.temp_directory) / filename
    
    def validate_file_size(self, file_path: Union[str, Path]) -> bool:
        """
        Validate file size against configured limits.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            bool: True if file size is acceptable
        """
        try:
            file_size = Path(file_path).stat().st_size
            max_size = self.max_file_size_mb * 1024 * 1024
            return file_size <= max_size
        except Exception:
            return False


def load_config(config_path: Optional[Union[str, Path]] = None) -> InkscapeConfig:
    """
    Load configuration from file or create a default config if it doesn't exist.
    
    Args:
        config_path: Optional path to configuration file. If None, uses default location.
        
    Returns:
        InkscapeConfig: Loaded configuration
        
    Raises:
        ValueError: If the config file is invalid
    """
    if config_path is None:
        # Use default config location in user's config directory
        config_dir = Path.home() / ".config" / "gimp-mcp"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.yaml"
    else:
        config_path = Path(config_path)
    
    # Create default config if it doesn't exist
    if not config_path.exists():
        logger.info(f"Config file not found at {config_path}, creating default config")
        create_default_config_file(config_path)
    
    try:
        # Load and validate the config
        return GimpConfig.load_from_file(config_path)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        logger.info("Falling back to default configuration")
        return GimpConfig.load_default()


def create_default_config_file(config_path: Union[str, Path]) -> None:
    """
    Create a default configuration file with comments.
    
    Args:
        config_path: Path where to create the config file
    """
    config_content = """
# GIMP MCP Server Configuration
# This file configures the GIMP MCP server behavior and settings

# GIMP Configuration
# gimp_executable: "/path/to/gimp"  # Auto-detected if not specified

# Performance Settings
max_concurrent_processes: 3  # Number of concurrent GIMP processes
process_timeout: 30          # Timeout for operations in seconds

# File Handling
temp_directory: "/tmp"       # Directory for temporary files (auto-detected)
max_file_size_mb: 100       # Maximum file size in MB
preserve_metadata: true     # Preserve EXIF data when possible
auto_cleanup: true          # Automatically clean up temp files
cleanup_interval: 3600      # Cleanup interval in seconds

# Image Processing Defaults
default_quality: 95         # Default JPEG quality (1-100)
default_interpolation: "lanczos"  # Interpolation method for resizing

# Supported formats (add/remove as needed)
supported_formats:
  - "jpeg"
  - "jpg" 
  - "png"
  - "webp"
  - "tiff"
  - "tif"
  - "bmp"
  - "gif"
  - "xcf"  # GIMP native format
  - "psd"  # Photoshop (limited support)

# Batch Processing
enable_batch_operations: true
batch_size_limit: 50        # Max files per batch

# Plugin System
enable_plugins: true       # Enable/disable plugin system
# plugin_dirs:             # Additional plugin directories
#   - "/path/to/plugins"
# disabled_plugins:        # List of plugin names to disable
#   - "example_plugin"
# plugin_config:           # Plugin-specific configuration
#   plugin_name:
#     setting1: value1
#     setting2: value2

# Logging and Debug
log_level: "INFO"           # DEBUG, INFO, WARNING, ERROR
enable_performance_logging: false

# Security Settings
enable_file_validation: true
# allowed_directories:      # Restrict operations to these directories
#   - "/home/user/images"
#   - "/var/www/uploads"
""".strip()
    
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    logger.info(f"Created default configuration file: {path}")
