"""
Base File Operation Tools for GIMP MCP Server.

This module provides the core file handling operations and data structures
used by the GIMP MCP server, including loading, saving, format conversion,
and metadata extraction.
"""

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, Any, TypeAlias

logger = logging.getLogger(__name__)

# Type aliases for better type hints
FilePath: TypeAlias = str
ImageMetadata: TypeAlias = Dict[str, Any]
ImageData: TypeAlias = Any  # Placeholder for actual image data type


class FileOperationStatus(Enum):
    """Status of a file operation."""

    SUCCESS = auto()
    FAILURE = auto()
    PARTIAL = auto()


@dataclass
class FileOperationResult:
    """Result of a file operation.

    Attributes:
        status: Status of the operation
        message: Human-readable message
        data: Additional data related to the operation
        error: Error message if the operation failed
    """

    status: FileOperationStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "success": self.status == FileOperationStatus.SUCCESS,
            "message": self.message,
            "data": self.data or {},
            "error": self.error,
        }

    @classmethod
    def create_success_response(
        cls, data: Optional[Dict[str, Any]] = None, message: str = ""
    ) -> Dict[str, Any]:
        """Create a standardized success response."""
        return {"status": "success", "data": data or {}, "message": message}

    @classmethod
    def create_error_response(cls, message: str, details: Optional[str] = None) -> Dict[str, Any]:
        """Create a standardized error response."""
        response = {"status": "error", "error": message}
        if details:
            response["details"] = details
        return response


class FileOperationBase:
    """Base class for file operations in GIMP MCP Server.

    This class provides core file operation functionality that can be used
    both directly and through the MCP server interface.
    """

    def __init__(self, cli_wrapper, config):
        """Initialize file operation base.

        Args:
            cli_wrapper: The GIMP CLI wrapper instance
            config: The application configuration
        """
        self.cli_wrapper = cli_wrapper
        self.config = config

    def _error_response(self, message: str, details: Optional[str] = None) -> Dict[str, Any]:
        """Create a standardized error response.

        Args:
            message: Error message
            details: Optional detailed error information

        Returns:
            Dictionary with error information
        """
        response = {"status": "error", "error": message}
        if details:
            response["details"] = details
        return response
