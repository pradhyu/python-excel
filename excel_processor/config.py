"""
Configuration settings for Excel DataFrame Processor
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CacheConfig:
    """SQLite cache configuration"""
    enabled: bool = True
    cache_dir: Optional[str] = None
    auto_cache_on_load: bool = True
    cache_threshold_mb: float = 5.0  # Only cache files larger than this
    

@dataclass
class PerformanceConfig:
    """Performance optimization settings"""
    use_sqlite_cache: bool = True
    memory_limit_mb: float = 2048.0
    enable_query_optimization: bool = True
    parallel_loading: bool = False
    chunk_size: int = 10000  # For large file processing
    

@dataclass
class ProcessorConfig:
    """Main processor configuration"""
    cache: CacheConfig = CacheConfig()
    performance: PerformanceConfig = PerformanceConfig()
    verbose: bool = True
    log_queries: bool = True
    

# Default configuration
DEFAULT_CONFIG = ProcessorConfig()

# High-performance configuration for large datasets
HIGH_PERFORMANCE_CONFIG = ProcessorConfig(
    cache=CacheConfig(
        enabled=True,
        auto_cache_on_load=True,
        cache_threshold_mb=1.0
    ),
    performance=PerformanceConfig(
        use_sqlite_cache=True,
        memory_limit_mb=4096.0,
        enable_query_optimization=True,
        parallel_loading=False
    )
)

# Low-memory configuration
LOW_MEMORY_CONFIG = ProcessorConfig(
    cache=CacheConfig(
        enabled=True,
        auto_cache_on_load=False,
        cache_threshold_mb=10.0
    ),
    performance=PerformanceConfig(
        use_sqlite_cache=True,
        memory_limit_mb=512.0,
        enable_query_optimization=True
    )
)
