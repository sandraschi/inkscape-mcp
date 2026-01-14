"""
Base class for GIMP MCP tool categories.

Provides common functionality and patterns for all tool implementations.
This module defines the base class that all GIMP MCP tools inherit from,
ensuring consistent behavior and interface across all tool categories.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Callable, Union
from functools import wraps
from pathlib import Path

from fastmcp import FastMCP

from ..cli_wrapper import GimpCliWrapper
from ..config import InkscapeConfig

logger = logging.getLogger(__name__)

# Type variable for tool methods
T = TypeVar('T', bound=Callable[..., Any])

def tool(
    name: Optional[str] = None,
    description: str = "",
    parameters: Optional[Dict[str, Dict[str, Any]]] = None,
    returns: Optional[Dict[str, Any]] = None,
    examples: Optional[List[Dict[str, str]]] = None
) -> Callable[[T], T]:
    """
    Decorator for GIMP MCP tool methods.
    
    This decorator enhances tool methods with metadata and documentation
    that can be used for API documentation, validation, and help systems.
    
    Args:
        name: Tool name (defaults to function name)
        description: Detailed description of the tool
        parameters: Parameter specifications
        returns: Return value specification
        examples: List of usage examples
        
    Returns:
        Decorated function with added metadata
    """
    def decorator(func: T) -> T:
        # Set or update function metadata
        if not hasattr(func, '_tool_metadata'):
            func._tool_metadata = {}
            
        func._tool_metadata.update({
            'name': name or func.__name__,
            'description': description or func.__doc__ or "",
            'parameters': parameters or {},
            'returns': returns or {},
            'examples': examples or []
        })
        
        # Preserve the original function's docstring and metadata
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            
        return wrapper  # type: ignore
    return decorator

class BaseToolCategory(ABC):
    """
    Base class for all GIMP MCP tool categories.
    
    This class provides common functionality like error handling, validation,
    and consistent patterns across all tool implementations. All tool categories
    should inherit from this class and implement the required abstract methods.
    
    Attributes:
        cli_wrapper: Instance of GimpCliWrapper for executing GIMP commands
        config: Server configuration
        logger: Logger instance for the tool category
    """
    
    def __init__(self, cli_wrapper: Optional[InkscapeCliWrapper], config: InkscapeConfig):
        """
        Initialize base tool category with dependencies and robust error handling.

        Args:
            cli_wrapper: GIMP CLI wrapper instance for executing commands (can be None)
            config: Server configuration with settings and allowed directories

        Raises:
            ValueError: If config is invalid or missing required settings
            TypeError: If parameters are of incorrect type

        Example:
            ```python
            config = InkscapeConfig()
            cli_wrapper = GimpCliWrapper(config)
            tool = MyToolCategory(cli_wrapper, config)
            ```
        """
        # Validate inputs with detailed error messages
        if config is None:
            raise ValueError("Configuration object cannot be None")

        if not isinstance(config, InkscapeConfig):
            raise TypeError(f"Expected GimpConfig, got {type(config)}")

        # CLI wrapper can be None in limited functionality mode
        self.cli_wrapper = cli_wrapper
        self.config = config

        # Initialize logger with error handling
        try:
            from ..logging_config import get_logger
            self.logger = get_logger(self.__class__.__name__)
        except ImportError:
            # Fallback to standard logging if structured logging unavailable
            import logging
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.warning("Structured logging unavailable, using standard logging")

        self.logger.info(f"Initialized {self.__class__.__name__} tool category")
    
    @abstractmethod
    def register_tools(self, app: FastMCP) -> None:
        """
        Register all tools in this category with the FastMCP application.
        
        This method is responsible for setting up all the tool endpoints
        and their corresponding handlers. Each tool method should be decorated
        with @app.tool() and the appropriate metadata.
        
        Args:
            app: FastMCP application instance to register tools with
            
        Example:
            ```python
            @app.tool()
            async def my_tool(self, param1: str, param2: int) -> Dict[str, Any]:
                # Tool implementation
                pass
            ```
        """
        pass
    
    def validate_file_path(self, file_path: str, must_exist: bool = True) -> bool:
        """
        Validate file path for security and accessibility.
        
        Args:
            file_path: Path to validate
            must_exist: Whether file must exist
            
        Returns:
            bool: True if path is valid
        """
        try:
            from pathlib import Path
            
            path = Path(file_path).resolve()
            
            # Check if file exists (if required)
            if must_exist and not path.exists():
                return False
            
            # Check if parent directory exists (for output files)
            if not must_exist and not path.parent.exists():
                return False
            
            # Security: Check if path is within allowed directories
            if self.config.allowed_directories:
                allowed = any(
                    str(path).startswith(str(Path(allowed_dir).resolve()))
                    for allowed_dir in self.config.allowed_directories
                )
                if not allowed:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Path validation failed for {file_path}: {e}")
            return False
    
    def create_error_response(self, error_msg: str, details: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create standardized error response.
        
        Args:
            error_msg: Error message
            details: Optional error details
            
        Returns:
            Dict[str, Any]: Error response
        """
        response = {
            "success": False,
            "error": error_msg
        }
        
        if details:
            response["details"] = details
        
        return response
    
    def create_success_response(self, data: Any = None, message: str = "Operation completed successfully", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create comprehensive success response with optional metadata.

        Args:
            data: Response data
            message: Success message
            metadata: Optional metadata (timing, version, etc.)

        Returns:
            Dict[str, Any]: Success response with enhanced information
        """
        import time

        response = {
            "success": True,
            "message": message,
            "timestamp": time.time()
        }

        if data is not None:
            response["data"] = data

        if metadata:
            response["metadata"] = metadata

        return response

    def create_error_response(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None, recoverable: bool = True) -> Dict[str, Any]:
        """
        Create comprehensive error response with detailed diagnostic information.

        Args:
            message: Human-readable error message
            error_code: Optional error code for categorization
            details: Optional technical details for debugging
            recoverable: Whether this error allows continued operation

        Returns:
            Dict[str, Any]: Error response with diagnostic information
        """
        import time
        import traceback

        response = {
            "success": False,
            "error": message,
            "timestamp": time.time(),
            "recoverable": recoverable
        }

        if error_code:
            response["error_code"] = error_code

        if details:
            response["details"] = details

        # Add stack trace in debug mode
        if hasattr(self.config, 'debug_mode') and getattr(self.config, 'debug_mode', False):
            response["stack_trace"] = traceback.format_exc()

        return response

    def validate_file_path(self, file_path: Union[str, Path], operation: str = "access") -> Path:
        """
        Validate and normalize file paths with comprehensive security checks.

        Args:
            file_path: File path to validate
            operation: Type of operation being performed (read, write, etc.)

        Returns:
            Normalized Path object

        Raises:
            ValueError: If path is invalid or not allowed
            PermissionError: If access is not permitted
        """
        try:
            # Convert to Path and resolve
            path = Path(file_path).resolve()

            # Check if path exists for read operations
            if operation in ["read", "access"] and not path.exists():
                raise FileNotFoundError(f"File does not exist: {path}")

            # Check file permissions
            if operation == "read" and not path.is_file():
                raise ValueError(f"Path is not a file: {path}")

            if operation == "write":
                # Check if parent directory exists and is writable
                if not path.parent.exists():
                    raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
                if not path.parent.is_dir():
                    raise ValueError(f"Parent path is not a directory: {path.parent}")

            # Security check: ensure path is within allowed directories
            allowed_dirs = getattr(self.config, 'allowed_directories', [])
            if allowed_dirs:
                path_allowed = any(path.is_relative_to(Path(allowed_dir).resolve())
                                 for allowed_dir in allowed_dirs)
                if not path_allowed:
                    raise PermissionError(f"Access denied: {path} is outside allowed directories")

            return path

        except Exception as e:
            self.logger.error(f"File path validation failed for {file_path}: {e}")
            raise

    def handle_operation_error(self, operation: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle operation errors with appropriate logging and response generation.

        Args:
            operation: Name of the operation that failed
            error: The exception that occurred
            context: Additional context information

        Returns:
            Standardized error response
        """
        error_details = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error)
        }

        if context:
            error_details["context"] = context

        # Log the error with appropriate level
        if isinstance(error, (FileNotFoundError, PermissionError)):
            self.logger.warning(f"Operation '{operation}' failed: {error}", extra=error_details)
        else:
            self.logger.error(f"Operation '{operation}' failed: {error}", extra=error_details)

        # Determine if error is recoverable
        recoverable_errors = (FileNotFoundError, PermissionError, ValueError)
        recoverable = isinstance(error, recoverable_errors)

        return self.create_error_response(
            message=f"Operation '{operation}' failed: {str(error)}",
            error_code=type(error).__name__,
            details=error_details,
            recoverable=recoverable
        )
