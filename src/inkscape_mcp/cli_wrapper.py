"""
Inkscape CLI Wrapper for executing Inkscape operations via command line.

This module provides a robust interface for executing Inkscape batch operations
through command line interface with proper error handling and cross-platform support.
"""

import asyncio
import logging
import os
import platform
import shlex
import subprocess
import tempfile
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .config import InkscapeConfig

logger = logging.getLogger(__name__)

class InkscapeCliError(Exception):
    """Base exception for Inkscape CLI operations."""
    pass

class InkscapeTimeoutError(InkscapeCliError):
    """Inkscape operation timed out."""
    pass

class InkscapeExecutionError(InkscapeCliError):
    """Inkscape execution failed."""
    pass

class InkscapeCliWrapper:
    """
    Cross-platform Inkscape command-line interface wrapper.

    Provides a high-level interface for executing Inkscape batch operations
    with proper error handling, timeout management, and result parsing.
    """

    def __init__(self, config: InkscapeConfig):
        """
        Initialize Inkscape CLI wrapper.

        Args:
            config: Inkscape configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.system = platform.system().lower()
        
        # Validate GIMP executable
        if not self.config.gimp_executable:
            raise GimpCliError("GIMP executable not configured")
        
        if not Path(self.config.gimp_executable).exists():
            raise GimpCliError(f"GIMP executable not found: {self.config.gimp_executable}")
    
    async def execute_script_fu(self, script_content: str, timeout: Optional[int] = None) -> str:
        """
        Execute a Script-Fu script in GIMP batch mode.
        
        Args:
            script_content: Script-Fu code to execute
            timeout: Operation timeout in seconds
            
        Returns:
            str: GIMP output
            
        Raises:
            GimpExecutionError: If execution fails
            GimpTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout
        
        # Build command arguments
        cmd_args = [
            self.config.gimp_executable,
            "-i",  # No interface
            "-d",  # No data (faster startup)
            "-f",  # No fonts (faster startup)
            "-b", script_content,
            "-b", "(gimp-quit 0)"
        ]
        
        return await self._execute_command(cmd_args, timeout)
    
    async def execute_python_fu(self, python_content: str, timeout: Optional[int] = None) -> str:
        """
        Execute Python-Fu code in GIMP (GIMP 3.0+).
        
        Args:
            python_content: Python code to execute
            timeout: Operation timeout in seconds
            
        Returns:
            str: GIMP output
            
        Raises:
            GimpExecutionError: If execution fails
            GimpTimeoutError: If operation times out
        """
        timeout = timeout or self.config.process_timeout
        
        # Create temporary Python script file
        temp_script = self.config.get_temp_file_path(".py")
        
        try:
            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write(python_content)
            
            # Build command arguments for Python-Fu
            cmd_args = [
                self.config.gimp_executable,
                "-i",  # No interface
                "-d",  # No data
                "-f",  # No fonts
                "--batch-interpreter", "python-fu-eval",
                "-b", f"exec(open('{temp_script}').read())",
                "-b", "pdb.gimp_quit(1)"
            ]
            
            return await self._execute_command(cmd_args, timeout)
            
        finally:
            # Clean up temporary script file
            try:
                temp_script.unlink(missing_ok=True)
            except Exception as e:
                self.logger.warning(f"Failed to clean up temp script {temp_script}: {e}")
    
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
