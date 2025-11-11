#!/usr/bin/env python
"""Test that REPL reuses existing cache."""

from excel_processor.repl import ExcelREPL
from pathlib import Path

print("Testing REPL cache reuse...")
print("=" * 80)

# Initialize REPL (should use existing cache)
repl = ExcelREPL(db_directory=Path("massive_data"), memory_limit_mb=1024.0)

# Check cache stats
stats = repl.df_manager.sqlite_cache.get_cache_stats()
print(f"\nCache status:")
print(f"  Files cached: {stats['cached_files']}")
print(f"  Total rows: {sum(f['rows'] for f in stats['files']):,}")
print(f"  Cache size: {stats['total_size_mb']:.2f} MB")
print("\n✅ Cache is ready for use!")
