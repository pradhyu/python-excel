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

## 3. Start the REPL

```bash
uv run python -m excel_processor --db sample_data
```

## 4. Try These Commands

### Basic Commands
```sql
-- Show all available files and sheets
SHOW DB

-- Load all files into memory for faster queries
LOAD DB

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

## Next Steps

- Check out the full [README.md](README.md) for comprehensive documentation
- Explore the `Excel_DataFrame_Processor_Example.ipynb` notebook for advanced examples
- Explore the `sample_data/` directory to understand the data structure
- Try more complex queries with multiple joins and aggregations
- Experiment with different Excel files and sheet structures
- Create visualizations and analysis in Jupyter notebooks

## Need Help?

- Use `HELP` command in the REPL for syntax reference
- Check error messages for specific guidance
- Review the examples in the README for more query patterns

Happy querying! 🚀