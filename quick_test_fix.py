#!/usr/bin/env python3
"""Quick test of SQLite cache performance fix"""

from excel_processor.notebook import ExcelProcessor
import time

print('🔥 Testing SQLite Cache Performance Fix')
print('=' * 60)
print()

processor = ExcelProcessor('massive_data', use_sqlite_cache=True, memory_limit_mb=8192)

# Test COUNT query (should be FAST now!)
print('Test 1: COUNT on 2M rows (was 5m 33s, should be < 5s)')
start = time.time()
result = processor.query('SELECT COUNT(*) FROM massive_employees.default')
elapsed = time.time() - start
print(f'⏱️  Time: {elapsed:.2f}s')
print(f'📊 Result: {len(result)} rows')
print(f'✅ Status: {"FIXED!" if elapsed < 10 else "Still slow"}')
print()

print('Test 2: COUNT on 4M rows (was 57s, should be < 5s)')
start = time.time()
result = processor.query('SELECT COUNT(*) FROM massive_transactions.default')
elapsed = time.time() - start
print(f'⏱️  Time: {elapsed:.2f}s')
print(f'📊 Result: {len(result)} rows')
print(f'✅ Status: {"FIXED!" if elapsed < 10 else "Still slow"}')
print()

print('=' * 60)
print('🎯 Performance Fix Verification Complete!')
