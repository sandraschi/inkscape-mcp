"""
Tool utilities for GIMP MCP Server.

This module provides decorators and utilities for registering tools with FastMCP.
"""

import logging
import inspect
from typing import Dict, Any, Optional, List, Callable, TypeVar, cast, Type, Union
from functools import wraps

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=Callable[..., Any])


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    required_parameters: Optional[List[str]] = None,
) -> Callable[[Union[T, Type]], T]:
    """Decorator to mark a method as an MCP tool.

    Args:
        name: The name of the tool (defaults to function name if not provided)
        description: A description of what the tool does (defaults to function docstring)
        parameters: Dictionary of parameter definitions
        required_parameters: List of required parameter names

    Returns:
        A decorator that marks the method as an MCP tool
    """

    def decorator(func: Union[T, Type]) -> T:
        # Get function name and docstring
        func_name = name or func.__name__
        func_doc = (inspect.getdoc(func) or "").strip()

        # Extract the first line of the docstring as description if not provided
        if description is None and func_doc:
            short_desc = func_doc.split("\n")[0].strip()
        else:
            short_desc = description or "No description provided"

        # Parse function signature for parameters if not provided
        sig_params = {}
        if parameters is None:
            try:
                sig = inspect.signature(func)
                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue

                    param_info = {
                        "type": param.annotation
                        if param.annotation != inspect.Parameter.empty
                        else "string",
                        "description": "",
                    }

                    if param.default != inspect.Parameter.empty:
                        param_info["default"] = param.default

                    sig_params[param_name] = param_info
            except Exception as e:
                logger.warning(f"Could not parse signature for {func_name}: {e}")

        # Store tool metadata as an attribute
        tool_meta = {
            "name": func_name,
            "description": short_desc,
            "parameters": parameters or sig_params or {},
            "required_parameters": required_parameters or [],
        }

        setattr(func, "_mcp_tool", tool_meta)

        # If it's already a coroutine function, just add the metadata
        if inspect.iscoroutinefunction(func):
            return cast(T, func)

        # Otherwise, wrap it to make it async
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # If it's a bound method, pass self as first arg
                if args and hasattr(args[0], func.__name__):
                    result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # If the function returns a coroutine, await it
                if inspect.iscoroutine(result):
                    return await result
                return result

            except Exception as e:
                logger.error(f"Error in tool {func_name}: {e}", exc_info=True)
                raise

        return cast(T, async_wrapper)

    # Handle both @tool and @tool() syntax
    if callable(name):
        func = name
        return decorator(func)
    return decorator
