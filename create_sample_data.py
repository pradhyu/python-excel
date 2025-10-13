#!/usr/bin/env python3
"""
Script to create sample Excel files for the Excel DataFrame Processor.
Run this script to generate sample data for testing and demonstration.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Create sample Excel files with realistic business data."""
    
    # Create sample data directory
    sample_dir = Path('sample_data')
    sample_dir.mkdir(exist_ok=True)
    
    print("Creating sample Excel files...")
    
    # 1. Create employees.xlsx
    print("  📊 Creating employees.xlsx...")
    employees = pd.DataFrame({
        'id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'name': [
            'Alice Johnson', 'Bob Smith', 'Charlie Brown', 'Diana Prince', 'Eve Wilson',
            'Frank Miller', 'Grace Lee', 'Henry Davis', 'Ivy Chen', 'Jack Wilson'
        ],
        'age': [28, 35, 42, 31, 29, 38, 26, 45, 33, 40],
        'department': [
            'Engineering', 'Sales', 'Engineering', 'Marketing', 'Sales',
            'Engineering', 'Marketing', 'Sales', 'Engineering', 'Marketing'
        ],
        'salary': [75000, 65000, 85000, 70000, 68000, 80000, 62000, 72000, 78000, 74000],
        'hire_date': pd.to_datetime([
            '2020-01-15', '2019-03-22', '2018-07-10', '2021-02-28', '2020-11-05',
            '2019-08-12', '2022-01-10', '2018-12-03', '2021-06-15', '2020-09-20'
        ]),
        'email': [
            'alice.johnson@company.com', 'bob.smith@company.com', 'charlie.brown@company.com',
            'diana.prince@company.com', 'eve.wilson@company.com', 'frank.miller@company.com',
            'grace.lee@company.com', 'henry.davis@company.com', 'ivy.chen@company.com',
            'jack.wilson@company.com'
        ]
    })
    
    with pd.ExcelWriter(sample_dir / 'employees.xlsx', engine='openpyxl') as writer:
        employees.to_excel(writer, sheet_name='staff', index=False)
        
        # Add a department summary sheet
        dept_summary = employees.groupby('department').agg({
            'salary': ['mean', 'min', 'max', 'count'],
            'age': 'mean'
        }).round(2)
        dept_summary.columns = ['avg_salary', 'min_salary', 'max_salary', 'employee_count', 'avg_age']
        dept_summary.to_excel(writer, sheet_name='department_summary')
    
    # 2. Create orders.xlsx
    print("  📈 Creating orders.xlsx...")
    orders = pd.DataFrame({
        'order_id': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112],
        'employee_id': [1, 2, 1, 3, 4, 2, 5, 6, 3, 7, 8, 4],
        'customer': [
            'Acme Corp', 'Beta Inc', 'Gamma LLC', 'Delta Co', 'Epsilon Ltd', 'Zeta Corp',
            'Alpha Systems', 'Omega Solutions', 'Theta Industries', 'Sigma Tech',
            'Lambda Enterprises', 'Kappa Holdings'
        ],
        'amount': [15000, 8500, 22000, 12000, 18500, 9500, 14000, 25000, 16500, 11000, 19000, 13500],
        'order_date': pd.to_datetime([
            '2024-01-10', '2024-01-15', '2024-01-20', '2024-01-25', '2024-02-01', '2024-02-05',
            '2024-02-10', '2024-02-15', '2024-02-20', '2024-02-25', '2024-03-01', '2024-03-05'
        ]),
        'status': [
            'Completed', 'Pending', 'Completed', 'Shipped', 'Completed', 'Pending',
            'Completed', 'Shipped', 'Pending', 'Completed', 'Shipped', 'Completed'
        ],
        'region': [
            'North', 'South', 'East', 'West', 'North', 'South',
            'East', 'West', 'North', 'South', 'East', 'West'
        ]
    })
    
    orders.to_excel(sample_dir / 'orders.xlsx', sheet_name='sales_data', index=False)
    
    # 3. Create products.xlsx with multiple sheets
    print("  🛍️ Creating products.xlsx...")
    products = pd.DataFrame({
        'product_id': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006', 'P007', 'P008'],
        'name': [
            'Laptop Pro', 'Desktop Elite', 'Tablet Max', 'Phone Ultra', 
            'Watch Smart', 'Headphones Premium', 'Monitor 4K', 'Keyboard Mechanical'
        ],
        'category': [
            'Computers', 'Computers', 'Tablets', 'Phones', 
            'Wearables', 'Audio', 'Monitors', 'Accessories'
        ],
        'price': [1299.99, 899.99, 599.99, 799.99, 299.99, 199.99, 449.99, 129.99],
        'in_stock': [45, 23, 67, 89, 156, 78, 34, 92],
        'supplier': [
            'TechCorp', 'CompuMax', 'TabletInc', 'PhoneCo',
            'WearTech', 'AudioPro', 'DisplayTech', 'AccessoryPlus'
        ]
    })
    
    inventory = pd.DataFrame({
        'product_id': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006', 'P007', 'P008'],
        'warehouse': ['West', 'East', 'West', 'Central', 'East', 'West', 'Central', 'East'],
        'quantity': [25, 15, 40, 60, 80, 45, 20, 55],
        'reserved': [5, 3, 8, 12, 15, 8, 4, 10],
        'last_updated': pd.to_datetime([
            '2024-02-01', '2024-02-02', '2024-02-01', '2024-02-03', 
            '2024-02-02', '2024-02-04', '2024-02-03', '2024-02-04'
        ])
    })
    
    with pd.ExcelWriter(sample_dir / 'products.xlsx', engine='openpyxl') as writer:
        products.to_excel(writer, sheet_name='catalog', index=False)
        inventory.to_excel(writer, sheet_name='inventory', index=False)
    
    # 4. Create customers.xlsx
    print("  👥 Creating customers.xlsx...")
    customers = pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        'company_name': [
            'Acme Corp', 'Beta Inc', 'Gamma LLC', 'Delta Co', 'Epsilon Ltd', 'Zeta Corp',
            'Alpha Systems', 'Omega Solutions', 'Theta Industries', 'Sigma Tech',
            'Lambda Enterprises', 'Kappa Holdings'
        ],
        'contact_person': [
            'John Doe', 'Jane Smith', 'Mike Johnson', 'Sarah Wilson', 'Tom Brown', 'Lisa Davis',
            'Chris Lee', 'Amy Chen', 'David Miller', 'Emma Taylor', 'Ryan Garcia', 'Sophia Martinez'
        ],
        'industry': [
            'Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 'Education',
            'Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 'Education'
        ],
        'annual_revenue': [
            5000000, 2500000, 8000000, 3500000, 6000000, 1500000,
            4500000, 7500000, 3000000, 5500000, 2000000, 4000000
        ],
        'region': [
            'North', 'South', 'East', 'West', 'North', 'South',
            'East', 'West', 'North', 'South', 'East', 'West'
        ]
    })
    
    customers.to_excel(sample_dir / 'customers.xlsx', sheet_name='client_data', index=False)
    
    # 5. Create a file with special characters for CSV export testing
    print("  🔤 Creating special_data.xlsx...")
    special_data = pd.DataFrame({
        'text_with_commas': ['Hello, World!', 'Test, Data', 'Comma, Separated, Values'],
        'text_with_quotes': ['He said "Hello"', 'Quote "Test"', 'Multiple "quotes" here'],
        'text_with_newlines': ['Line 1\nLine 2', 'Multi\nLine\nText', 'Single Line'],
        'mixed_data': ['Normal text', 'Text, with "quotes"', 'Text\nwith\nnewlines'],
        'numbers': [123, 456.78, 999.99]
    })
    
    special_data.to_excel(sample_dir / 'special_data.xlsx', sheet_name='test_data', index=False)
    
    print(f"\n✅ Sample Excel files created successfully in '{sample_dir}' directory!")
    print("\nFiles created:")
    print("  📊 employees.xlsx (sheets: staff, department_summary)")
    print("  📈 orders.xlsx (sheet: sales_data)")
    print("  🛍️ products.xlsx (sheets: catalog, inventory)")
    print("  👥 customers.xlsx (sheet: client_data)")
    print("  🔤 special_data.xlsx (sheet: test_data)")
    
    print(f"\nTo start using the Excel DataFrame Processor:")
    print(f"  uv run python -m excel_processor --db {sample_dir}")
    
    print(f"\nExample queries to try:")
    print("  SHOW DB")
    print("  SELECT * FROM employees.staff")
    print("  SELECT name, salary FROM employees.staff WHERE salary > 70000")
    print("  SELECT e.name, o.amount FROM employees.staff e, orders.sales_data o WHERE e.id = o.employee_id")

if __name__ == "__main__":
    create_sample_data()