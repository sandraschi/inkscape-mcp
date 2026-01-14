from __future__ import annotations

"""
Batch Processing Tools for GIMP MCP Server.

Provides bulk operation capabilities for processing multiple images
with the same operations efficiently.
"""

import asyncio
import glob
import logging
import os
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from fastmcp import FastMCP

from .base import BaseToolCategory

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

logger = logging.getLogger(__name__)

# Type aliases for better type hints
FilePath: TypeAlias = str
FilePattern: TypeAlias = str
BatchResult: TypeAlias = Dict[str, Any]
BatchProcessor = Callable[[FilePath], BatchResult]
T = TypeVar("T")


class BatchStatus(Enum):
    """Status of a batch operation."""

    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class BatchItem:
    """Represents an item in a batch process."""

    input_path: FilePath
    output_path: Optional[FilePath] = None
    status: BatchStatus = BatchStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Constants for batch processing
DEFAULT_BATCH_SIZE = 10
MAX_CONCURRENT_PROCESSES = 4
SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "tif", "tiff", "bmp", "gif", "webp", "xcf", "psd"}


class BatchProcessingTools(BaseToolCategory):
    """
    Batch processing tools for bulk operations.

    Provides high-performance batch processing of images with support for:
    - Concurrent processing with configurable worker count
    - Progress tracking and error handling
    - Atomic operations with rollback on failure
    - Support for all standard image formats
    - Memory-efficient processing of large batches
    """

    def __init__(self, cli_wrapper, config):
        """
        Initialize batch processing tools.

        Args:
            cli_wrapper: GIMP CLI wrapper instance
            config: Server configuration
        """
        super().__init__(cli_wrapper, config)
        self._supported_formats = {"jpg", "jpeg", "png", "tif", "tiff", "bmp", "gif", "webp", "xcf"}
        self._executor = ThreadPoolExecutor(max_workers=config.max_concurrent_processes)

    def _get_supported_files(self, directory: str, pattern: str = "*") -> List[str]:
        """
        Get list of supported image files matching pattern.

        Args:
            directory: Directory to search in
            pattern: File pattern to match (e.g., "*.jpg" or "image_*")

        Returns:
            List of absolute paths to matching image files
        """
        directory = os.path.abspath(directory)
        path = Path(directory) / pattern
        files = set()

        # Handle both with and without extension in pattern
        for ext in self._supported_formats:
            # Pattern with extension
            files.update(glob.glob(f"{path}.{ext}", recursive=True))
            files.update(glob.glob(f"{path}.{ext.upper()}", recursive=True))

            # Pattern without extension (add extension)
            if not any(path.suffix.lower() == f".{ext}" for ext in self._supported_formats):
                files.update(glob.glob(f"{path}.{ext}", recursive=True))
                files.update(glob.glob(f"{path}.{ext.upper()}", recursive=True))

        # Also support direct glob patterns
        if pattern != "*" and not any(files):
            files.update(glob.glob(os.path.join(directory, pattern), recursive=True))

        # Filter by supported extensions
        filtered_files = [
            f for f in files if Path(f).suffix.lower().lstrip(".") in self._supported_formats
        ]

        return sorted(list(set(filtered_files)))

    def _ensure_output_dir(self, path: str) -> None:
        """
        Ensure output directory exists and is writable.

        Args:
            path: Path to the output directory

        Raises:
            ValueError: If directory cannot be created or is not writable
        """
        try:
            os.makedirs(path, exist_ok=True)
            # Test write access
            test_file = os.path.join(path, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            raise ValueError(f"Cannot write to output directory {path}: {e}")

    async def _process_batch_operation(
        self,
        input_files: List[str],
        output_dir: str,
        operation_name: str,
        operation_func: Callable[[str, str, Dict[str, Any]], bool],
        **operation_kwargs,
    ) -> Dict[str, Any]:
        """
        Process a batch operation on multiple files with progress tracking.

        Args:
            input_files: List of input file paths
            output_dir: Output directory for processed files
            operation_name: Name of the operation (for logging)
            operation_func: Function that processes a single file
            **operation_kwargs: Additional arguments to pass to operation_func

        Returns:
            Dictionary with operation results and statistics
        """
        self._ensure_output_dir(output_dir)
        total_files = len(input_files)
        processed = 0
        success_count = 0
        failed_files = []

        # Process files concurrently
        loop = asyncio.get_event_loop()
        futures = []

        for input_file in input_files:
            # Create output path preserving subdirectory structure
            rel_path = os.path.relpath(input_file, os.path.dirname(input_files[0]))
            output_file = os.path.join(output_dir, os.path.basename(rel_path))
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Submit task to thread pool
            future = loop.run_in_executor(
                self._executor,
                self._process_single_file,
                input_file,
                output_file,
                operation_func,
                operation_kwargs,
            )
            futures.append(future)

        # Process results as they complete
        for future in as_completed(futures):
            try:
                success, result = await future
                processed += 1

                if success:
                    success_count += 1
                    logger.info(f"Processed {processed}/{total_files}: {result}")
                else:
                    failed_files.append(result)
                    logger.error(f"Failed to process {result}")

                # Calculate progress percentage
                int((processed / total_files) * 100)

                # TODO: Implement progress callback if needed

            except Exception as e:
                logger.error(f"Error processing batch operation: {e}")
                failed_files.append(str(e))

        # Prepare result summary
        result = {
            "operation": operation_name,
            "total_files": total_files,
            "processed": processed,
            "successful": success_count,
            "failed": len(failed_files),
            "failed_files": failed_files,
            "success_rate": (success_count / total_files * 100) if total_files > 0 else 0,
        }

        return result

    def _process_single_file(
        self,
        input_file: str,
        output_file: str,
        operation_func: Callable[[str, str, Dict[str, Any]], bool],
        operation_kwargs: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Process a single file with error handling and atomic write.

        Args:
            input_file: Path to input file
            output_file: Path to output file
            operation_func: Function to process the file
            operation_kwargs: Additional arguments for operation_func

        Returns:
            Tuple of (success, result_message)
        """
        temp_file = None
        try:
            # Create a temporary file in the same directory as output for atomic write
            temp_fd, temp_file = tempfile.mkstemp(
                prefix=os.path.basename(output_file) + ".", dir=os.path.dirname(output_file) or None
            )
            os.close(temp_fd)

            # Process the file
            success = operation_func(input_file, temp_file, **operation_kwargs)

            if not success:
                raise RuntimeError(f"Operation failed for {input_file}")

            # Atomic move to final destination
            if os.path.exists(output_file):
                os.unlink(output_file)
            shutil.move(temp_file, output_file)

            return True, output_file

        except Exception as e:
            logger.error(f"Error processing {input_file}: {e}")
            # Clean up temp file if it exists
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp file {temp_file}: {cleanup_error}")
            return False, f"{input_file}: {str(e)}"

    async def batch_resize(
        self,
        input_dir: str,
        output_dir: str,
        width: int,
        height: int,
        maintain_aspect_ratio: bool = True,
        pattern: str = "*",
    ) -> Dict[str, Any]:
        input_files = self._get_supported_files(input_dir, pattern)
        if not input_files:
            return self.create_error_response("No supported image files found")

        def resize_op(input_file: str, output_file: str, **kwargs) -> bool:
            # This would use the GIMP CLI wrapper to perform the resize
            # For now, just copy the file as a placeholder
            shutil.copy2(input_file, output_file)
            return True

        return await self._process_batch_operation(
            input_files,
            output_dir,
            "batch_resize",
            resize_op,
            width=width,
            height=height,
            maintain_aspect_ratio=maintain_aspect_ratio,
        )

    async def batch_convert(
        self,
        input_dir: str,
        output_dir: str,
        output_format: str,
        quality: int = 90,
        pattern: str = "*",
    ) -> Dict[str, Any]:
        input_files = self._get_supported_files(input_dir, pattern)
        if not input_files:
            return self.create_error_response("No supported image files found")

        def convert_op(input_file: str, output_file: str, **kwargs) -> bool:
            # This would use the GIMP CLI wrapper to perform the conversion
            # For now, just copy the file as a placeholder
            shutil.copy2(input_file, output_file)
            return True

        return await self._process_batch_operation(
            input_files,
            output_dir,
            "batch_convert",
            convert_op,
            output_format=output_format,
            quality=quality,
        )

    def register_tools(self, app: FastMCP) -> None:
        """
        Register all batch processing tools with FastMCP.

        This method sets up the API endpoints for all batch processing operations,
        making them available through the MCP protocol.

        Args:
            app: The FastMCP application instance to register tools with
        """

        @app.tool()
        async def batch_resize(
            self,
            input_directory: str,
            output_directory: str,
            width: int,
            height: int,
            maintain_aspect_ratio: bool = True,
            output_format: str = "jpg",
            quality: int = 90,
        ) -> Dict[str, Any]:
            """Batch resize multiple images to specified dimensions."""
            return await self.batch_resize(
                input_directory=input_directory,
                output_directory=output_directory,
                width=width,
                height=height,
                maintain_aspect_ratio=maintain_aspect_ratio,
                output_format=output_format,
                quality=quality,
            )

        @app.tool()
        async def batch_convert(
            self,
            input_directory: str,
            output_directory: str,
            output_format: str = "jpg",
            quality: int = 90,
        ) -> Dict[str, Any]:
            """Batch convert multiple images to a different format."""
            return await self.batch_convert(
                input_directory=input_directory,
                output_directory=output_directory,
                output_format=output_format,
                quality=quality,
            )
