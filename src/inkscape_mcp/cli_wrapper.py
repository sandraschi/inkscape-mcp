"""
Minimal Inkscape CLI Wrapper for essential vector graphics operations.

This module provides core Inkscape command-line functionality for MCP operations.
"""

import asyncio
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class InkscapeCliError(Exception):
    """Base exception for Inkscape CLI operations."""
    pass

class InkscapeCliWrapper:
    """
    Minimal Inkscape CLI wrapper for essential operations.
    """

    def __init__(self, config):
        """
        Initialize wrapper with config.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Basic validation
        if not hasattr(config, 'inkscape_executable') or not config.inkscape_executable:
            raise InkscapeCliError("Inkscape executable not configured")

        if not Path(config.inkscape_executable).exists():
            raise InkscapeCliError(f"Inkscape executable not found: {config.inkscape_executable}")

    async def export_file(self, input_path: str, output_path: str,
                         export_type: str = "png", dpi: int = 300) -> str:
        """
        Export SVG to other formats using Inkscape.
        """
        cmd = [
            self.config.inkscape_executable,
            f"--export-type={export_type}",
            f"--export-dpi={dpi}",
            f"--export-filename={output_path}",
            input_path
        ]

        return await self._execute_command(cmd)

    async def execute_actions(self, input_path: str, actions: str,
                             output_path: Optional[str] = None) -> str:
        """
        Execute Inkscape actions (Inkscape 1.2+ actions system).
        """
        cmd = [
            self.config.inkscape_executable,
            f"--actions={actions}"
        ]

        if output_path:
            cmd.append(f"--export-filename={output_path}")

        cmd.append(input_path)

        return await self._execute_command(cmd)

    async def trace_bitmap(self, input_path: str, output_path: str,
                          trace_type: str = "brightness", threshold: int = 128) -> str:
        """
        Convert raster image to vector using Inkscape's trace bitmap.
        """
        # Actions to select all, trace bitmap, and export
        actions = f"select-all;selection-trace;export-do"

        cmd = [
            self.config.inkscape_executable,
            f"--actions={actions}",
            f"--export-type=svg",
            f"--export-filename={output_path}",
            input_path
        ]

        return await self._execute_command(cmd)

    async def apply_boolean(self, input_path: str, output_path: str,
                           operation: str, object_ids: list) -> str:
        """
        Apply boolean operations to selected objects.
        """
        # Select objects and apply boolean operation
        select_actions = ";".join([f"select-by-id:{obj_id}" for obj_id in object_ids])

        op_map = {
            "union": "selection-union",
            "difference": "selection-diff",
            "intersection": "selection-intersect",
            "exclusion": "selection-exclusion",
            "division": "selection-division"
        }

        if operation not in op_map:
            raise InkscapeCliError(f"Unknown boolean operation: {operation}")

        actions = f"{select_actions};{op_map[operation]};export-do"

        cmd = [
            self.config.inkscape_executable,
            f"--actions={actions}",
            f"--export-type=svg",
            f"--export-filename={output_path}",
            input_path
        ]

        return await self._execute_command(cmd)

    async def get_document_info(self, input_path: str) -> str:
        """
        Get basic document information.
        """
        cmd = [
            self.config.inkscape_executable,
            "--query-all",
            input_path
        ]

        return await self._execute_command(cmd)

    async def _execute_command(self, cmd_args, timeout: int = 30) -> str:
        """
        Execute Inkscape command with timeout.
        """
        try:
            self.logger.debug(f"Executing: {' '.join(cmd_args)}")

            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                raise InkscapeCliError(f"Inkscape operation timed out after {timeout}s")

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore').strip()
                raise InkscapeCliError(f"Inkscape failed: {error_msg}")

            return stdout.decode('utf-8', errors='ignore').strip()

        except Exception as e:
            raise InkscapeCliError(f"Inkscape execution failed: {e}")
    
    async def export_file(self, input_path: str, output_path: str,
                         export_type: str = "png", dpi: int = 300,
                         export_area: str = "drawing", timeout: Optional[int] = None) -> str:
        """
        Export SVG file to raster or vector format using Inkscape CLI.

        Args:
            input_path: Input SVG file path
            output_path: Output file path
            export_type: Export format (png, pdf, eps, svg)
            dpi: Resolution for raster exports (ignored for vector formats)
            export_area: Export area (drawing, page, or custom coordinates)
            timeout: Operation timeout in seconds

        Returns:
            str: Inkscape output

        Raises:
            InkscapeExecutionError: If execution fails
            InkscapeTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout

        # Build command arguments
        cmd_args = [
            self.config.inkscape_executable,
            "--export-type", export_type,
            "--export-filename", output_path
        ]

        # Add DPI for raster formats
        if export_type.lower() in ["png", "jpg", "jpeg", "tiff", "bmp"]:
            cmd_args.extend(["--export-dpi", str(dpi)])

        # Add export area
        if export_area == "drawing":
            cmd_args.append("--export-area-drawing")
        elif export_area == "page":
            cmd_args.append("--export-area-page")
        elif export_area.startswith("custom:"):
            # Custom coordinates: "custom:x0:y0:x1:y1"
            coords = export_area.split(":", 1)[1]
            cmd_args.extend(["--export-area", coords])

        # Add input file
        cmd_args.append(input_path)

        return await self._execute_command(cmd_args, timeout)
    
    async def query_object(self, input_path: str, object_id: str,
                          query_type: str = "bbox", timeout: Optional[int] = None) -> str:
        """
        Query object properties from SVG file using Inkscape CLI.

        Args:
            input_path: Input SVG file path
            object_id: ID of object to query
            query_type: Type of query (bbox, x, y, width, height, all)
            timeout: Operation timeout in seconds

        Returns:
            str: Query result output

        Raises:
            InkscapeExecutionError: If execution fails
            InkscapeTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout

        # Build command arguments
        cmd_args = [
            self.config.inkscape_executable,
            "--query-id", object_id
        ]

        # Add specific query type
        if query_type == "bbox":
            cmd_args.append("--query-bbox")
        elif query_type == "x":
            cmd_args.append("--query-x")
        elif query_type == "y":
            cmd_args.append("--query-y")
        elif query_type == "width":
            cmd_args.append("--query-width")
        elif query_type == "height":
            cmd_args.append("--query-height")
        elif query_type == "all":
            # Query all properties
            pass

        # Add input file
        cmd_args.append(input_path)

        return await self._execute_command(cmd_args, timeout)

    async def execute_verbs(self, input_path: str, verbs: List[str],
                           output_path: Optional[str] = None, timeout: Optional[int] = None) -> str:
        """
        Execute Inkscape verbs (actions) on an SVG file.

        Args:
            input_path: Input SVG file path
            verbs: List of Inkscape verb IDs to execute
            output_path: Optional output path (will overwrite input if None)
            timeout: Operation timeout in seconds

        Returns:
            str: Inkscape output

        Raises:
            InkscapeExecutionError: If execution fails
            InkscapeTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout

        # Build command arguments
        cmd_args = [self.config.inkscape_executable]

        # Add verbs
        for verb in verbs:
            cmd_args.extend(["--verb", verb])

        # Add output if specified
        if output_path:
            cmd_args.extend(["--export-filename", output_path])

        # Add input file
        cmd_args.append(input_path)

        return await self._execute_command(cmd_args, timeout)

    async def get_document_info(self, input_path: str, timeout: Optional[int] = None) -> str:
        """
        Get document information and metadata from SVG file.

        Args:
            input_path: Input SVG file path
            timeout: Operation timeout in seconds

        Returns:
            str: Document information output

        Raises:
            InkscapeExecutionError: If execution fails
            InkscapeTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout

        # Build command arguments for document info
        cmd_args = [
            self.config.inkscape_executable,
            "--query-all",  # Get all object information
            input_path
        ]

        return await self._execute_command(cmd_args, timeout)

    
    async def load_image_info(self, file_path: str) -> Dict:
        """
        Load basic image information using GIMP.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dict: Image metadata
        """
        # Convert to absolute path for cross-platform compatibility
        abs_path = str(Path(file_path).resolve())
        
        script = f"""
(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE "{abs_path}" "{abs_path}")))
       (width (car (gimp-image-width image)))
       (height (car (gimp-image-height image)))
       (base-type (car (gimp-image-base-type image)))
       (precision (car (gimp-image-precision image))))
  (gimp-message (string-append "WIDTH:" (number->string width)
                              "|HEIGHT:" (number->string height)
                              "|TYPE:" (number->string base-type)
                              "|PRECISION:" (number->string precision)))
  (gimp-image-delete image))
"""
        
        try:
            output = await self.execute_script_fu(script)
            return self._parse_image_info(output)
        except Exception as e:
            raise GimpExecutionError(f"Failed to load image info for {file_path}: {e}")
    
    async def convert_image(self, 
                           input_path: str, 
                           output_path: str,
                           output_format: Optional[str] = None,
                           quality: Optional[int] = None) -> bool:
        """
        Convert image format using GIMP.
        
        Args:
            input_path: Source image path
            output_path: Destination image path
            output_format: Target format (auto-detected from extension if None)
            quality: JPEG quality (1-100)
            
        Returns:
            bool: True if conversion succeeded
        """
        input_abs = str(Path(input_path).resolve())
        output_abs = str(Path(output_path).resolve())
        
        # Ensure output directory exists
        Path(output_abs).parent.mkdir(parents=True, exist_ok=True)
        
        # Determine quality setting
        qual = quality or self.config.default_quality
        
        script = f"""
(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE "{input_abs}" "{input_abs}")))
       (drawable (car (gimp-image-get-active-layer image))))
  (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_abs}" "{output_abs}")
  (gimp-image-delete image)
  (gimp-message "CONVERSION:SUCCESS"))
"""
        
        try:
            output = await self.execute_script_fu(script)
            return "CONVERSION:SUCCESS" in output
        except Exception as e:
            self.logger.error(f"Image conversion failed: {e}")
            return False
    
    async def resize_image(self,
                          input_path: str,
                          output_path: str,
                          width: int,
                          height: int,
                          maintain_aspect: bool = True) -> bool:
        """
        Resize image using GIMP.
        
        Args:
            input_path: Source image path
            output_path: Destination image path
            width: Target width in pixels
            height: Target height in pixels
            maintain_aspect: Whether to maintain aspect ratio
            
        Returns:
            bool: True if resize succeeded
        """
        input_abs = str(Path(input_path).resolve())
        output_abs = str(Path(output_path).resolve())
        
        # Ensure output directory exists
        Path(output_abs).parent.mkdir(parents=True, exist_ok=True)
        
        # Build resize script
        if maintain_aspect:
            resize_func = "gimp-image-scale"
        else:
            resize_func = "gimp-image-scale"
        
        script = f"""
(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE "{input_abs}" "{input_abs}")))
       (drawable (car (gimp-image-get-active-layer image))))
  ({resize_func} image {width} {height})
  (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_abs}" "{output_abs}")
  (gimp-image-delete image)
  (gimp-message "RESIZE:SUCCESS"))
"""
        
        try:
            output = await self.execute_script_fu(script)
            return "RESIZE:SUCCESS" in output
        except Exception as e:
            self.logger.error(f"Image resize failed: {e}")
            return False
    
    async def _execute_command(self, cmd_args: List[str], timeout: int) -> str:
        """
        Execute GIMP command with proper error handling.
        
        Args:
            cmd_args: Command arguments list
            timeout: Timeout in seconds
            
        Returns:
            str: Command output
            
        Raises:
            GimpExecutionError: If execution fails
            GimpTimeoutError: If operation times out
        """
        try:
            self.logger.debug(f"Executing GIMP command: {' '.join(cmd_args[:3])}...")
            
            # Create subprocess with proper error capture
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.config.temp_directory,
                env=self._get_environment()
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                # Kill the process and raise timeout error
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                raise GimpTimeoutError(f"GIMP operation timed out after {timeout} seconds")
            
            # Check return code
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace') if stderr else "Unknown error"
                raise GimpExecutionError(f"GIMP execution failed (code {process.returncode}): {error_msg}")
            
            # Return stdout
            output = stdout.decode('utf-8', errors='replace') if stdout else ""
            self.logger.debug(f"GIMP command completed successfully")
            return output
            
        except (GimpTimeoutError, GimpExecutionError):
            raise
        except Exception as e:
            raise GimpExecutionError(f"Failed to execute GIMP command: {e}")
    
    def _get_environment(self) -> Dict[str, str]:
        """
        Get environment variables for GIMP execution.
        
        Returns:
            Dict[str, str]: Environment variables
        """
        env = os.environ.copy()
        
        # Set GIMP-specific environment variables
        env['GIMP_CONSOLE_MODE'] = '1'
        
        # Disable GIMP splash screen and user interface
        if 'DISPLAY' in env and self.system == "linux":
            # For headless Linux operation
            env['DISPLAY'] = ''
        
        return env
    
    def _parse_image_info(self, gimp_output: str) -> Dict:
        """
        Parse image information from GIMP output.
        
        Args:
            gimp_output: Raw GIMP output
            
        Returns:
            Dict: Parsed image information
        """
        try:
            # Look for our custom message format
            lines = gimp_output.split('\n')
            for line in lines:
                if 'WIDTH:' in line and 'HEIGHT:' in line:
                    # Parse format: WIDTH:1920|HEIGHT:1080|TYPE:0|PRECISION:100
                    parts = line.split('|')
                    info = {}
                    
                    for part in parts:
                        if ':' in part:
                            key, value = part.split(':', 1)
                            if key in ['WIDTH', 'HEIGHT', 'TYPE', 'PRECISION']:
                                info[key.lower()] = int(value)
                    
                    # Convert GIMP type codes to readable names
                    type_map = {0: 'RGB', 1: 'GRAYSCALE', 2: 'INDEXED'}
                    if 'type' in info:
                        info['color_mode'] = type_map.get(info['type'], 'UNKNOWN')
                    
                    return info
            
            # Fallback: return empty info if parsing fails
            return {}
            
        except Exception as e:
            self.logger.warning(f"Failed to parse GIMP output: {e}")
            return {}
    
    def validate_image_file(self, file_path: str) -> bool:
        """
        Validate if file is a supported image format.
        
        Args:
            file_path: Path to image file
            
        Returns:
            bool: True if file is valid
        """
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                return False
            
            # Check file size
            if not self.config.validate_file_size(path):
                return False
            
            # Check file extension
            extension = path.suffix.lower().lstrip('.')
            if not self.config.is_format_supported(extension):
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"File validation failed for {file_path}: {e}")
            return False


# Backward compatibility alias for legacy code
GimpCliWrapper = InkscapeCliWrapper
