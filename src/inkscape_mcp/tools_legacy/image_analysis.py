from __future__ import annotations

"""
Image Analysis Tools for GIMP MCP Server.

Provides advanced image analysis capabilities including quality assessment,
content analysis, and metadata extraction following FastMCP 2.10 standards.
"""

import asyncio
import logging
import math
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any, Dict, List, Literal, Optional, Sequence, Set, Tuple, TypeVar, Union, cast, TypedDict
)

from fastmcp import FastMCP

# Optional numpy import with type checking
try:
    import numpy as np
    import numpy.typing as npt
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore
    npt = None  # type: ignore
    HAS_NUMPY = False

from .base import BaseToolCategory, tool

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

logger = logging.getLogger(__name__)

# Type aliases
FilePath: TypeAlias = str
ImageData: TypeAlias = Any  # numpy.ndarray | PIL.Image.Image | GIMP image
AnalysisResult: TypeAlias = Dict[str, Any]

class AnalysisType(str, Enum):
    """Types of image analysis that can be performed."""
    BASIC = "basic"
    COMPREHENSIVE = "comprehensive"
    DETAILED = "detailed"
    QUALITY = "quality"
    NOISE = "noise"
    COLOR = "color"
    COMPOSITION = "composition"
    METADATA = "metadata"

class ImageQualityMetrics(TypedDict, total=False):
    """Metrics for image quality assessment."""
    sharpness: float
    noise_level: float
    contrast: float
    brightness: float
    color_balance: Dict[str, float]
    dynamic_range: float
    compression_artifacts: float
    blur_detection: Dict[str, float]
    exposure: Dict[str, float]
    snr: Optional[float]  # Signal-to-Noise Ratio
    psnr: Optional[float]  # Peak Signal-to-Noise Ratio
    ssim: Optional[float]  # Structural Similarity Index

@dataclass
class ImageAnalysisConfig:
    """Configuration for image analysis operations."""
    analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE
    include_metrics: List[str] = field(default_factory=lambda: ["all"])
    export_visualization: bool = False
    output_format: str = "json"
    max_dimension: int = 4000

class ImageAnalysisTools(BaseToolCategory):
    """
    Advanced image analysis tools for GIMP operations.
    
    Provides tools for image quality assessment, content analysis,
    metadata extraction, and statistical analysis.
    """
    
    def register_tools(self, app: FastMCP) -> None:
        """Register all image analysis tools with FastMCP."""
        
        @app.tool()
        async def analyze_image_quality(
            input_path: str,
            analysis_type: str = "comprehensive"
        ) -> Dict[str, Any]:
            """
            Analyze image quality and provide detailed assessment.
            
            Args:
                input_path: Source image file path
                analysis_type: Type of analysis (basic, comprehensive, detailed)
                
            Returns:
                Dict containing image quality analysis results
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                valid_analysis_types = ["basic", "comprehensive", "detailed"]
                if analysis_type not in valid_analysis_types:
                    return self.create_error_response(
                        f"Invalid analysis type. Must be one of: {valid_analysis_types}")
                
                # Create GIMP script for quality analysis
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (width (car (gimp-image-width image)))
                    (height (car (gimp-image-height image)))
                    (area (* width height))
                    (aspect-ratio (/ (float width) (float height))))
                    
                    ; Basic quality metrics
                    (gimp-message (string-append
                        "Image Quality Analysis:" "\\n"
                        "Dimensions: " (number->string width) "x" (number->string height) "\\n"
                        "Total Pixels: " (number->string area) "\\n"
                        "Aspect Ratio: " (number->string aspect-ratio) "\\n"
                        "File Size: " (number->string (car (gimp-image-get-file-size image))) " bytes"))
                    
                    ; Resolution analysis
                    (let* (
                        (dpi-x (car (gimp-image-get-resolution image)))
                        (dpi-y (cadr (gimp-image-get-resolution image))))
                        (gimp-message (string-append
                            "Resolution: " (number->string dpi-x) "x" (number->string dpi-y) " DPI")))
                    
                    ; Color depth analysis
                    (let* (
                        (color-type (car (gimp-drawable-type drawable))))
                        (gimp-message (string-append
                            "Color Type: " (symbol->string color-type))))
                    
                    ; Layer analysis
                    (let* (
                        (layers (gimp-image-get-layers image))
                        (num-layers (car layers)))
                        (gimp-message (string-append
                            "Number of Layers: " (number->string num-layers))))
                    
                    (gimp-image-delete image)
                ))
                """
                
                # Execute the script
                output = await self.cli_wrapper.execute_script_fu(script)
                
                # Parse output for structured response
                quality_metrics = self._parse_quality_analysis(output)
                
                return self.create_success_response(
                    message="Image quality analysis completed successfully",
                    details={
                        "input_path": input_path,
                        "analysis_type": analysis_type,
                        "quality_metrics": quality_metrics,
                        "raw_output": output
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Image quality analysis failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Image quality analysis failed: {str(e)}")
        
        @app.tool()
        async def extract_image_statistics(
            input_path: str,
            include_histogram: bool = True,
            include_color_info: bool = True
        ) -> Dict[str, Any]:
            """
            Extract comprehensive image statistics and metadata.
            
            Args:
                input_path: Source image file path
                include_histogram: Whether to include histogram data
                include_color_info: Whether to include color information
                
            Returns:
                Dict containing image statistics
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                # Create GIMP script for statistics extraction
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (width (car (gimp-image-width image)))
                    (height (car (gimp-image-height image))))
                    
                    ; Basic statistics
                    (gimp-message (string-append
                        "Image Statistics:" "\\n"
                        "Width: " (number->string width) " pixels" "\\n"
                        "Height: " (number->string height) " pixels" "\\n"
                        "Total Pixels: " (number->string (* width height)) "\\n"
                        "File Format: " (car (gimp-image-get-file-format image))))
                    
                    ; Color information
                    (if {str(include_color_info).lower()}
                        (let* (
                            (color-type (car (gimp-drawable-type drawable)))
                            (has-alpha (gimp-drawable-has-alpha drawable)))
                            (gimp-message (string-append
                                "Color Information:" "\\n"
                                "Color Type: " (symbol->string color-type) "\\n"
                                "Has Alpha Channel: " (if has-alpha "Yes" "No")))))
                    
                    ; Histogram data
                    (if {str(include_histogram).lower()}
                        (let* (
                            (histogram (gimp-drawable-histogram drawable 0))
                            (mean (car histogram))
                            (std-dev (cadr histogram))
                            (median (caddr histogram))
                            (pixels (cadddr histogram))
                            (count (car (cddddr histogram))))
                            (gimp-message (string-append
                                "Histogram Data:" "\\n"
                                "Mean: " (number->string mean) "\\n"
                                "Standard Deviation: " (number->string std-dev) "\\n"
                                "Median: " (number->string median) "\\n"
                                "Total Pixels: " (number->string pixels) "\\n"
                                "Count: " (number->string count)))))
                    
                    (gimp-image-delete image)
                ))
                """
                
                # Execute the script
                output = await self.cli_wrapper.execute_script_fu(script)
                
                # Parse output for structured response
                statistics = self._parse_statistics_output(output)
                
                return self.create_success_response(
                    message="Image statistics extracted successfully",
                    details={
                        "input_path": input_path,
                        "statistics": statistics,
                        "raw_output": output
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Image statistics extraction failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Image statistics extraction failed: {str(e)}")
        
        @app.tool()
        async def detect_image_issues(
            input_path: str,
            check_types: List[str] = ["all"]
        ) -> Dict[str, Any]:
            """
            Detect common image issues and quality problems.
            
            Args:
                input_path: Source image file path
                check_types: Types of issues to check for
                
            Returns:
                Dict containing detected issues and recommendations
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                valid_check_types = [
                    "all", "resolution", "compression", "color", "noise", "artifacts"
                ]
                if not all(t in valid_check_types for t in check_types):
                    return self.create_error_response(
                        f"Invalid check types. Must be one of: {valid_check_types}")
                
                # Create GIMP script for issue detection
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (width (car (gimp-image-width image)))
                    (height (car (gimp-image-height image)))
                    (issues '()))
                    
                    ; Resolution check
                    (if (or (< width 800) (< height 600))
                        (set! issues (cons "Low resolution - may appear pixelated" issues)))
                    
                    ; Aspect ratio check
                    (let* (
                        (aspect-ratio (/ (float width) (float height))))
                        (if (or (< aspect-ratio 0.5) (> aspect-ratio 2.0))
                            (set! issues (cons "Extreme aspect ratio - may not display well" issues))))
                    
                    ; Color depth check
                    (let* (
                        (color-type (car (gimp-drawable-type drawable))))
                        (if (eq? color-type INDEXED)
                            (set! issues (cons "Indexed color - limited color palette" issues))))
                    
                    ; File size check
                    (let* (
                        (file-size (car (gimp-image-get-file-size image))))
                        (if (> file-size 10000000)  ; 10MB
                            (set! issues (cons "Large file size - may be slow to process" issues))))
                    
                    ; Report issues
                    (if (null? issues)
                        (gimp-message "No issues detected - image appears to be in good condition")
                        (gimp-message (string-append
                            "Detected Issues:" "\\n"
                            (apply string-append (map (lambda (issue) (string-append issue "\\n")) issues)))))
                    
                    (gimp-image-delete image)
                ))
                """
                
                # Execute the script
                output = await self.cli_wrapper.execute_script_fu(script)
                
                # Parse output for structured response
                issues = self._parse_issues_output(output)
                
                return self.create_success_response(
                    message="Image issue detection completed",
                    details={
                        "input_path": input_path,
                        "check_types": check_types,
                        "detected_issues": issues,
                        "raw_output": output
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Image issue detection failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Image issue detection failed: {str(e)}")
        
        @app.tool()
        async def compare_images(
            image1_path: str,
            image2_path: str,
            comparison_type: str = "visual"
        ) -> Dict[str, Any]:
            """
            Compare two images and provide analysis.
            
            Args:
                image1_path: First image file path
                image2_path: Second image file path
                comparison_type: Type of comparison (visual, statistical, metadata)
                
            Returns:
                Dict containing image comparison results
            """
            try:
                # Validate inputs
                if not self.validate_file_path(image1_path, must_exist=True):
                    return self.create_error_response(f"Invalid first image file: {image1_path}")
                
                if not self.validate_file_path(image2_path, must_exist=True):
                    return self.create_error_response(f"Invalid second image file: {image2_path}")
                
                valid_comparison_types = ["visual", "statistical", "metadata", "all"]
                if comparison_type not in valid_comparison_types:
                    return self.create_error_response(
                        f"Invalid comparison type. Must be one of: {valid_comparison_types}")
                
                # Create GIMP script for image comparison
                script = f"""
                (let* (
                    (image1 (car (gimp-file-load RUN-NONINTERACTIVE "{image1_path}" "{image1_path}")))
                    (image2 (car (gimp-file-load RUN-NONINTERACTIVE "{image2_path}" "{image2_path}")))
                    (drawable1 (car (gimp-image-get-active-layer image1)))
                    (drawable2 (car (gimp-image-get-active-layer image2)))
                    (width1 (car (gimp-image-width image1)))
                    (height1 (car (gimp-image-height image1)))
                    (width2 (car (gimp-image-width image2)))
                    (height2 (car (gimp-image-height image2))))
                    
                    ; Basic comparison
                    (gimp-message (string-append
                        "Image Comparison Results:" "\\n"
                        "Image 1: " (number->string width1) "x" (number->string height1) "\\n"
                        "Image 2: " (number->string width2) "x" (number->string height2)))
                    
                    ; Size comparison
                    (if (and (= width1 width2) (= height1 height2))
                        (gimp-message "Images have identical dimensions")
                        (gimp-message "Images have different dimensions"))
                    
                    ; Aspect ratio comparison
                    (let* (
                        (aspect1 (/ (float width1) (float height1)))
                        (aspect2 (/ (float width2) (float height2))))
                        (if (= aspect1 aspect2)
                            (gimp-message "Images have identical aspect ratios")
                            (gimp-message (string-append
                                "Different aspect ratios: " 
                                (number->string aspect1) " vs " (number->string aspect2)))))
                    
                    ; Color type comparison
                    (let* (
                        (color1 (car (gimp-drawable-type drawable1)))
                        (color2 (car (gimp-drawable-type drawable2))))
                        (if (eq? color1 color2)
                            (gimp-message "Images have identical color types")
                            (gimp-message (string-append
                                "Different color types: " 
                                (symbol->string color1) " vs " (symbol->string color2)))))
                    
                    (gimp-image-delete image1)
                    (gimp-image-delete image2)
                ))
                """
                
                # Execute the script
                output = await self.cli_wrapper.execute_script_fu(script)
                
                # Parse output for structured response
                comparison_results = self._parse_comparison_output(output)
                
                return self.create_success_response(
                    message="Image comparison completed successfully",
                    details={
                        "image1_path": image1_path,
                        "image2_path": image2_path,
                        "comparison_type": comparison_type,
                        "comparison_results": comparison_results,
                        "raw_output": output
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Image comparison failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Image comparison failed: {str(e)}")
        
        @app.tool()
        async def generate_image_report(
            input_path: str,
            report_format: str = "detailed"
        ) -> Dict[str, Any]:
            """
            Generate a comprehensive image analysis report.
            
            Args:
                input_path: Source image file path
                report_format: Format of the report (basic, detailed, technical)
                
            Returns:
                Dict containing comprehensive image report
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                valid_report_formats = ["basic", "detailed", "technical"]
                if report_format not in valid_report_formats:
                    return self.create_error_response(
                        f"Invalid report format. Must be one of: {valid_report_formats}")
                
                # Create GIMP script for comprehensive report
                script = f"""
                (let* (
                    (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
                    (drawable (car (gimp-image-get-active-layer image)))
                    (width (car (gimp-image-width image)))
                    (height (car (gimp-image-height image)))
                    (file-size (car (gimp-image-get-file-size image)))
                    (file-format (car (gimp-image-get-file-format image)))
                    (color-type (car (gimp-drawable-type drawable)))
                    (has-alpha (gimp-drawable-has-alpha drawable))
                    (layers (gimp-image-get-layers image))
                    (num-layers (car layers)))
                    
                    ; Generate comprehensive report
                    (gimp-message (string-append
                        "=== IMAGE ANALYSIS REPORT ===" "\\n\\n"
                        "File Information:" "\\n"
                        "- Path: {input_path}" "\\n"
                        "- Format: " (symbol->string file-format) "\\n"
                        "- Size: " (number->string file-size) " bytes" "\\n\\n"
                        
                        "Image Properties:" "\\n"
                        "- Dimensions: " (number->string width) "x" (number->string height) " pixels" "\\n"
                        "- Total Pixels: " (number->string (* width height)) "\\n"
                        "- Aspect Ratio: " (number->string (/ (float width) (float height))) "\\n"
                        "- Resolution: " (number->string (car (gimp-image-get-resolution image))) " DPI" "\\n\\n"
                        
                        "Color Information:" "\\n"
                        "- Color Type: " (symbol->string color-type) "\\n"
                        "- Alpha Channel: " (if has-alpha "Yes" "No") "\\n"
                        "- Number of Layers: " (number->string num-layers) "\\n\\n"
                        
                        "Quality Assessment:" "\\n"
                        "- Resolution: " (if (>= width 1920) "High" (if (>= width 1280) "Medium" "Low")) "\\n"
                        "- File Size: " (if (> file-size 5000000) "Large" (if (> file-size 1000000) "Medium" "Small")) "\\n"
                        "- Color Depth: " (if (eq? color-type RGB) "Full Color" "Limited Color")))
                    
                    (gimp-image-delete image)
                ))
                """
                
                # Execute the script
                output = await self.cli_wrapper.execute_script_fu(script)
                
                # Parse output for structured response
                report_data = self._parse_report_output(output)
                
                return self.create_success_response(
                    message="Image analysis report generated successfully",
                    details={
                        "input_path": input_path,
                        "report_format": report_format,
                        "report_data": report_data,
                        "raw_output": output
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Image report generation failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Image report generation failed: {str(e)}")
    
    def _parse_quality_analysis(self, output: str) -> Dict[str, Any]:
        """Parse quality analysis output into structured data."""
        try:
            lines = output.strip().split('\n')
            metrics = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    metrics[key.strip()] = value.strip()
            
            return metrics
        except Exception as e:
            self.logger.warning(f"Failed to parse quality analysis output: {e}")
            return {"raw_output": output}
    
    def _parse_statistics_output(self, output: str) -> Dict[str, Any]:
        """Parse statistics output into structured data."""
        try:
            lines = output.strip().split('\n')
            stats = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    stats[key.strip()] = value.strip()
            
            return stats
        except Exception as e:
            self.logger.warning(f"Failed to parse statistics output: {e}")
            return {"raw_output": output}
    
    def _parse_issues_output(self, output: str) -> Dict[str, Any]:
        """Parse issues output into structured data."""
        try:
            lines = output.strip().split('\n')
            issues = []
            
            for line in lines:
                if line.strip() and not line.startswith('==='):
                    issues.append(line.strip())
            
            return {
                "total_issues": len(issues),
                "issues": issues
            }
        except Exception as e:
            self.logger.warning(f"Failed to parse issues output: {e}")
            return {"raw_output": output}
    
    def _parse_comparison_output(self, output: str) -> Dict[str, Any]:
        """Parse comparison output into structured data."""
        try:
            lines = output.strip().split('\n')
            comparison = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    comparison[key.strip()] = value.strip()
            
            return comparison
        except Exception as e:
            self.logger.warning(f"Failed to parse comparison output: {e}")
            return {"raw_output": output}
    
    def _parse_report_output(self, output: str) -> Dict[str, Any]:
        """Parse report output into structured data."""
        try:
            lines = output.strip().split('\n')
            report = {}
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('==='):
                    continue
                elif line.endswith(':') and not line.startswith('-'):
                    current_section = line[:-1]
                    report[current_section] = {}
                elif line.startswith('-') and current_section:
                    if ':' in line:
                        key, value = line[1:].split(':', 1)
                        report[current_section][key.strip()] = value.strip()
            
            return report
        except Exception as e:
            self.logger.warning(f"Failed to parse report output: {e}")
            return {"raw_output": output}
