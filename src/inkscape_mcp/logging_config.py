"""
Structured logging configuration for GIMP MCP Server using loguru.

This module provides comprehensive logging setup with structured output,
error handling, and multiple output formats for development and production.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
import json
from datetime import datetime

class StructuredLogger:
    """
    Structured logging manager for GIMP MCP Server.
    
    Provides consistent, structured logging across all components with
    proper error handling and multiple output formats.
    """
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[Path] = None):
        """
        Initialize structured logger.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path for persistent logging
        """
        self.log_level = log_level.upper()
        self.log_file = log_file
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Configure loguru logger with structured output."""
        # Remove default handler
        logger.remove()
        
        # Console handler with structured format
        logger.add(
            sys.stderr,
            level=self.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # File handler with JSON format if log file specified
        if self.log_file:
            logger.add(
                str(self.log_file),
                level=self.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
                rotation="10 MB",
                retention="7 days",
                compression="gz",
                serialize=False  # Keep as text for readability
            )
    
    def get_logger(self, name: str) -> "logger":
        """
        Get a logger instance for a specific component.
        
        Args:
            name: Component name for logger identification
            
        Returns:
            Configured logger instance
        """
        return logger.bind(component=name)

# Global logger instance
_logger_instance: Optional[StructuredLogger] = None

def setup_logging(
    log_level: str = "INFO", 
    log_file: Optional[Path] = None,
    component: str = "gimp_mcp"
) -> "logger":
    """
    Setup global logging configuration.
    
    Args:
        log_level: Logging level
        log_file: Optional log file path
        component: Component name
        
    Returns:
        Configured logger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = StructuredLogger(log_level, log_file)
    
    return _logger_instance.get_logger(component)

def get_logger(component: str = "gimp_mcp") -> "logger":
    """
    Get logger for a component.
    
    Args:
        component: Component name
        
    Returns:
        Logger instance
    """
    if _logger_instance is None:
        setup_logging()
    
    return _logger_instance.get_logger(component)

def log_operation_start(operation: str, **kwargs) -> Dict[str, Any]:
    """
    Log the start of an operation with structured data.
    
    Args:
        operation: Operation name
        **kwargs: Additional operation parameters
        
    Returns:
        Operation context for tracking
    """
    context = {
        "operation": operation,
        "start_time": datetime.utcnow().isoformat(),
        "parameters": kwargs
    }
    
    logger.info(f"Starting operation: {operation}", extra={"context": context})
    return context

def log_operation_success(context: Dict[str, Any], result: Any = None) -> None:
    """
    Log successful operation completion.
    
    Args:
        context: Operation context from log_operation_start
        result: Optional operation result
    """
    end_time = datetime.utcnow().isoformat()
    
    logger.info(
        f"Operation completed successfully: {context['operation']}", 
        extra={
            "context": {
                **context,
                "end_time": end_time,
                "result": result,
                "status": "success"
            }
        }
    )

def log_operation_error(
    context: Dict[str, Any], 
    error: Exception, 
    error_details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log operation error with full context.
    
    Args:
        context: Operation context from log_operation_start
        error: Exception that occurred
        error_details: Additional error details
    """
    end_time = datetime.utcnow().isoformat()
    
    logger.error(
        f"Operation failed: {context['operation']} - {str(error)}", 
        extra={
            "context": {
                **context,
                "end_time": end_time,
                "error": str(error),
                "error_type": type(error).__name__,
                "error_details": error_details,
                "status": "error"
            }
        }
    )

def log_tool_call(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log MCP tool call with parameters.
    
    Args:
        tool_name: Name of the tool being called
        parameters: Tool parameters
        
    Returns:
        Call context for tracking
    """
    context = {
        "tool": tool_name,
        "start_time": datetime.utcnow().isoformat(),
        "parameters": parameters
    }
    
    logger.info(f"Tool called: {tool_name}", extra={"tool_call": context})
    return context

def log_tool_result(context: Dict[str, Any], result: Any, success: bool = True) -> None:
    """
    Log MCP tool result.
    
    Args:
        context: Tool call context
        result: Tool result
        success: Whether the call was successful
    """
    end_time = datetime.utcnow().isoformat()
    
    log_func = logger.info if success else logger.error
    status = "success" if success else "error"
    
    log_func(
        f"Tool {status}: {context['tool']}", 
        extra={
            "tool_result": {
                **context,
                "end_time": end_time,
                "result": result,
                "status": status
            }
        }
    )

# Convenience functions for common logging patterns
def log_server_start(port: Optional[int] = None, mode: str = "stdio") -> None:
    """Log server startup."""
    logger.info(
        f"GIMP MCP Server starting in {mode} mode", 
        extra={"server_start": {"mode": mode, "port": port}}
    )

def log_server_stop(reason: str = "shutdown") -> None:
    """Log server shutdown."""
    logger.info(
        f"GIMP MCP Server stopping: {reason}", 
        extra={"server_stop": {"reason": reason}}
    )

def log_tool_registration(category: str, tool_count: int, success: bool = True) -> None:
    """Log tool category registration."""
    status = "success" if success else "failed"
    logger.info(
        f"Tool registration {status}: {category} ({tool_count} tools)", 
        extra={
            "tool_registration": {
                "category": category,
                "tool_count": tool_count,
                "status": status
            }
        }
    )

def log_gimp_detection(gimp_path: Optional[str], success: bool) -> None:
    """Log GIMP detection result."""
    if success and gimp_path:
        logger.info(
            f"GIMP detected at: {gimp_path}", 
            extra={"gimp_detection": {"path": gimp_path, "found": True}}
        )
    else:
        logger.warning(
            "GIMP not found - running in limited mode", 
            extra={"gimp_detection": {"found": False}}
        )

def log_config_load(config_path: Optional[Path], success: bool) -> None:
    """Log configuration loading."""
    if success:
        logger.info(
            f"Configuration loaded from: {config_path or 'defaults'}", 
            extra={"config_load": {"path": str(config_path) if config_path else None, "success": True}}
        )
    else:
        logger.error(
            f"Failed to load configuration from: {config_path}", 
            extra={"config_load": {"path": str(config_path) if config_path else None, "success": False}}
        )

