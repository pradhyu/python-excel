#!/usr/bin/env python
"""Demonstrate cache behavior: first run vs subsequent runs."""

import time
import shutil
from pathlib import Path
from excel_processor.dataframe_manager import DataFrameManager

print("=" * 80)
print("DEMO: SQLite Cache Behavior")
print("=" * 80)

# Use a test directory with smaller files
test_dir = Path("sample_data")
cache_dir = test_dir / ".excel_cache"

print(f"\nTest directory: {test_dir}")
print(f"Cache directory: {cache_dir}")

# Scenario 1: No cache exists
print("\n" + "=" * 80)
print("SCENARIO 1: First Run (No Cache)")
print("=" * 80)

if cache_dir.exists():
    print(f"Removing existing cache: {cache_dir}")
    shutil.rmtree(cache_dir)

print("\nInitializing DataFrameManager...")
start = time.time()
df_manager = DataFrameManager(test_dir, use_sqlite_cache=True)
print(f"✓ Initialized in {time.time() - start:.2f}s")

print("\nCaching files...")
start = time.time()
cached = df_manager.cache_all_files_to_sqlite(show_progress=True)
cache_time = time.time() - start
print(f"\n✓ Caching completed in {cache_time:.2f}s")
print(f"  Files cached: {sum(1 for v in cached.values() if v)}/{len(cached)}")

# Get cache stats
stats = df_manager.sqlite_cache.get_cache_stats()
print(f"\nCache Statistics:")
print(f"  Files: {stats['cached_files']}")
print(f"  Total rows: {sum(f['rows'] for f in stats['files']):,}")
print(f"  Size: {stats['total_size_mb']:.2f} MB")

# Scenario 2: Cache exists
print("\n" + "=" * 80)
print("SCENARIO 2: Subsequent Run (Cache Exists)")
print("=" * 80)

print("\nInitializing new DataFrameManager...")
start = time.time()
df_manager2 = DataFrameManager(test_dir, use_sqlite_cache=True)
print(f"✓ Initialized in {time.time() - start:.2f}s")

print("\nChecking cache (should find existing files)...")
start = time.time()
cached2 = df_manager2.cache_all_files_to_sqlite(show_progress=True)
reuse_time = time.time() - start
print(f"\n✓ Cache check completed in {reuse_time:.2f}s")
print(f"  Files already cached: {sum(1 for v in cached2.values() if v)}/{len(cached2)}")

# Compare times
print("\n" + "=" * 80)
print("PERFORMANCE COMPARISON")
print("=" * 80)
print(f"First run (caching):     {cache_time:.2f}s")
print(f"Subsequent run (reuse):  {reuse_time:.2f}s")
if cache_time > 0:
    speedup = cache_time / reuse_time if reuse_time > 0 else float('inf')
    print(f"Speedup:                 {speedup:.1f}x faster")

print("\n" + "=" * 80)
print("✅ Demo Complete!")
print("=" * 80)
print("\nKey Takeaways:")
print("  1. First run caches all files (one-time cost)")
print("  2. Subsequent runs detect existing cache instantly")
print("  3. No re-caching needed unless files change")
print("  4. Queries use cached data for instant performance")
