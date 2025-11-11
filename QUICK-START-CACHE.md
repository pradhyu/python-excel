# Quick Start: SQLite Cache

## TL;DR

The REPL now automatically caches your data to SQLite for instant performance. First run takes time to cache, subsequent runs are instant!

## Usage

### Start the REPL
```bash
python -m excel_processor --db massive_data
```

**First time**: Caches all files (~2 min for 6M rows)  
**Every other time**: Instant startup (<0.1s)

### Commands
```sql
SHOW CACHE       -- View cache stats
SHOW DB          -- List all files
SELECT ...       -- Query instantly
REBUILD CACHE    -- Rebuild if needed
```

## Performance

| Scenario | Time | Notes |
|----------|------|-------|
| First startup | ~120s | One-time caching |
| Subsequent startups | <0.1s | **2300x faster!** |
| Queries (6M rows) | <1s | Sub-second |

## Example

```bash
$ python -m excel_processor --db massive_data

✅ Using existing SQLite cache (3 files, 6,000,027 rows)
   ✓ All files up to date

excel> SELECT COUNT(*) FROM massive_employees.csv.default
# Instant result: 2,000,000 rows

excel> SELECT department, AVG(salary) 
       FROM massive_employees.csv.default 
       GROUP BY department
# <1 second for aggregation on 2M rows
```

## Cache Location

- Default: `{your_data_dir}/.excel_cache/`
- Persistent across sessions
- Automatic management

## Tips

1. **First run**: Be patient, it's caching everything
2. **Subsequent runs**: Enjoy instant startup!
3. **New files**: Automatically detected and cached
4. **Check status**: Use `SHOW CACHE` anytime
5. **Rebuild**: Use `REBUILD CACHE` if data changes

## That's It!

Just run the REPL and it handles everything automatically. First run caches, every other run is instant!
