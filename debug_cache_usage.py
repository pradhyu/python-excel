#!/usr/bin/env python3
"""Debug why SQLite cache isn't being used"""

from excel_processor.notebook import ExcelProcessor
import time

processor = ExcelProcessor('massive_data', use_sqlite_cache=True, memory_limit_mb=8192)

# Check cache status
print("Checking SQLite cache status...")
cache_stats = processor.get_cache_stats()
print(f"Cache enabled: {cache_stats.get('enabled')}")
print(f"Cached files: {cache_stats.get('cached_files', 0)}")
print()

# Try direct SQLite query
print("Testing direct SQLite query...")
conn = processor.df_manager.sqlite_cache.get_connection('massive_employees.csv')
if conn:
    print("✅ Got SQLite connection")
    
    # Try simple COUNT
    import pandas as pd
    start = time.time()
    result = pd.read_sql_query('SELECT COUNT(*) as count FROM "default"', conn)
    elapsed = time.time() - start
    print(f"Direct SQLite COUNT: {elapsed:.3f}s")
    print(f"Result: {result}")
else:
    print("❌ No SQLite connection")

print()
print("Testing through processor.query()...")
start = time.time()
result = processor.query('SELECT COUNT(*) FROM massive_employees.default')
elapsed = time.time() - start
print(f"Processor query: {elapsed:.2f}s")
print(f"Rows: {len(result)}")
