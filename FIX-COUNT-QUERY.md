# Fix: COUNT(*) and Aggregate Queries Without GROUP BY

## Problem

Queries like `SELECT COUNT(*) FROM table` were returning all rows instead of a single aggregated result.

### Example of Bug
```sql
SELECT COUNT(*) FROM employees.xlsx.staff
```

**Expected**: 1 row with count value  
**Actual**: All 10 employee rows

## Root Cause

The REPL's `_execute_query` method only handled aggregate functions when there was a GROUP BY clause. Queries with aggregate functions but no GROUP BY (like `SELECT COUNT(*)`) were treated as regular SELECT queries and returned all rows.

## Solution

### 1. Added Aggregate Function Detection
Modified the query execution logic to detect aggregate functions in the SELECT clause, even without GROUP BY:

```python
# Check if we have aggregate functions or window functions in SELECT
has_aggregate_functions = False
if parsed_query.select_node:
    from .sql_ast import AggregateFunctionNode, ColumnAliasNode
    for col in parsed_query.select_node.columns:
        if isinstance(col, AggregateFunctionNode):
            has_aggregate_functions = True
        elif isinstance(col, ColumnAliasNode):
            # Check inside aliases (e.g., COUNT(*) as total)
            if isinstance(col.expression, AggregateFunctionNode):
                has_aggregate_functions = True
```

### 2. Created `_execute_simple_aggregation` Method
Added a new method to handle aggregate functions without GROUP BY:

```python
def _execute_simple_aggregation(self, df: pd.DataFrame, parsed_query) -> pd.DataFrame:
    """Execute aggregate functions without GROUP BY."""
    # Calculates aggregates over entire table
    # Returns single-row DataFrame with results
```

Supports:
- `COUNT(*)` - Count all rows
- `COUNT(column)` - Count non-null values
- `SUM(column)` - Sum values
- `AVG(column)` - Average values
- `MIN(column)` - Minimum value
- `MAX(column)` - Maximum value

### 3. Updated Query Execution Flow
```python
if has_aggregate_functions:
    # Handle aggregate functions without GROUP BY
    df = self._execute_simple_aggregation(df, parsed_query)
elif has_window_functions:
    df = self._execute_window_functions(df, parsed_query)
else:
    # Regular SELECT
    df = self._apply_column_selection(df, parsed_query.select_node.columns)
```

## Test Results

### Before Fix
```bash
$ python -m excel_processor --db sample_data --query 'SELECT COUNT(*) FROM employees.xlsx.staff'
# Returns all 10 employee rows ❌
```

### After Fix
```bash
$ python -m excel_processor --db sample_data --query 'SELECT COUNT(*) FROM employees.xlsx.staff'
# Returns:
┌──────────┐
│ count(*) │
├──────────┤
│ 10       │
└──────────┘
✅ Correct!
```

## Additional Test Cases

### COUNT with Alias
```sql
SELECT COUNT(*) as total FROM employees.xlsx.staff
```
Result: `total: 10` ✅

### Multiple Aggregates
```sql
SELECT AVG(salary) as avg_salary, MAX(salary) as max_salary FROM employees.xlsx.staff
```
Result: `avg_salary: 72900, max_salary: 85000` ✅

### COUNT on Column
```sql
SELECT COUNT(department) FROM employees.xlsx.staff
```
Result: `count(department): 10` ✅

## Files Modified

- `excel_processor/repl.py`
  - Added aggregate function detection in `_execute_query()`
  - Created `_execute_simple_aggregation()` method
  - Updated query execution flow

## Impact

- ✅ `SELECT COUNT(*)` now works correctly
- ✅ All aggregate functions work without GROUP BY
- ✅ Aliases are properly handled
- ✅ Multiple aggregates in one query work
- ✅ Backward compatible with existing GROUP BY queries

## Related

This fix complements the existing GROUP BY aggregation logic and doesn't affect:
- GROUP BY queries (still work as before)
- Window functions
- Regular SELECT queries
