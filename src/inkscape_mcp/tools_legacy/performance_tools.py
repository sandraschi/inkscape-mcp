from __future__ import annotations

"""
Performance Optimization Tools for GIMP MCP Server.

Provides performance optimization, caching, and monitoring capabilities
following FastMCP 2.10 standards.
"""

import asyncio
import hashlib
import logging
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path
from typing import (
    Any, Callable, Dict, List, Literal, Optional, Type, TypeVar, Union, cast
)

from fastmcp import FastMCP

from .base import BaseToolCategory, tool

if sys.version_info >= (3, 10):
    from typing import TypeAlias, ParamSpec
else:
    from typing_extensions import TypeAlias, ParamSpec

logger = logging.getLogger(__name__)

# Type aliases
T = TypeVar('T')
P = ParamSpec('P')
FilePath: TypeAlias = str
CacheKey: TypeAlias = str
OperationID: TypeAlias = str
PerformanceMetric: TypeAlias = Dict[str, Union[float, int, str]]

class CacheStrategy(str, Enum):
    """Available caching strategies."""
    LRU = "lru"          # Least Recently Used
    LFU = "lfu"          # Least Frequently Used
    FIFO = "fifo"        # First In, First Out
    NONE = "none"        # No caching
    MEMORY = "memory"    # In-memory only
    DISK = "disk"        # Disk-based
    HYBRID = "hybrid"    # Memory + Disk

class PerformanceMetricType(str, Enum):
    """Types of performance metrics that can be collected."""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    CPU_USAGE = "cpu_usage"
    GPU_USAGE = "gpu_usage"

@dataclass
class CacheConfig:
    """Configuration for caching behavior."""
    enabled: bool = True
    strategy: CacheStrategy = CacheStrategy.LRU
    max_size: int = 1000
    ttl: Optional[int] = 3600  # Time to live in seconds
    disk_path: Optional[Path] = None
    compress: bool = True
    pickle_protocol: int = 4
    
    def __post_init__(self):
        if self.disk_path is None:
            self.disk_path = Path(".cache/gimp-mcp")
        if not self.disk_path.exists():
            self.disk_path.mkdir(parents=True, exist_ok=True)

@dataclass
class PerformanceConfig:
    """Configuration for performance monitoring."""
    enabled: bool = True
    metrics: List[PerformanceMetricType] = field(
        default_factory=lambda: [
            PerformanceMetricType.EXECUTION_TIME,
            PerformanceMetricType.MEMORY_USAGE,
            PerformanceMetricType.CACHE_HIT_RATE
        ]
    )
    sampling_interval: float = 1.0  # seconds
    history_size: int = 1000
    enable_profiling: bool = False
    profile_output_dir: Path = Path("./profiles")
    
    def __post_init__(self):
        if not self.profile_output_dir.exists():
            self.profile_output_dir.mkdir(parents=True, exist_ok=True)

class PerformanceTools(BaseToolCategory):
    """
    Performance optimization and monitoring tools for GIMP operations.
    
    Provides tools for caching, optimization, performance monitoring,
    and resource management.
    """
    
    def __init__(self, cli_wrapper, config):
        """Initialize performance tools with caching and monitoring."""
        super().__init__(cli_wrapper, config)
        self._cache = {}
        self._performance_metrics = {}
        self._cache_dir = Path(config.temp_directory) / "cache"
        self._cache_dir.mkdir(exist_ok=True)
        
        # Performance monitoring
        self._operation_times = {}
        self._memory_usage = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def register_tools(self, app: FastMCP) -> None:
        """Register all performance tools with FastMCP."""
        
        @app.tool()
        async def optimize_image_processing(
            input_path: str,
            output_path: str,
            optimization_level: str = "balanced",
            enable_caching: bool = True,
            memory_limit_mb: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Optimize image processing with performance enhancements.
            
            Args:
                input_path: Source image file path
                output_path: Destination file path
                optimization_level: Optimization level (fast, balanced, quality)
                enable_caching: Whether to enable result caching
                memory_limit_mb: Memory limit in MB (None for auto)
                
            Returns:
                Dict containing optimization results and performance metrics
            """
            try:
                # Validate inputs
                if not self.validate_file_path(input_path, must_exist=True):
                    return self.create_error_response(f"Invalid input file: {input_path}")
                
                if not self.validate_file_path(output_path, must_exist=False):
                    return self.create_error_response(f"Invalid output path: {output_path}")
                
                valid_optimization_levels = ["fast", "balanced", "quality"]
                if optimization_level not in valid_optimization_levels:
                    return self.create_error_response(
                        f"Invalid optimization level. Must be one of: {valid_optimization_levels}")
                
                # Check cache if enabled
                cache_key = None
                if enable_caching:
                    cache_key = self._generate_cache_key(input_path, optimization_level)
                    cached_result = self._get_cached_result(cache_key)
                    if cached_result:
                        self._cache_hits += 1
                        return self.create_success_response(
                            message="Optimized result retrieved from cache",
                            details={
                                "input_path": input_path,
                                "output_path": output_path,
                                "optimization_level": optimization_level,
                                "cached": True,
                                "cache_key": cache_key
                            }
                        )
                
                # Start performance monitoring
                start_time = time.time()
                start_memory = self._get_memory_usage()
                
                # Create GIMP script with optimization
                script = self._create_optimization_script(
                    input_path, output_path, optimization_level, memory_limit_mb
                )
                
                # Execute the script
                await self.cli_wrapper.execute_script_fu(script)
                
                # End performance monitoring
                end_time = time.time()
                end_memory = self._get_memory_usage()
                
                # Calculate performance metrics
                processing_time = end_time - start_time
                memory_delta = end_memory - start_memory
                
                # Cache result if enabled
                if enable_caching and cache_key:
                    self._cache_result(cache_key, output_path)
                    self._cache_misses += 1
                
                # Store performance metrics
                operation_key = f"optimize_{optimization_level}"
                self._performance_metrics[operation_key] = {
                    "processing_time": processing_time,
                    "memory_delta": memory_delta,
                    "input_size": os.path.getsize(input_path),
                    "output_size": os.path.getsize(output_path),
                    "timestamp": time.time()
                }
                
                return self.create_success_response(
                    message=f"Image processing optimized with {optimization_level} settings",
                    details={
                        "input_path": input_path,
                        "output_path": output_path,
                        "optimization_level": optimization_level,
                        "performance_metrics": {
                            "processing_time_seconds": processing_time,
                            "memory_delta_mb": memory_delta,
                            "input_size_bytes": os.path.getsize(input_path),
                            "output_size_bytes": os.path.getsize(output_path)
                        },
                        "cached": False,
                        "cache_key": cache_key
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Image optimization failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Image optimization failed: {str(e)}")
        
        @app.tool()
        async def clear_cache(
            cache_type: str = "all",
            older_than_hours: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Clear performance cache to free up memory and disk space.
            
            Args:
                cache_type: Type of cache to clear (all, results, metrics, temp)
                older_than_hours: Only clear items older than specified hours
                
            Returns:
                Dict containing cache clearing results
            """
            try:
                valid_cache_types = ["all", "results", "metrics", "temp"]
                if cache_type not in valid_cache_types:
                    return self.create_error_response(
                        f"Invalid cache type. Must be one of: {valid_cache_types}")
                
                cleared_items = 0
                freed_space = 0
                
                if cache_type in ["all", "results"]:
                    # Clear result cache
                    cache_size = len(self._cache)
                    self._cache.clear()
                    cleared_items += cache_size
                
                if cache_type in ["all", "metrics"]:
                    # Clear performance metrics
                    metrics_size = len(self._performance_metrics)
                    self._performance_metrics.clear()
                    cleared_items += metrics_size
                
                if cache_type in ["all", "temp"]:
                    # Clear temporary files
                    temp_files = list(self._cache_dir.glob("*"))
                    for temp_file in temp_files:
                        try:
                            if temp_file.is_file():
                                file_size = temp_file.stat().st_size
                                temp_file.unlink()
                                freed_space += file_size
                                cleared_items += 1
                        except Exception as e:
                            self.logger.warning(f"Failed to delete temp file {temp_file}: {e}")
                
                # Reset counters
                if cache_type in ["all", "metrics"]:
                    self._cache_hits = 0
                    self._cache_misses = 0
                
                return self.create_success_response(
                    message=f"Cache cleared successfully",
                    details={
                        "cache_type": cache_type,
                        "cleared_items": cleared_items,
                        "freed_space_bytes": freed_space,
                        "freed_space_mb": freed_space / (1024 * 1024)
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Cache clearing failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Cache clearing failed: {str(e)}")
        
        @app.tool()
        async def get_performance_metrics(
            operation_type: Optional[str] = None,
            time_range_hours: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Get performance metrics and statistics.
            
            Args:
                operation_type: Specific operation type to analyze (None for all)
                time_range_hours: Time range for analysis in hours (None for all time)
                
            Returns:
                Dict containing performance metrics and analysis
            """
            try:
                current_time = time.time()
                
                if operation_type and operation_type not in self._performance_metrics:
                    return self.create_error_response(f"Operation type '{operation_type}' not found")
                
                # Filter metrics by time range if specified
                filtered_metrics = {}
                if time_range_hours:
                    cutoff_time = current_time - (time_range_hours * 3600)
                    for op_type, metrics in self._performance_metrics.items():
                        if metrics.get("timestamp", 0) >= cutoff_time:
                            filtered_metrics[op_type] = metrics
                else:
                    filtered_metrics = self._performance_metrics
                
                # Filter by operation type if specified
                if operation_type:
                    filtered_metrics = {operation_type: filtered_metrics.get(operation_type, {})}
                
                # Calculate aggregate statistics
                if filtered_metrics:
                    processing_times = [m.get("processing_time", 0) for m in filtered_metrics.values()]
                    memory_deltas = [m.get("memory_delta", 0) for m in filtered_metrics.values()]
                    
                    stats = {
                        "total_operations": len(filtered_metrics),
                        "avg_processing_time": sum(processing_times) / len(processing_times),
                        "min_processing_time": min(processing_times),
                        "max_processing_time": max(processing_times),
                        "avg_memory_delta": sum(memory_deltas) / len(memory_deltas),
                        "total_memory_delta": sum(memory_deltas)
                    }
                else:
                    stats = {
                        "total_operations": 0,
                        "avg_processing_time": 0,
                        "min_processing_time": 0,
                        "max_processing_time": 0,
                        "avg_memory_delta": 0,
                        "total_memory_delta": 0
                    }
                
                return self.create_success_response(
                    message="Performance metrics retrieved successfully",
                    details={
                        "operation_type": operation_type,
                        "time_range_hours": time_range_hours,
                        "cache_statistics": {
                            "cache_hits": self._cache_hits,
                            "cache_misses": self._cache_misses,
                            "hit_rate": self._cache_hits / max(1, self._cache_hits + self._cache_misses)
                        },
                        "performance_statistics": stats,
                        "detailed_metrics": filtered_metrics
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Performance metrics retrieval failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Performance metrics retrieval failed: {str(e)}")
        
        @app.tool()
        async def optimize_batch_processing(
            input_directory: str,
            output_directory: str,
            optimization_settings: Dict[str, Any],
            enable_parallel: bool = True,
            max_workers: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Optimize batch processing with performance enhancements.
            
            Args:
                input_directory: Directory containing input images
                output_directory: Directory for output images
                optimization_settings: Dictionary of optimization parameters
                enable_parallel: Whether to enable parallel processing
                max_workers: Maximum number of parallel workers (None for auto)
                
            Returns:
                Dict containing batch optimization results
            """
            try:
                # Validate inputs
                if not os.path.isdir(input_directory):
                    return self.create_error_response(f"Invalid input directory: {input_directory}")
                
                if not os.path.isdir(output_directory):
                    os.makedirs(output_directory, exist_ok=True)
                
                # Set default optimization settings
                default_settings = {
                    "compression_quality": 85,
                    "interpolation_method": "lanczos",
                    "memory_optimization": True,
                    "cache_results": True
                }
                
                # Merge with provided settings
                final_settings = {**default_settings, **optimization_settings}
                
                # Get list of input files
                input_files = []
                for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.webp']:
                    input_files.extend(Path(input_directory).glob(f"*{ext}"))
                    input_files.extend(Path(input_directory).glob(f"*{ext.upper()}"))
                
                if not input_files:
                    return self.create_error_response("No image files found in input directory")
                
                # Determine optimal worker count
                if max_workers is None:
                    max_workers = min(len(input_files), os.cpu_count() or 4, 8)
                
                # Start performance monitoring
                start_time = time.time()
                start_memory = self._get_memory_usage()
                
                # Process files with optimization
                processed_files = 0
                failed_files = 0
                
                if enable_parallel and max_workers > 1:
                    # Parallel processing
                    semaphore = asyncio.Semaphore(max_workers)
                    
                    async def process_file(file_path):
                        async with semaphore:
                            return await self._process_single_file_optimized(
                                file_path, output_directory, final_settings
                            )
                    
                    # Create tasks for all files
                    tasks = [process_file(file_path) for file_path in input_files]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Count results
                    for result in results:
                        if isinstance(result, Exception):
                            failed_files += 1
                        else:
                            processed_files += 1
                else:
                    # Sequential processing
                    for file_path in input_files:
                        try:
                            await self._process_single_file_optimized(
                                file_path, output_directory, final_settings
                            )
                            processed_files += 1
                        except Exception as e:
                            self.logger.error(f"Failed to process {file_path}: {e}")
                            failed_files += 1
                
                # End performance monitoring
                end_time = time.time()
                end_memory = self._get_memory_usage()
                
                # Calculate performance metrics
                total_time = end_time - start_time
                memory_delta = end_memory - start_memory
                avg_time_per_file = total_time / max(1, processed_files)
                
                return self.create_success_response(
                    message="Batch processing optimization completed",
                    details={
                        "input_directory": input_directory,
                        "output_directory": output_directory,
                        "optimization_settings": final_settings,
                        "processing_results": {
                            "total_files": len(input_files),
                            "processed_files": processed_files,
                            "failed_files": failed_files,
                            "success_rate": processed_files / len(input_files)
                        },
                        "performance_metrics": {
                            "total_processing_time": total_time,
                            "average_time_per_file": avg_time_per_file,
                            "memory_delta_mb": memory_delta,
                            "parallel_processing": enable_parallel,
                            "max_workers": max_workers
                        }
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Batch processing optimization failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"Batch processing optimization failed: {str(e)}")
        
        @app.tool()
        async def get_system_performance_info() -> Dict[str, Any]:
            """
            Get system performance information and resource usage.
            
            Returns:
                Dict containing system performance information
            """
            try:
                import psutil
                
                # Get system information
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Get process information
                process = psutil.Process()
                process_memory = process.memory_info()
                process_cpu = process.cpu_percent()
                
                # Get GIMP-specific information
                gimp_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                    try:
                        if 'gimp' in proc.info['name'].lower():
                            gimp_processes.append({
                                'pid': proc.info['pid'],
                                'memory_mb': proc.info['memory_info'].rss / (1024 * 1024),
                                'cpu_percent': proc.info['cpu_percent']
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                return self.create_success_response(
                    message="System performance information retrieved successfully",
                    details={
                        "system_performance": {
                            "cpu_usage_percent": cpu_percent,
                            "memory_usage_percent": memory.percent,
                            "memory_available_gb": memory.available / (1024**3),
                            "disk_usage_percent": disk.percent,
                            "disk_free_gb": disk.free / (1024**3)
                        },
                        "process_performance": {
                            "memory_usage_mb": process_memory.rss / (1024 * 1024),
                            "cpu_usage_percent": process_cpu
                        },
                        "gimp_processes": gimp_processes,
                        "cache_performance": {
                            "cache_size": len(self._cache),
                            "cache_hits": self._cache_hits,
                            "cache_misses": self._cache_misses,
                            "hit_rate": self._cache_hits / max(1, self._cache_hits + self._cache_misses)
                        }
                    }
                )
                
            except Exception as e:
                self.logger.error(f"System performance info retrieval failed: {str(e)}", exc_info=True)
                return self.create_error_response(f"System performance info retrieval failed: {str(e)}")
    
    def _generate_cache_key(self, input_path: str, optimization_level: str) -> str:
        """Generate a cache key for the given input and optimization level."""
        file_hash = hashlib.md5(open(input_path, 'rb').read()).hexdigest()
        return f"{file_hash}_{optimization_level}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[str]:
        """Get cached result if available."""
        return self._cache.get(cache_key)
    
    def _cache_result(self, cache_key: str, output_path: str) -> None:
        """Cache a result."""
        self._cache[cache_key] = output_path
        
        # Limit cache size
        if len(self._cache) > 100:  # Keep only last 100 results
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
    
    def _create_optimization_script(
        self, 
        input_path: str, 
        output_path: str, 
        optimization_level: str,
        memory_limit_mb: Optional[int]
    ) -> str:
        """Create GIMP script with optimization settings."""
        
        # Set optimization parameters based on level
        if optimization_level == "fast":
            quality = 70
            interpolation = "linear"
            compression = 6
        elif optimization_level == "balanced":
            quality = 85
            interpolation = "cubic"
            compression = 4
        else:  # quality
            quality = 95
            interpolation = "lanczos"
            compression = 2
        
        script = f"""
        (let* (
            (image (car (gimp-file-load RUN-NONINTERACTIVE "{input_path}" "{input_path}")))
            (drawable (car (gimp-image-get-active-layer image))))
            
            ; Apply optimization settings
            (gimp-context-set-interpolation {interpolation})
            (gimp-context-set-quality {quality})
            
            ; Memory optimization if specified
            (if {str(memory_limit_mb is not None).lower()}
                (gimp-context-set-memory-limit (* {memory_limit_mb or 512} 1024 1024)))
            
            ; Save with optimization
            (gimp-file-save RUN-NONINTERACTIVE image drawable "{output_path}" "{output_path}")
            (gimp-image-delete image)
        ))
        """
        
        return script
    
    async def _process_single_file_optimized(
        self, 
        file_path: Path, 
        output_directory: str, 
        settings: Dict[str, Any]
    ) -> None:
        """Process a single file with optimization settings."""
        output_path = Path(output_directory) / f"optimized_{file_path.name}"
        
        # Create optimization script
        script = self._create_optimization_script(
            str(file_path), 
            str(output_path), 
            "balanced",  # Use balanced for batch processing
            settings.get("memory_limit_mb")
        )
        
        # Execute the script
        await self.cli_wrapper.execute_script_fu(script)
