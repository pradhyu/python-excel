# Excel DataFrame Processor

A powerful Python application that provides a REPL (Read-Eval-Print Loop) interface for executing Oracle-like SQL queries on Excel and CSV files. Load spreadsheets and CSV data into DataFrames and query them using familiar SQL syntax with support for joins, filtering, sorting, and CSV export.

## Features

### Core SQL Capabilities
- 🔍 **Advanced SQL Syntax**: Oracle-like SQL with SELECT, WHERE, JOIN, GROUP BY, HAVING, ORDER BY
- 📊 **File Format Support**: Works with Excel (.xlsx, .xls, .xlsm, .xlsb) and CSV files
- 🔗 **Cross-file Joins**: Join data from different Excel files and sheets
- 🪟 **Window Functions**: ROW_NUMBER(), RANK(), LAG(), LEAD() with OVER clause
- 📈 **Aggregations**: COUNT, SUM, AVG, MIN, MAX with GROUP BY and HAVING
- 🏷️ **Column Aliases**: Support for AS keyword and column renaming

### Advanced Features
- 📝 **Quoted Identifiers**: Handle files, sheets, and columns with spaces using quotes
- 💾 **Temporary Tables**: CREATE TABLE AS SELECT for intermediate results
- 🎯 **Smart Parsing**: Automatic detection of quoted names and proper escaping
- 🔄 **CSV Integration**: Query CSV files using filename.default notation

### User Experience
- 🎨 **Colorful Output**: Beautiful ASCII tables with rich formatting
- 📤 **CSV Export**: Export query results using > filename.csv syntax
- 🗂️ **Database Directory**: Organize files in a database directory structure
- 🔧 **Interactive REPL**: Command history, auto-completion, and intelligent error handling

### System Management
- ⚡ **Memory Management**: Configurable limits, usage tracking, and cache control
- 📊 **Performance Monitoring**: Query timing, memory usage, and optimization
- 📝 **Comprehensive Logging**: Session logs, query history, and error tracking
- 🧹 **Cache Management**: CLEAR CACHE command and automatic cleanup

### Integration & APIs
- 📓 **Jupyter Integration**: Full notebook support with magic commands and rich HTML display
- 🐍 **Python API**: Programmatic interface for scripts and applications
- 🎛️ **Magic Commands**: %excel_init, %%excel_sql for notebook workflows
- 📋 **Rich Display**: Automatic table formatting in notebooks and terminals

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install the Excel DataFrame Processor

```bash
# Clone the repository
git clone <repository-url>
cd excel-dataframe-processor

# Install dependencies
uv sync

# Install development dependencies (optional)
uv sync --extra dev

# Install notebook dependencies for Jupyter support (optional)
uv sync --extra notebook
```

## Quick Start

### 1. Create Sample Excel Files

First, let's create some sample Excel files to work with:

```python
# Run this script to create sample data
uv run python -c "
import pandas as pd
from pathlib import Path

# Create sample data directory
Path('sample_data').mkdir(exist_ok=True)

# Create employees.xlsx
employees = pd.DataFrame({
    'id': [1, 2, 3, 4, 5],
    'name': ['Alice Johnson', 'Bob Smith', 'Charlie Brown', 'Diana Prince', 'Eve Wilson'],
    'age': [28, 35, 42, 31, 29],
    'department': ['Engineering', 'Sales', 'Engineering', 'Marketing', 'Sales'],
    'salary': [75000, 65000, 85000, 70000, 68000],
    'hire_date': pd.to_datetime(['2020-01-15', '2019-03-22', '2018-07-10', '2021-02-28', '2020-11-05'])
})

with pd.ExcelWriter('sample_data/employees.xlsx', engine='openpyxl') as writer:
    employees.to_excel(writer, sheet_name='staff', index=False)
    # Add a summary sheet
    dept_summary = employees.groupby('department').agg({
        'salary': ['mean', 'count'],
        'age': 'mean'
    }).round(2)
    dept_summary.to_excel(writer, sheet_name='department_summary')

# Create orders.xlsx
orders = pd.DataFrame({
    'order_id': [101, 102, 103, 104, 105, 106],
    'employee_id': [1, 2, 1, 3, 4, 2],
    'customer': ['Acme Corp', 'Beta Inc', 'Gamma LLC', 'Delta Co', 'Epsilon Ltd', 'Zeta Corp'],
    'amount': [15000, 8500, 22000, 12000, 18500, 9500],
    'order_date': pd.to_datetime(['2024-01-10', '2024-01-15', '2024-01-20', '2024-01-25', '2024-02-01', '2024-02-05']),
    'status': ['Completed', 'Pending', 'Completed', 'Shipped', 'Completed', 'Pending']
})

orders.to_excel('sample_data/orders.xlsx', sheet_name='sales_data', index=False)

# Create products.xlsx with multiple sheets
products = pd.DataFrame({
    'product_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
    'name': ['Laptop Pro', 'Desktop Elite', 'Tablet Max', 'Phone Ultra', 'Watch Smart'],
    'category': ['Computers', 'Computers', 'Tablets', 'Phones', 'Wearables'],
    'price': [1299.99, 899.99, 599.99, 799.99, 299.99],
    'in_stock': [45, 23, 67, 89, 156]
})

inventory = pd.DataFrame({
    'product_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
    'warehouse': ['West', 'East', 'West', 'Central', 'East'],
    'quantity': [25, 15, 40, 60, 80],
    'last_updated': pd.to_datetime(['2024-02-01', '2024-02-02', '2024-02-01', '2024-02-03', '2024-02-02'])
})

with pd.ExcelWriter('sample_data/products.xlsx', engine='openpyxl') as writer:
    products.to_excel(writer, sheet_name='catalog', index=False)
    inventory.to_excel(writer, sheet_name='inventory', index=False)

print('Sample Excel files created in sample_data/ directory!')
"
```

### 2. Start the REPL

```bash
# Start the Excel processor with your database directory
uv run python -m excel_processor --db sample_data
```

### 3. Basic Commands

Once in the REPL, you can use these commands:

```sql
-- Show all Excel files and sheets in the database
SHOW DB

-- Load all Excel files into memory for faster queries
LOAD DB

-- Get help with available commands and syntax
HELP

-- Exit the application
EXIT
```

## SQL Query Examples

### Basic SELECT Queries

```sql
-- Select all employees
SELECT * FROM employees.xlsx.staff

-- Select specific columns
SELECT name, department, salary FROM employees.xlsx.staff

-- Select with aliases (you can omit .xlsx extension)
SELECT name, salary FROM employees.staff AS e
```

### Filtering with WHERE

```sql
-- Filter by department
SELECT name, salary FROM employees.staff WHERE department = 'Engineering'

-- Filter by salary range
SELECT name, age, salary FROM employees.staff WHERE salary > 70000

-- Multiple conditions
SELECT name, department FROM employees.staff 
WHERE age > 30 AND department = 'Sales'

-- String matching
SELECT name FROM employees.staff WHERE name LIKE '%Johnson%'
```

### Sorting with ORDER BY

```sql
-- Sort by salary (descending)
SELECT name, salary FROM employees.staff ORDER BY salary DESC

-- Multiple column sorting
SELECT name, age, department FROM employees.staff 
ORDER BY department ASC, age DESC

-- Limit results with ROWNUM
SELECT name, salary FROM employees.staff 
WHERE ROWNUM <= 3 ORDER BY salary DESC
```

### Joins Between Files

```sql
-- Join employees with orders
SELECT e.name, e.department, o.customer, o.amount
FROM employees.staff e, orders.sales_data o
WHERE e.id = o.employee_id

-- Explicit JOIN syntax
SELECT e.name, o.customer, o.amount, o.status
FROM employees.staff e
INNER JOIN orders.sales_data o ON e.id = o.employee_id
WHERE o.amount > 10000

-- Left join to include all employees
SELECT e.name, e.department, o.customer, o.amount
FROM employees.staff e
LEFT JOIN orders.sales_data o ON e.id = o.employee_id
ORDER BY e.name
```

### Aggregate Functions

```sql
-- Count employees by department
SELECT department, COUNT(*) FROM employees.staff GROUP BY department

-- Average salary by department
SELECT department, AVG(salary) FROM employees.staff GROUP BY department

-- Total sales by employee
SELECT e.name, SUM(o.amount) as total_sales
FROM employees.staff e, orders.sales_data o
WHERE e.id = o.employee_id
GROUP BY e.name
ORDER BY total_sales DESC
```

### Working with Multiple Sheets

```sql
-- Query different sheets in the same file
SELECT * FROM products.catalog

SELECT * FROM products.inventory

-- Join sheets within the same file
SELECT p.name, p.price, i.quantity, i.warehouse
FROM products.catalog p, products.inventory i
WHERE p.product_id = i.product_id
```

### CSV Export

```sql
-- Export query results to CSV
SELECT name, salary FROM employees.staff WHERE salary > 70000 > high_earners.csv

-- Export join results
SELECT e.name, o.customer, o.amount
FROM employees.staff e, orders.sales_data o
WHERE e.id = o.employee_id > employee_sales.csv

-- Export with complex query
SELECT 
    e.name,
    e.department,
    COUNT(o.order_id) as order_count,
    SUM(o.amount) as total_sales
FROM employees.staff e
LEFT JOIN orders.sales_data o ON e.id = o.employee_id
GROUP BY e.name, e.department
ORDER BY total_sales DESC > sales_summary.csv
```

## Jupyter Notebook Usage

### Programmatic Interface

```python
from excel_processor.notebook import ExcelProcessor

# Initialize the processor
excel = ExcelProcessor(db_directory='sample_data')

# Show available files
excel.show_db()

# Execute SQL queries
result = excel.query("SELECT * FROM employees.staff WHERE salary > 70000")

# Export results
excel.query("SELECT name, salary FROM employees.staff > output.csv")
```

### Magic Commands

```python
# Load the magic commands
%load_ext excel_processor.notebook

# Initialize
%excel_init --db sample_data

# Show database
%excel_show_db

# Execute SQL queries
%%excel_sql
SELECT name, department, salary 
FROM employees.staff 
WHERE salary > 70000 
ORDER BY salary DESC
```

### Example Notebook

Check out the comprehensive example notebook: `Excel_DataFrame_Processor_Example.ipynb`

This notebook demonstrates:
- 📊 Data loading and querying
- 📈 Data visualization with matplotlib, seaborn, and plotly
- 🔗 Combining data from multiple Excel files
- 📤 Exporting results and analysis
- 💾 Memory management

## Advanced Features

### Quoted Identifiers and Aliases

```sql
-- Files and sheets with spaces (use quotes)
SELECT * FROM "Employee Data"."Staff Info"

-- Column names with spaces
SELECT "Full Name", "Annual Salary" FROM "Employee Data"."Staff Info"

-- Column aliases with AS keyword
SELECT "Full Name" AS employee_name, "Annual Salary" AS salary 
FROM "Employee Data"."Staff Info"

-- Mixed quoted and unquoted
SELECT name, "Job Title" AS position FROM employees.staff
```

### CSV File Support

```sql
-- Query CSV files (use .default as sheet name)
SELECT * FROM sales_data.default

-- CSV files with spaces in filename
SELECT "Customer Name", Amount FROM "Sales Report.csv".default

-- All SQL features work with CSV files
SELECT Category, COUNT(*), AVG(Price) 
FROM products.default 
GROUP BY Category
```

### Window Functions

```sql
-- Row numbering
SELECT name, salary, 
       ROW_NUMBER() OVER (ORDER BY salary DESC) AS rank
FROM employees.staff

-- Partitioned ranking
SELECT name, department, salary,
       ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees.staff

-- LAG and LEAD functions
SELECT name, salary,
       LAG(salary) OVER (ORDER BY salary) AS prev_salary
FROM employees.staff
```

### Temporary Tables

```sql
-- Create temporary table from query results
CREATE TABLE high_earners AS 
SELECT name, department, salary 
FROM employees.staff 
WHERE salary > 75000

-- Query the temporary table
SELECT department, COUNT(*) 
FROM high_earners 
GROUP BY department

-- Temporary tables persist for the session
SELECT * FROM high_earners WHERE department = 'Engineering'
```

### Advanced Aggregations

```sql
-- GROUP BY with HAVING
SELECT department, COUNT(*) AS emp_count, AVG(salary) AS avg_salary
FROM employees.staff 
GROUP BY department 
HAVING COUNT(*) > 2

-- Multiple aggregations with aliases
SELECT department,
       COUNT(*) AS total_employees,
       AVG(salary) AS average_salary,
       MIN(salary) AS min_salary,
       MAX(salary) AS max_salary
FROM employees.staff 
GROUP BY department
```

### File and Sheet References

```sql
-- Different ways to reference Excel files and sheets
SELECT * FROM employees.xlsx.staff        -- Full filename with extension
SELECT * FROM employees.staff             -- Filename without extension
SELECT * FROM "file with spaces.xlsx".sheet1  -- Files with spaces (use quotes)
SELECT * FROM data.employees AS e         -- With table alias
```

### Complex WHERE Conditions

```sql
-- Date filtering (if your Excel has date columns)
SELECT * FROM orders.sales_data 
WHERE order_date >= '2024-01-01' AND order_date < '2024-02-01'

-- IN clause
SELECT * FROM employees.staff 
WHERE department IN ('Engineering', 'Sales')

-- BETWEEN clause
SELECT * FROM employees.staff 
WHERE age BETWEEN 25 AND 35

-- NULL handling
SELECT * FROM employees.staff 
WHERE department IS NOT NULL
```

### Memory Management

```sql
-- Check memory usage
SHOW MEMORY

-- Clear cache for specific file
CLEAR CACHE employees.xlsx

-- Reload modified files
REFRESH CACHE
```

## Command Reference

### REPL Commands

| Command | Description |
|---------|-------------|
| `SHOW DB` | List all Excel/CSV files and sheets in database directory |
| `LOAD DB` | Load all files into memory |
| `SHOW MEMORY` | Display current memory usage by file |
| `SHOW LOGS` | Display log file information and locations |
| `CLEAR CACHE [file]` | Clear DataFrame cache (all or specific file) |
| `HELP` | Show help and example queries |
| `EXIT` | Exit the application |

### SQL Syntax

| Feature | Syntax | Example |
|---------|--------|---------|
| Basic SELECT | `SELECT columns FROM file.sheet` | `SELECT * FROM data.employees` |
| Quoted Names | `"Name with Spaces"` | `SELECT "Full Name" FROM "Employee Data"."Staff Info"` |
| Column Aliases | `column AS alias` | `SELECT "Full Name" AS name` |
| CSV Files | `filename.default` | `SELECT * FROM sales_data.default` |
| WHERE clause | `WHERE condition` | `WHERE "Annual Salary" > 70000` |
| ORDER BY | `ORDER BY column [ASC\|DESC]` | `ORDER BY "Performance Rating" DESC` |
| GROUP BY | `GROUP BY columns HAVING condition` | `GROUP BY department HAVING COUNT(*) > 5` |
| Window Functions | `FUNCTION() OVER (...)` | `ROW_NUMBER() OVER (ORDER BY salary DESC)` |
| Temporary Tables | `CREATE TABLE name AS SELECT...` | `CREATE TABLE temp AS SELECT * FROM data` |
| LIMIT | `WHERE ROWNUM <= n` | `WHERE ROWNUM <= 10` |
| JOIN | `FROM table1, table2 WHERE condition` | `FROM emp e, orders o WHERE e.id = o.emp_id` |
| Explicit JOIN | `FROM table1 JOIN table2 ON condition` | `FROM emp e JOIN orders o ON e.id = o.emp_id` |
| CSV Export | `query > filename.csv` | `SELECT * FROM data > output.csv` |

### Supported Operators

| Type | Operators |
|------|-----------|
| Comparison | `=`, `!=`, `<>`, `<`, `>`, `<=`, `>=` |
| Logical | `AND`, `OR`, `NOT` |
| Pattern | `LIKE` |
| Set | `IN`, `NOT IN` |
| Range | `BETWEEN`, `NOT BETWEEN` |
| NULL | `IS NULL`, `IS NOT NULL` |

### Aggregate Functions

- `COUNT(*)` - Count rows
- `COUNT(column)` - Count non-null values
- `SUM(column)` - Sum values
- `AVG(column)` - Average values
- `MIN(column)` - Minimum value
- `MAX(column)` - Maximum value
- `STDDEV(column)` - Standard deviation
- `VARIANCE(column)` - Variance

### Window Functions

- `ROW_NUMBER() OVER (...)` - Sequential row numbering
- `RANK() OVER (...)` - Ranking with gaps
- `DENSE_RANK() OVER (...)` - Ranking without gaps
- `LAG(column) OVER (...)` - Previous row value
- `LEAD(column) OVER (...)` - Next row value

## File Structure

```
excel-dataframe-processor/
├── excel_processor/           # Main application code
│   ├── __init__.py
│   ├── main.py               # CLI entry point
│   ├── repl.py               # REPL interface
│   ├── sql_parser.py         # SQL parser
│   ├── query_executor.py     # Query execution engine
│   ├── dataframe_manager.py  # DataFrame management
│   ├── excel_loader.py       # Excel file loading
│   ├── result_formatter.py   # Output formatting
│   ├── csv_exporter.py       # CSV export functionality
│   ├── models.py             # Data models
│   ├── exceptions.py         # Custom exceptions
│   └── sql_ast.py            # SQL AST nodes
├── tests/                    # Unit tests
├── sample_data/              # Sample Excel files
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=excel_processor

# Run specific test file
uv run pytest tests/test_sql_parser.py -v
```

### Code Formatting

```bash
# Format code with black
uv run black excel_processor tests

# Lint with ruff
uv run ruff check excel_processor tests
```

## Troubleshooting

### Common Issues

1. **File not found**: Ensure Excel files are in the specified database directory
2. **Sheet not found**: Use `SHOW DB` to see available sheets
3. **Memory issues**: Use `SHOW MEMORY` to monitor usage, clear cache if needed
4. **SQL syntax errors**: Check the help with `HELP` command for correct syntax

### Performance Tips

1. Use `LOAD DB` to preload files for faster queries
2. Filter early with WHERE clauses to reduce data processing
3. Use specific column selection instead of `SELECT *` for large files
4. Monitor memory usage with large Excel files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [pandas](https://pandas.pydata.org/) for DataFrame operations
- Uses [openpyxl](https://openpyxl.readthedocs.io/) for Excel file reading
- Powered by [rich](https://rich.readthedocs.io/) for beautiful terminal output
- Interactive features with [prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/)