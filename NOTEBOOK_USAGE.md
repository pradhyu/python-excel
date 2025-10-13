# Jupyter Notebook Usage Guide

The Excel DataFrame Processor provides full Jupyter notebook integration with both programmatic API and magic commands for convenient data analysis workflows.

## Installation

```bash
# Install with notebook dependencies
uv sync --extra notebook

# Start Jupyter
uv run jupyter notebook
# or
uv run jupyter lab
```

## Method 1: Programmatic API

### Basic Usage

```python
from excel_processor.notebook import ExcelProcessor

# Initialize with your Excel files directory
excel = ExcelProcessor(db_directory='sample_data')

# Show available files and sheets
excel.show_db()

# Execute SQL queries
employees = excel.query("SELECT * FROM employees.staff")
high_earners = excel.query("SELECT name, salary FROM employees.staff WHERE salary > 70000")

# Export results
excel.query("SELECT * FROM employees.staff WHERE department = 'Engineering' > engineers.csv")
```

### Advanced Features

```python
# Load all files for faster querying
excel.load_db()

# Get file information
file_info = excel.get_file_info('employees.xlsx')
sheet_info = excel.get_sheet_info('employees.xlsx', 'staff')

# Monitor memory usage
memory_info = excel.get_memory_usage()
print(f"Memory usage: {memory_info['total_mb']:.2f} MB")

# Query without displaying results (for further processing)
data = excel.query("SELECT * FROM orders.sales_data", display_result=False)
```

## Method 2: Magic Commands

### Load Magic Extension

```python
%load_ext excel_processor.notebook
```

### Available Magic Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `%excel_init` | Initialize processor | `%excel_init --db sample_data` |
| `%excel_show_db` | Show available files | `%excel_show_db` |
| `%excel_load_db` | Load all files | `%excel_load_db` |
| `%excel_memory` | Show memory usage | `%excel_memory` |
| `%%excel_sql` | Execute SQL query | See examples below |

### Magic Command Examples

```python
# Initialize
%excel_init --db sample_data --memory-limit 512

# Show database contents
%excel_show_db

# Execute SQL queries
%%excel_sql
SELECT name, department, salary 
FROM employees.staff 
WHERE salary > 70000 
ORDER BY salary DESC
```

```python
# Complex query with magic
%%excel_sql
SELECT * FROM products.catalog 
WHERE price BETWEEN 100 AND 500 
ORDER BY price ASC
```

## Data Analysis Workflows

### Combining with Pandas

```python
# Get data using Excel processor
employees = excel.query("SELECT * FROM employees.staff", display_result=False)
orders = excel.query("SELECT * FROM orders.sales_data", display_result=False)

# Use pandas for advanced analysis
import pandas as pd

# Employee performance analysis
employee_sales = orders.groupby('employee_id').agg({
    'order_id': 'count',
    'amount': ['sum', 'mean']
}).round(2)

# Merge with employee data
performance = employees.merge(employee_sales, left_on='id', right_on='employee_id')
```

### Visualization Integration

```python
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Get data
employees = excel.query("SELECT * FROM employees.staff", display_result=False)

# Matplotlib/Seaborn
plt.figure(figsize=(10, 6))
sns.boxplot(data=employees, x='department', y='salary')
plt.title('Salary Distribution by Department')
plt.show()

# Plotly for interactive charts
fig = px.scatter(employees, x='age', y='salary', color='department', 
                 hover_data=['name'], title='Employee Salary vs Age')
fig.show()
```

### Export and Reporting

```python
# Export analysis results
analysis_results = excel.query("""
    SELECT department, COUNT(*) as employee_count, AVG(salary) as avg_salary
    FROM employees.staff 
    GROUP BY department
""", display_result=False)

# Save to CSV
analysis_results.to_csv('department_analysis.csv', index=False)

# Create formatted report
report = f"""
# Employee Analysis Report

## Summary
- Total Employees: {len(employees)}
- Departments: {employees['department'].nunique()}
- Average Salary: ${employees['salary'].mean():,.2f}

## Department Breakdown
{analysis_results.to_string(index=False)}
"""

with open('employee_report.md', 'w') as f:
    f.write(report)
```

## Example Notebook

Check out `Excel_DataFrame_Processor_Example.ipynb` for a comprehensive example that demonstrates:

- 📊 Loading and querying Excel data
- 📈 Data visualization with multiple libraries
- 🔗 Combining data from multiple Excel files
- 📤 Exporting results and creating reports
- 💾 Memory management and optimization
- 🎨 Interactive dashboards with Plotly

## Tips and Best Practices

### Performance Optimization

```python
# Load all files once for faster queries
excel.load_db()

# Monitor memory usage
%excel_memory

# Use specific column selection instead of SELECT *
result = excel.query("SELECT name, salary FROM employees.staff WHERE salary > 70000")
```

### Error Handling

```python
try:
    result = excel.query("SELECT * FROM nonexistent.sheet")
except Exception as e:
    print(f"Query failed: {e}")
```

### Working with Large Datasets

```python
# Use ROWNUM to limit results
sample = excel.query("SELECT * FROM large_file.sheet WHERE ROWNUM <= 1000")

# Export large results directly to CSV
excel.query("SELECT * FROM large_file.sheet > large_export.csv")
```

## Integration with Data Science Workflows

### Machine Learning Pipeline

```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# Get training data
data = excel.query("SELECT age, department, salary FROM employees.staff", display_result=False)

# Prepare features
data_encoded = pd.get_dummies(data, columns=['department'])
X = data_encoded.drop('salary', axis=1)
y = data_encoded['salary']

# Train model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = RandomForestRegressor()
model.fit(X_train, y_train)
```

### Time Series Analysis

```python
# Get time series data
orders = excel.query("SELECT order_date, amount FROM orders.sales_data ORDER BY order_date", display_result=False)
orders['order_date'] = pd.to_datetime(orders['order_date'])

# Resample to monthly
monthly_sales = orders.set_index('order_date').resample('M')['amount'].sum()

# Plot trend
monthly_sales.plot(title='Monthly Sales Trend')
plt.show()
```

## Troubleshooting

### Common Issues

1. **Magic commands not working**: Make sure to run `%load_ext excel_processor.notebook`
2. **File not found**: Check that your database directory path is correct
3. **Memory issues**: Use `%excel_memory` to monitor usage and clear cache if needed
4. **Query errors**: Verify file and sheet names with `%excel_show_db`

### Getting Help

```python
# Show available files and sheets
excel.show_db()

# Check memory usage
excel.get_memory_usage()

# Get file information
excel.get_file_info('filename.xlsx')
```

Happy analyzing! 🚀📊