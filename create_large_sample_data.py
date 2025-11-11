#!/usr/bin/env python3
"""
Create large Excel files for performance testing
Generates realistic datasets with 100K+ rows
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

def generate_large_employee_data(num_rows=100000):
    """Generate large employee dataset"""
    print(f"🔄 Generating {num_rows:,} employee records...")
    
    # Generate realistic data
    np.random.seed(42)
    random.seed(42)
    
    # Names
    first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
                   'William', 'Barbara', 'David', 'Elizabeth', 'Richard', 'Susan', 'Joseph', 'Jessica',
                   'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                  'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
                  'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White']
    
    departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 
                   'IT', 'Customer Service', 'Legal', 'R&D']
    
    locations = ['New York', 'San Francisco', 'Chicago', 'Austin', 'Seattle', 
                 'Boston', 'Denver', 'Atlanta', 'Los Angeles', 'Miami']
    
    job_titles = ['Junior', 'Mid-Level', 'Senior', 'Lead', 'Principal', 'Manager', 'Director']
    
    # Generate data
    data = {
        'employee_id': range(1, num_rows + 1),
        'first_name': [random.choice(first_names) for _ in range(num_rows)],
        'last_name': [random.choice(last_names) for _ in range(num_rows)],
        'email': [f'employee{i}@company.com' for i in range(1, num_rows + 1)],
        'department': [random.choice(departments) for _ in range(num_rows)],
        'job_title': [random.choice(job_titles) for _ in range(num_rows)],
        'location': [random.choice(locations) for _ in range(num_rows)],
        'salary': np.random.normal(75000, 25000, num_rows).clip(35000, 250000).astype(int),
        'age': np.random.normal(38, 10, num_rows).clip(22, 65).astype(int),
        'years_experience': np.random.normal(8, 5, num_rows).clip(0, 40).astype(int),
        'performance_rating': np.random.choice([1, 2, 3, 4, 5], num_rows, p=[0.05, 0.15, 0.40, 0.30, 0.10]),
        'hire_date': [datetime(2010, 1, 1) + timedelta(days=random.randint(0, 5000)) for _ in range(num_rows)],
        'is_remote': np.random.choice([True, False], num_rows, p=[0.3, 0.7]),
        'bonus_eligible': np.random.choice([True, False], num_rows, p=[0.6, 0.4]),
    }
    
    df = pd.DataFrame(data)
    
    # Add computed columns
    df['full_name'] = df['first_name'] + ' ' + df['last_name']
    df['annual_compensation'] = df['salary'] + (df['salary'] * 0.15 * df['bonus_eligible'])
    
    print(f"✅ Generated {len(df):,} employee records")
    print(f"📊 Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    return df

def generate_large_sales_data(num_rows=200000):
    """Generate large sales transaction dataset"""
    print(f"🔄 Generating {num_rows:,} sales transactions...")
    
    np.random.seed(42)
    random.seed(42)
    
    products = [f'Product_{chr(65+i)}' for i in range(50)]  # Product_A to Product_AX
    regions = ['North', 'South', 'East', 'West', 'Central']
    sales_reps = [f'Rep_{i:04d}' for i in range(1, 501)]
    customers = [f'Customer_{i:05d}' for i in range(1, 10001)]
    
    data = {
        'transaction_id': range(1, num_rows + 1),
        'transaction_date': [datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1460)) for _ in range(num_rows)],
        'product': [random.choice(products) for _ in range(num_rows)],
        'customer_id': [random.choice(customers) for _ in range(num_rows)],
        'sales_rep': [random.choice(sales_reps) for _ in range(num_rows)],
        'region': [random.choice(regions) for _ in range(num_rows)],
        'quantity': np.random.poisson(5, num_rows) + 1,
        'unit_price': np.random.uniform(10, 1000, num_rows).round(2),
        'discount_percent': np.random.choice([0, 5, 10, 15, 20], num_rows, p=[0.5, 0.2, 0.15, 0.10, 0.05]),
        'shipping_cost': np.random.uniform(5, 50, num_rows).round(2),
        'tax_rate': np.random.choice([0.05, 0.07, 0.08, 0.10], num_rows),
    }
    
    df = pd.DataFrame(data)
    
    # Computed columns
    df['subtotal'] = (df['quantity'] * df['unit_price']).round(2)
    df['discount_amount'] = (df['subtotal'] * df['discount_percent'] / 100).round(2)
    df['tax_amount'] = ((df['subtotal'] - df['discount_amount']) * df['tax_rate']).round(2)
    df['total_amount'] = (df['subtotal'] - df['discount_amount'] + df['tax_amount'] + df['shipping_cost']).round(2)
    
    print(f"✅ Generated {len(df):,} sales transactions")
    print(f"📊 Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    return df

def generate_time_series_data(num_rows=500000):
    """Generate large time series dataset"""
    print(f"🔄 Generating {num_rows:,} time series records...")
    
    np.random.seed(42)
    
    # Generate timestamps
    start_date = datetime(2020, 1, 1)
    timestamps = [start_date + timedelta(minutes=i) for i in range(num_rows)]
    
    # Generate sensor data
    data = {
        'timestamp': timestamps,
        'sensor_id': np.random.randint(1, 101, num_rows),
        'temperature': np.random.normal(72, 5, num_rows).round(2),
        'humidity': np.random.normal(45, 10, num_rows).clip(20, 80).round(2),
        'pressure': np.random.normal(1013, 5, num_rows).round(2),
        'cpu_usage': np.random.beta(2, 5, num_rows) * 100,
        'memory_usage': np.random.beta(3, 4, num_rows) * 100,
        'disk_io': np.random.exponential(50, num_rows),
        'network_traffic': np.random.exponential(100, num_rows),
        'error_count': np.random.poisson(0.5, num_rows),
        'status': np.random.choice(['OK', 'WARNING', 'ERROR'], num_rows, p=[0.85, 0.12, 0.03]),
    }
    
    df = pd.DataFrame(data)
    
    print(f"✅ Generated {len(df):,} time series records")
    print(f"📊 Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    return df

def main():
    """Generate all large sample files"""
    print("=" * 60)
    print("🚀 Creating Large Sample Data for Performance Testing")
    print("=" * 60)
    print()
    
    # Create sample_data directory
    sample_dir = Path('sample_data')
    sample_dir.mkdir(exist_ok=True)
    
    # Generate datasets
    print("📊 Dataset 1: Large Employee Database")
    print("-" * 60)
    employees_df = generate_large_employee_data(100000)
    
    print("\n📊 Dataset 2: Large Sales Transactions")
    print("-" * 60)
    sales_df = generate_large_sales_data(200000)
    
    print("\n📊 Dataset 3: Time Series Sensor Data")
    print("-" * 60)
    timeseries_df = generate_time_series_data(500000)
    
    # Save to Excel files
    print("\n💾 Saving to Excel files...")
    print("-" * 60)
    
    # Large employees file
    print("📝 Writing large_employees.xlsx...")
    with pd.ExcelWriter(sample_dir / 'large_employees.xlsx', engine='openpyxl') as writer:
        employees_df.to_excel(writer, sheet_name='employees', index=False)
        
        # Add summary sheet
        summary = employees_df.groupby('department').agg({
            'employee_id': 'count',
            'salary': ['mean', 'min', 'max'],
            'age': 'mean',
            'performance_rating': 'mean'
        }).round(2)
        summary.to_excel(writer, sheet_name='department_summary')
    
    print(f"✅ Saved large_employees.xlsx ({(sample_dir / 'large_employees.xlsx').stat().st_size / 1024**2:.2f} MB)")
    
    # Large sales file
    print("📝 Writing large_sales.xlsx...")
    with pd.ExcelWriter(sample_dir / 'large_sales.xlsx', engine='openpyxl') as writer:
        sales_df.to_excel(writer, sheet_name='transactions', index=False)
        
        # Add monthly summary
        sales_df['month'] = pd.to_datetime(sales_df['transaction_date']).dt.to_period('M')
        monthly = sales_df.groupby('month').agg({
            'transaction_id': 'count',
            'total_amount': 'sum',
            'quantity': 'sum'
        }).round(2)
        monthly.to_excel(writer, sheet_name='monthly_summary')
    
    print(f"✅ Saved large_sales.xlsx ({(sample_dir / 'large_sales.xlsx').stat().st_size / 1024**2:.2f} MB)")
    
    # Time series as CSV (more efficient for large data)
    print("📝 Writing large_timeseries.csv...")
    timeseries_df.to_csv(sample_dir / 'large_timeseries.csv', index=False)
    print(f"✅ Saved large_timeseries.csv ({(sample_dir / 'large_timeseries.csv').stat().st_size / 1024**2:.2f} MB)")
    
    # Create performance test queries file
    print("\n📝 Creating performance test queries...")
    test_queries = """# Performance Test Queries for Large Datasets

## Basic Queries
SHOW DB
SELECT COUNT(*) FROM large_employees.employees
SELECT COUNT(*) FROM large_sales.transactions
SELECT COUNT(*) FROM large_timeseries.default

## Filtering Queries
SELECT * FROM large_employees.employees WHERE salary > 100000 LIMIT 10
SELECT * FROM large_sales.transactions WHERE total_amount > 1000 LIMIT 10
SELECT * FROM large_timeseries.default WHERE status = 'ERROR' LIMIT 10

## Aggregation Queries
SELECT department, COUNT(*) as emp_count, AVG(salary) as avg_salary 
FROM large_employees.employees 
GROUP BY department 
ORDER BY avg_salary DESC

SELECT region, SUM(total_amount) as total_sales, COUNT(*) as transaction_count
FROM large_sales.transactions 
GROUP BY region 
ORDER BY total_sales DESC

SELECT sensor_id, AVG(temperature) as avg_temp, AVG(cpu_usage) as avg_cpu
FROM large_timeseries.default 
GROUP BY sensor_id 
LIMIT 20

## Complex Queries
SELECT department, location, COUNT(*) as count, AVG(salary) as avg_sal
FROM large_employees.employees 
WHERE performance_rating >= 4 
GROUP BY department, location 
HAVING COUNT(*) > 10
ORDER BY avg_sal DESC

SELECT product, region, SUM(total_amount) as revenue, COUNT(*) as sales
FROM large_sales.transactions 
WHERE transaction_date >= '2023-01-01'
GROUP BY product, region 
ORDER BY revenue DESC 
LIMIT 20

## Export Queries
SELECT * FROM large_employees.employees WHERE salary > 150000 > high_earners.csv
SELECT product, SUM(total_amount) as revenue FROM large_sales.transactions GROUP BY product > product_revenue.csv
"""
    
    with open(sample_dir / 'performance_test_queries.txt', 'w') as f:
        f.write(test_queries)
    
    print("✅ Saved performance_test_queries.txt")
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ Large Sample Data Generation Complete!")
    print("=" * 60)
    print(f"\n📁 Files created in {sample_dir}:")
    print(f"   📊 large_employees.xlsx    - {len(employees_df):,} rows")
    print(f"   📊 large_sales.xlsx        - {len(sales_df):,} rows")
    print(f"   📄 large_timeseries.csv    - {len(timeseries_df):,} rows")
    print(f"   📝 performance_test_queries.txt")
    
    total_size = sum((sample_dir / f).stat().st_size for f in ['large_employees.xlsx', 'large_sales.xlsx', 'large_timeseries.csv'])
    print(f"\n💾 Total size: {total_size / 1024**2:.2f} MB")
    print(f"📊 Total records: {len(employees_df) + len(sales_df) + len(timeseries_df):,}")
    
    print("\n🚀 Ready for performance testing!")
    print("   Run: ./docker-run.sh run --db-dir ./sample_data")

if __name__ == '__main__':
    main()
