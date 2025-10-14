# Quick Start Guide

Get up and running with the Excel DataFrame Processor in 5 minutes!

## 1. Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repository-url>
cd excel-dataframe-processor
uv sync
```

## 2. Create Sample Data

```bash
# Generate sample Excel files
uv run python create_sample_data.py
```

This creates:
- `employees.xlsx` - Employee data with departments and salaries
- `orders.xlsx` - Sales order data
- `products.xlsx` - Product catalog and inventory
- `customers.xlsx` - Customer information
- `special_data.xlsx` - Data with special characters for testing

## 3. Start the REPL or Run Single Query

### Interactive REPL Mode
```bash
uv run python -m excel_processor --db sample_data
```

**💡 Pro Tip:** The REPL has intelligent auto-completion! Press `Tab` while typing to get:
- Table names after `FROM`
- Column names in `SELECT` and `WHERE` clauses  
- Actual data values after operators like `=`, `>`, etc.
- SQL keywords and commands

### Single Query Mode (Great for Scripting)
```bash
# Execute one query and exit
uv run python -m excel_processor --db sample_data --query "SELECT * FROM employees.staff WHERE department='Engineering'"

# Export to CSV
uv run python -m excel_processor --db sample_data --query "SELECT name, salary FROM employees.staff WHERE salary > 70000 > high_earners.csv"
```

## 4. Try These Commands

### Basic Commands
```sql
-- Show all available files and sheets (including temporary tables)
SHOW DB

-- Load all files into memory for faster queries
LOAD DB

-- Show memory usage
SHOW MEMORY

-- Show log files and query history
SHOW LOGS

-- Get help
HELP
```

### Simple Queries
```sql
-- View all employees
SELECT * FROM employees.staff

-- High earners only
SELECT name, salary FROM employees.staff WHERE salary > 70000

-- Sort by salary
SELECT name, department, salary FROM employees.staff ORDER BY salary DESC

-- Oracle-style NULL checks
SELECT * FROM test_nulls.staff_with_nulls WHERE name IS NULL
SELECT * FROM test_nulls.staff_with_nulls WHERE department IS NOT NULL
```

### Column Names with Spaces and Aliases
```sql
-- Use quotes for column names with spaces
SELECT "Full Name", "Annual Salary" FROM spaced_columns.employee_data

-- Column aliases with AS keyword
SELECT "Full Name" as employee_name, "Annual Salary" as salary 
FROM spaced_columns.employee_data

-- Both single and double quotes work
SELECT 'Job Title' as position, "Performance Rating" as rating
FROM spaced_columns.employee_data

-- Aliases in WHERE clauses and ORDER BY
SELECT "Full Name" as name, "Annual Salary" as salary
FROM spaced_columns.employee_data 
WHERE "Annual Salary" > 70000
ORDER BY "Performance Rating" DESC

-- Complex queries with multiple aliases and conditions
SELECT "Full Name" as name, "Job Title" as role, "Annual Salary" as salary
FROM spaced_columns.employee_data 
WHERE "Years of Experience" > 3 AND "Annual Salary" > 70000
ORDER BY "Performance Rating" DESC

-- Quoted file and sheet names (for files/sheets with spaces)
SELECT * FROM "Employee Data"."Staff Info"

-- Quoted table names with column aliases
SELECT "Employee Name" as name, "Department" as dept 
FROM "Employee Data"."Staff Info" 
WHERE "Salary" > 70000

-- Table aliases with quoted names
SELECT "Employee Name", "Salary" 
FROM "Employee Data"."Staff Info" AS emp 
WHERE "Salary" > 70000
```

### GROUP BY and Aggregation Functions
```sql
-- Count employees by department
SELECT department, COUNT(*) FROM employees.staff GROUP BY department

-- Department statistics
SELECT department, COUNT(*), AVG(salary), MIN(salary), MAX(salary) 
FROM employees.staff GROUP BY department

-- Filter grouped results with HAVING
SELECT department, COUNT(*) as emp_count, AVG(salary) as avg_salary
FROM employees.staff 
GROUP BY department 
HAVING COUNT(*) >= 3

-- Combine with WHERE clause
SELECT department, SUM(salary) as total_salary
FROM employees.staff 
WHERE salary > 65000
GROUP BY department
```

### Window Functions (Oracle-style Analytical Functions)
```sql
-- Row numbers within each department (ranked by salary)
SELECT name, department, salary, 
       ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC)
FROM employees.staff

-- Ranking functions
SELECT name, department, salary,
       RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rank,
       DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dense_rank
FROM employees.staff

-- LAG and LEAD functions for comparing with previous/next rows
SELECT name, salary,
       LAG(salary) OVER (ORDER BY salary) as prev_salary,
       LEAD(salary) OVER (ORDER BY salary) as next_salary
FROM employees.staff
ORDER BY salary

-- Window functions without partitioning
SELECT name, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC) as overall_rank
FROM employees.staff
```

### Temporary Tables (Oracle-style CREATE TABLE AS)
```sql
-- Create temporary table from query results
CREATE TABLE high_earners AS SELECT name, salary FROM employees.staff WHERE salary > 70000

-- Query the temporary table
SELECT * FROM high_earners

-- Use in complex queries with GROUP BY
CREATE TABLE dept_stats AS 
  SELECT department, COUNT(*) as count, AVG(salary) as avg_sal 
  FROM employees.staff GROUP BY department

SELECT * FROM dept_stats WHERE count > 3
```

### Joins
```sql
-- Employee sales data
SELECT e.name, e.department, o.customer, o.amount
FROM employees.staff e, orders.sales_data o
WHERE e.id = o.employee_id

-- Product inventory
SELECT p.name, p.price, i.quantity, i.warehouse
FROM products.catalog p, products.inventory i
WHERE p.product_id = i.product_id
```

### Export to CSV
```sql
-- Export high earners
SELECT name, salary FROM employees.staff WHERE salary > 70000 > high_earners.csv

-- Export sales summary
SELECT e.name, COUNT(o.order_id) as orders, SUM(o.amount) as total
FROM employees.staff e, orders.sales_data o
WHERE e.id = o.employee_id
GROUP BY e.name > sales_summary.csv
```

## 5. Test Programmatically

```bash
# Run the example script to see the components in action
uv run python example_usage.py
```

## 6. Try Jupyter Notebook

```bash
# Install notebook dependencies
uv sync --extra notebook

# Start Jupyter
uv run jupyter notebook

# Open Excel_DataFrame_Processor_Example.ipynb
```

Or use the programmatic interface:

```python
from excel_processor.notebook import ExcelProcessor

excel = ExcelProcessor('sample_data')
result = excel.query("SELECT * FROM employees.staff WHERE salary > 70000")
```

## Logging and Query History

All REPL interactions are automatically logged to the `.log` directory:

```bash
# View log files
SHOW LOGS

# Log files created:
# - repl_session_YYYYMMDD_HHMMSS.log (session activity)
# - query_history.log (SQL queries with timing)
```

Example log entries:
```
2025-10-12 22:57:31 - QUERY: SELECT * FROM employees.staff WHERE salary > 70000 | ROWS: 6 (0.041s)
2025-10-12 22:57:56 - CREATED TABLE: high_earners (6 rows × 2 columns)
```

## 💡 Tips

- Use tab completion for commands and table names
- Arrow keys navigate command history  
- File names can omit .xlsx extension
- Use quotes for files/sheets with spaces: `"Employee Data"."Staff Info"`
- Use quotes for column names with spaces: `"Full Name"`, `"Annual Salary"`
- Both single and double quotes work: `'Job Title'` or `"Job Title"`
- Combine quoted table and column names: `SELECT "Employee Name" FROM "Employee Data"."Staff Info"`

## Next Steps

- Check out the full [README.md](README.md) for comprehensive documentation
- Explore the `Excel_DataFrame_Processor_Example.ipynb` notebook for advanced examples
- Explore the `sample_data/` directory to understand the data structure
- Try more complex queries with multiple joins and aggregations
- Experiment with different Excel files and sheet structures
- Create visualizations and analysis in Jupyter notebooks
- Review query history in the `.log` directory for performance analysis

## Need Help?

- Use `HELP` command in the REPL for syntax reference
- Check error messages for specific guidance
- Review the examples in the README for more query patterns

Happy querying! 🚀