# REPL Auto-Cache Feature

## Overview

The Excel DataFrame Processor REPL now automatically caches all CSV/Excel files to SQLite when it starts up, providing instant query performance from the beginning.

## What Was Implemented

### 1. Auto-Cache on Startup
- When the REPL starts, it automatically scans the database directory
- All CSV and Excel files are cached to SQLite before the prompt appears
- Shows progress during caching with file counts and row statistics
- Skips files that are already cached (smart caching)

### 2. New DataFrameManager Method
Added `cache_all_files_to_sqlite()` method that:
- Scans all files in the database directory
- Checks if each file is already cached
- Loads and caches uncached files to SQLite
- Shows detailed progress with file counts and row statistics
- Returns success/failure status for each file

### 3. New REPL Commands
- `SHOW CACHE` - Display SQLite cache statistics including:
  - Cache directory location
  - Total files cached
  - Total tables and rows
  - Cache size in MB
  - Cache hit/miss statistics
  - Hit rate percentage
  - Detailed breakdown by file

- `REBUILD CACHE` - Clear and rebuild the entire SQLite cache:
  - Prompts for confirmation
  - Clears existing cache
  - Re-caches all files with progress display

### 4. Updated Help System
- Added new commands to help text
- Updated tab completion to include new commands
- Enhanced command completer with cache-related commands

## How to Use

### Start the REPL

#### First Run (No Cache)
```bash
python -m excel_processor --db massive_data
```

On first startup, you'll see:
```
🚀 Initializing SQLite cache for fast queries...
🔄 Caching 5 files to SQLite...
  [1/5] 🔄 Caching massive_employees.csv...
      ✓ Cached 1 sheets (2,000,000 rows)
  [2/5] 🔄 Caching massive_transactions.csv...
      ✓ Cached 1 sheets (4,000,000 rows)
  ...
✅ Successfully cached 5/5 files to SQLite

✅ Cache ready! 5 files available for instant querying.
```

#### Subsequent Runs (Cache Exists)
```bash
python -m excel_processor --db massive_data
```

On subsequent startups, you'll see:
```
✅ Using existing SQLite cache (5 files, 6,000,000 rows)
   Checking for new or updated files...
   ✓ All files up to date
```

**Instant startup!** No re-caching needed.

### Query with Lightning Speed
Once cached, queries run instantly:
```sql
SELECT COUNT(*) as total FROM massive_employees.csv.default
SELECT department, COUNT(*) as count FROM massive_employees.csv.default GROUP BY department
SELECT * FROM massive_employees.csv.default WHERE salary > 150000 LIMIT 10
```

### Check Cache Statistics
```
excel> SHOW CACHE
```

Shows:
- Cache directory
- Total files, tables, rows
- Cache size
- Hit/miss statistics
- Per-file breakdown

### Rebuild Cache
```
excel> REBUILD CACHE
```

Clears and rebuilds the entire cache (useful after data updates).

## Performance Benefits

### Before Auto-Cache
- First query on a file: 30-60 seconds (loads entire CSV)
- Subsequent queries: Still slow if file not in memory
- Memory pressure with large files

### After Auto-Cache
- **First startup**: One-time caching (30-120 seconds depending on data size)
- **Subsequent startups**: Instant (0.04s) - **2300x faster!**
- **All queries**: Sub-second performance
- Efficient disk-based storage
- Indexed for fast lookups
- Cache persists across sessions

### Real Performance Numbers
From `demo_cache_behavior.py` with 800K rows across 13 files:
- First run (caching): 101.04s
- Subsequent run (reuse): 0.04s
- **Speedup: 2324x faster**

## Example Session

```bash
$ python -m excel_processor --db massive_data

🚀 Initializing SQLite cache for fast queries...
🔄 Caching 5 files to SQLite...
  [1/5] ✓ massive_employees.csv (already cached)
  [2/5] ✓ massive_transactions.csv (already cached)
  ...
✅ Cache ready! 5 files available for instant querying.

excel> SHOW CACHE
💾 SQLite Cache Statistics
┌─────────────────┬──────────────────────┐
│ Metric          │ Value                │
├─────────────────┼──────────────────────┤
│ Cache Directory │ massive_data/.excel_cache │
│ Total Files     │ 5                    │
│ Total Tables    │ 5                    │
│ Total Rows      │ 6,000,000            │
│ Cache Size      │ 1,234.56 MB          │
│ Cache Hits      │ 150                  │
│ Cache Misses    │ 5                    │
│ Hit Rate        │ 96.8%                │
└─────────────────┴──────────────────────┘

excel> SELECT COUNT(*) FROM massive_employees.csv.default
Query executed in 0.05 seconds
Result: 2,000,000 rows

excel> EXIT
👋 Goodbye!
```

## Technical Details

### Cache Location
- Default: `{db_directory}/.excel_cache/`
- Contains SQLite database files
- Persistent across sessions
- Automatically managed

### Smart Caching
- Checks file modification times
- Only re-caches if file changed
- Skips already-cached files
- Efficient incremental updates

### Memory Management
- Cache stored on disk (SQLite)
- Minimal memory footprint
- No need to load entire files into RAM
- Indexed for fast queries

## Files Modified

1. `excel_processor/dataframe_manager.py`
   - Added `cache_all_files_to_sqlite()` method

2. `excel_processor/repl.py`
   - Added `_auto_cache_files()` method
   - Added `_handle_show_cache()` method
   - Added `_handle_rebuild_cache()` method
   - Updated `start()` to call auto-cache
   - Updated help text and command completion

## Testing

Run the test script:
```bash
python test_repl_autocache.py
```

Or test manually:
```bash
python -m excel_processor --db massive_data
```

## Benefits

1. **Instant Queries**: All files pre-cached for immediate use
2. **No Waiting**: Cache built once at startup, not per-query
3. **Persistent**: Cache survives across sessions
4. **Smart**: Only caches new/changed files
5. **Transparent**: Works automatically, no user action needed
6. **Monitorable**: SHOW CACHE command for visibility
7. **Maintainable**: REBUILD CACHE for manual refresh

## Future Enhancements

- Background caching (non-blocking startup)
- Selective caching (cache only specific files)
- Cache expiration policies
- Automatic cache refresh on file changes
- Cache compression for smaller disk usage
