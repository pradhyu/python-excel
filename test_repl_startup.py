#!/usr/bin/env python
"""Test REPL startup to ensure it's not stuck."""

import sys
import time
from pathlib import Path
from excel_processor.repl import ExcelREPL

print("Testing REPL startup...")
print("=" * 80)

start = time.time()

# Initialize REPL
repl = ExcelREPL(db_directory=Path("sample_data"), memory_limit_mb=1024.0)

init_time = time.time() - start

print(f"\n✅ REPL initialized successfully in {init_time:.2f}s")
print(f"   Cache enabled: {repl.df_manager.use_sqlite_cache}")

# Check cache stats
if repl.df_manager.use_sqlite_cache:
    stats = repl.df_manager.sqlite_cache.get_cache_stats()
    print(f"   Files cached: {stats.get('cached_files', 0)}")
    total_rows = sum(f['rows'] for f in stats.get('files', []))
    print(f"   Total rows: {total_rows:,}")

print("\n✅ REPL is ready and not stuck!")
print("=" * 80)
