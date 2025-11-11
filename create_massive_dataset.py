#!/usr/bin/env python3
"""
Create massive datasets for stress testing
Generates 10M+ rows with 50+ columns to test scalability
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path
import time

def format_size(bytes_size):
    """Format size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def generate_massive_employee_data(num_rows=2_000_000):
    """Generate massive employee dataset with 50+ columns"""
    print(f"🔄 Generating {num_rows:,} employee records with 50+ columns...")
    start_time = time.time()
    
    np.random.seed(42)
    random.seed(42)
    
    # Expanded lists for variety
    first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
                   'William', 'Barbara', 'David', 'Elizabeth', 'Richard', 'Susan', 'Joseph', 'Jessica',
                   'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
                   'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra', 'Donald', 'Ashley',
                   'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle'] * 25
    
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                  'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
                  'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White',
                  'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker'] * 33
    
    departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 
                   'IT', 'Customer Service', 'Legal', 'R&D', 'Product', 'Design',
                   'Analytics', 'Security', 'Compliance', 'Quality Assurance'] * 62
    
    locations = ['New York', 'San Francisco', 'Chicago', 'Austin', 'Seattle', 
                 'Boston', 'Denver', 'Atlanta', 'Los Angeles', 'Miami',
                 'Portland', 'Phoenix', 'Dallas', 'Houston', 'Philadelphia'] * 66
    
    job_levels = ['Junior', 'Mid-Level', 'Senior', 'Lead', 'Principal', 'Manager', 'Director', 'VP', 'C-Level'] * 111
    
    skills = ['Python', 'Java', 'JavaScript', 'SQL', 'AWS', 'Docker', 'Kubernetes', 'React',
              'Angular', 'Node.js', 'Machine Learning', 'Data Science', 'DevOps', 'Agile'] * 71
    
    print("   📊 Generating core employee data...")
    data = {
        # Core identity
        'employee_id': range(1, num_rows + 1),
        'first_name': [random.choice(first_names) for _ in range(num_rows)],
        'last_name': [random.choice(last_names) for _ in range(num_rows)],
        'email': [f'employee{i}@company.com' for i in range(1, num_rows + 1)],
        'employee_code': [f'EMP{i:08d}' for i in range(1, num_rows + 1)],
        
        # Job information
        'department': [random.choice(departments) for _ in range(num_rows)],
        'job_title': [random.choice(job_levels) for _ in range(num_rows)],
        'job_level': np.random.randint(1, 11, num_rows),
        'location': [random.choice(locations) for _ in range(num_rows)],
        'office_floor': np.random.randint(1, 51, num_rows),
        'desk_number': np.random.randint(1, 1001, num_rows),
        
        # Compensation
        'salary': np.random.normal(75000, 25000, num_rows).clip(35000, 250000).astype(int),
        'bonus_percent': np.random.uniform(0, 30, num_rows).round(2),
        'stock_options': np.random.exponential(5000, num_rows).astype(int),
        'commission_rate': np.random.uniform(0, 15, num_rows).round(2),
        
        # Demographics
        'age': np.random.normal(38, 10, num_rows).clip(22, 65).astype(int),
        'years_experience': np.random.normal(8, 5, num_rows).clip(0, 40).astype(int),
        'education_level': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], num_rows, p=[0.1, 0.5, 0.3, 0.1]),
        'gender': np.random.choice(['M', 'F', 'Other'], num_rows, p=[0.48, 0.48, 0.04]),
        
        # Performance
        'performance_rating': np.random.choice([1, 2, 3, 4, 5], num_rows, p=[0.05, 0.15, 0.40, 0.30, 0.10]),
        'projects_completed': np.random.poisson(12, num_rows),
        'certifications': np.random.poisson(2, num_rows),
        'training_hours': np.random.exponential(40, num_rows).astype(int),
        
        # Work details
        'hire_date': [datetime(2010, 1, 1) + timedelta(days=random.randint(0, 5000)) for _ in range(num_rows)],
        'last_promotion_date': [datetime(2015, 1, 1) + timedelta(days=random.randint(0, 3500)) for _ in range(num_rows)],
        'is_remote': np.random.choice([True, False], num_rows, p=[0.4, 0.6]),
        'work_hours_per_week': np.random.normal(40, 5, num_rows).clip(20, 60).astype(int),
        'overtime_hours': np.random.exponential(5, num_rows).astype(int),
        
        # Benefits
        'health_insurance': np.random.choice([True, False], num_rows, p=[0.95, 0.05]),
        'dental_insurance': np.random.choice([True, False], num_rows, p=[0.85, 0.15]),
        'vision_insurance': np.random.choice([True, False], num_rows, p=[0.75, 0.25]),
        'retirement_401k': np.random.choice([True, False], num_rows, p=[0.80, 0.20]),
        'pto_days': np.random.randint(10, 31, num_rows),
        'sick_days': np.random.randint(5, 16, num_rows),
        
        # Skills and competencies
        'primary_skill': [random.choice(skills) for _ in range(num_rows)],
        'skill_level': np.random.randint(1, 11, num_rows),
        'languages_spoken': np.random.randint(1, 6, num_rows),
        'leadership_score': np.random.uniform(0, 100, num_rows).round(2),
        'technical_score': np.random.uniform(0, 100, num_rows).round(2),
        'communication_score': np.random.uniform(0, 100, num_rows).round(2),
        
        # Engagement
        'satisfaction_score': np.random.uniform(1, 10, num_rows).round(2),
        'engagement_score': np.random.uniform(1, 10, num_rows).round(2),
        'retention_risk': np.random.choice(['Low', 'Medium', 'High'], num_rows, p=[0.7, 0.2, 0.1]),
        'last_survey_date': [datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365)) for _ in range(num_rows)],
        
        # Additional metrics
        'meetings_per_week': np.random.poisson(15, num_rows),
        'emails_per_day': np.random.poisson(50, num_rows),
        'code_commits': np.random.exponential(100, num_rows).astype(int),
        'bugs_fixed': np.random.exponential(50, num_rows).astype(int),
        'customer_interactions': np.random.exponential(20, num_rows).astype(int),
        'sales_closed': np.random.exponential(10, num_rows).astype(int),
        'revenue_generated': np.random.exponential(100000, num_rows).astype(int),
    }
    
    print("   🔧 Creating DataFrame...")
    df = pd.DataFrame(data)
    
    # Add computed columns
    print("   ➕ Adding computed columns...")
    df['full_name'] = df['first_name'] + ' ' + df['last_name']
    df['annual_compensation'] = df['salary'] + (df['salary'] * df['bonus_percent'] / 100) + df['stock_options']
    df['tenure_years'] = ((datetime.now() - df['hire_date']).dt.days / 365).round(2)
    df['total_benefits_value'] = (
        df['health_insurance'] * 5000 +
        df['dental_insurance'] * 1000 +
        df['vision_insurance'] * 500 +
        df['retirement_401k'] * 3000
    )
    
    elapsed = time.time() - start_time
    memory_mb = df.memory_usage(deep=True).sum() / 1024**2
    
    print(f"✅ Generated {len(df):,} employee records with {len(df.columns)} columns")
    print(f"⏱️  Generation time: {elapsed:.2f}s")
    print(f"📊 Memory usage: {memory_mb:.2f} MB")
    
    return df

def generate_massive_transactions(num_rows=4_000_000):
    """Generate massive transaction dataset"""
    print(f"🔄 Generating {num_rows:,} transaction records...")
    start_time = time.time()
    
    np.random.seed(42)
    random.seed(42)
    
    products = [f'Product_{chr(65+i//26)}{chr(65+i%26)}' for i in range(200)]
    regions = ['North', 'South', 'East', 'West', 'Central', 'Northeast', 'Southeast', 'Northwest', 'Southwest']
    channels = ['Online', 'In-Store', 'Mobile App', 'Phone', 'Partner']
    payment_methods = ['Credit Card', 'Debit Card', 'PayPal', 'Wire Transfer', 'Cash', 'Crypto']
    
    print("   📊 Generating transaction data...")
    data = {
        'transaction_id': range(1, num_rows + 1),
        'transaction_date': [datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1460), 
                                                               hours=random.randint(0, 23),
                                                               minutes=random.randint(0, 59)) 
                            for _ in range(num_rows)],
        'product': [random.choice(products) for _ in range(num_rows)],
        'customer_id': np.random.randint(1, 1_000_001, num_rows),
        'sales_rep_id': np.random.randint(1, 10001, num_rows),
        'region': [random.choice(regions) for _ in range(num_rows)],
        'channel': [random.choice(channels) for _ in range(num_rows)],
        'payment_method': [random.choice(payment_methods) for _ in range(num_rows)],
        
        'quantity': np.random.poisson(5, num_rows) + 1,
        'unit_price': np.random.uniform(10, 1000, num_rows).round(2),
        'discount_percent': np.random.choice([0, 5, 10, 15, 20, 25], num_rows, p=[0.4, 0.2, 0.15, 0.15, 0.08, 0.02]),
        'shipping_cost': np.random.uniform(5, 50, num_rows).round(2),
        'tax_rate': np.random.choice([0.05, 0.07, 0.08, 0.10], num_rows),
        
        'processing_time_seconds': np.random.exponential(30, num_rows).astype(int),
        'customer_rating': np.random.choice([1, 2, 3, 4, 5], num_rows, p=[0.02, 0.05, 0.13, 0.35, 0.45]),
        'is_returned': np.random.choice([True, False], num_rows, p=[0.05, 0.95]),
        'is_fraud': np.random.choice([True, False], num_rows, p=[0.001, 0.999]),
    }
    
    print("   🔧 Creating DataFrame...")
    df = pd.DataFrame(data)
    
    # Computed columns
    print("   ➕ Adding computed columns...")
    df['subtotal'] = (df['quantity'] * df['unit_price']).round(2)
    df['discount_amount'] = (df['subtotal'] * df['discount_percent'] / 100).round(2)
    df['tax_amount'] = ((df['subtotal'] - df['discount_amount']) * df['tax_rate']).round(2)
    df['total_amount'] = (df['subtotal'] - df['discount_amount'] + df['tax_amount'] + df['shipping_cost']).round(2)
    df['profit_margin'] = np.random.uniform(0.1, 0.4, num_rows).round(2)
    df['profit'] = (df['total_amount'] * df['profit_margin']).round(2)
    
    elapsed = time.time() - start_time
    memory_mb = df.memory_usage(deep=True).sum() / 1024**2
    
    print(f"✅ Generated {len(df):,} transaction records with {len(df.columns)} columns")
    print(f"⏱️  Generation time: {elapsed:.2f}s")
    print(f"📊 Memory usage: {memory_mb:.2f} MB")
    
    return df

def save_in_chunks(df, file_path, chunk_size=100000):
    """Save large DataFrame to Excel in chunks"""
    print(f"   💾 Saving to {file_path.name} in chunks...")
    
    # For very large files, save as CSV instead of Excel
    if len(df) > 1_000_000:
        print(f"   📄 File too large for Excel, saving as CSV...")
        df.to_csv(file_path.with_suffix('.csv'), index=False)
        return file_path.with_suffix('.csv')
    
    # Save to Excel
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='data', index=False)
    
    return file_path

def main():
    """Generate massive datasets for stress testing"""
    print("=" * 80)
    print("🚀 Creating MASSIVE Datasets for Stress Testing (20x larger)")
    print("=" * 80)
    print()
    print("⚠️  WARNING: This will generate LARGE files!")
    print("   • 2M employee records (~1GB)")
    print("   • 4M transaction records (~2GB)")
    print("   • Total: ~3GB of data")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Create directory
    massive_dir = Path('massive_data')
    massive_dir.mkdir(exist_ok=True)
    
    print("\n" + "=" * 80)
    print("📊 Dataset 1: Massive Employee Database (2M rows, 50+ columns)")
    print("=" * 80)
    
    employees_df = generate_massive_employee_data(2_000_000)
    
    print("\n💾 Saving employee data...")
    emp_file = massive_dir / 'massive_employees.csv'
    employees_df.to_csv(emp_file, index=False)
    file_size = emp_file.stat().st_size
    print(f"✅ Saved: {emp_file.name} ({format_size(file_size)})")
    
    # Create summary
    print("\n📊 Creating employee summary...")
    emp_summary = employees_df.groupby('department').agg({
        'employee_id': 'count',
        'salary': ['mean', 'min', 'max'],
        'age': 'mean',
        'performance_rating': 'mean',
        'annual_compensation': 'mean'
    }).round(2)
    emp_summary.to_csv(massive_dir / 'employee_summary.csv')
    
    print("\n" + "=" * 80)
    print("📊 Dataset 2: Massive Transaction Database (4M rows)")
    print("=" * 80)
    
    transactions_df = generate_massive_transactions(4_000_000)
    
    print("\n💾 Saving transaction data...")
    trans_file = massive_dir / 'massive_transactions.csv'
    transactions_df.to_csv(trans_file, index=False)
    file_size = trans_file.stat().st_size
    print(f"✅ Saved: {trans_file.name} ({format_size(file_size)})")
    
    # Create summary
    print("\n📊 Creating transaction summary...")
    trans_summary = transactions_df.groupby('region').agg({
        'transaction_id': 'count',
        'total_amount': 'sum',
        'profit': 'sum'
    }).round(2)
    trans_summary.to_csv(massive_dir / 'transaction_summary.csv')
    
    # Create test queries file
    print("\n📝 Creating stress test queries...")
    test_queries = """# Stress Test Queries for Massive Datasets

## Basic Queries (Should be fast with SQLite cache)
SELECT COUNT(*) FROM massive_employees.data
SELECT COUNT(*) FROM massive_transactions.data

## Filtering Queries
SELECT * FROM massive_employees.data WHERE salary > 150000 LIMIT 1000
SELECT * FROM massive_transactions.data WHERE total_amount > 5000 LIMIT 1000

## Aggregation Queries (Test GROUP BY performance)
SELECT department, COUNT(*) as count, AVG(salary) as avg_salary 
FROM massive_employees.data 
GROUP BY department

SELECT region, SUM(total_amount) as revenue, COUNT(*) as transactions
FROM massive_transactions.data 
GROUP BY region

## Complex Queries
SELECT department, location, COUNT(*) as count, AVG(annual_compensation) as avg_comp
FROM massive_employees.data 
WHERE performance_rating >= 4 
GROUP BY department, location 
HAVING COUNT(*) > 100
ORDER BY avg_comp DESC
LIMIT 50

SELECT product, region, SUM(total_amount) as revenue, SUM(profit) as profit
FROM massive_transactions.data 
WHERE transaction_date >= '2023-01-01'
GROUP BY product, region 
ORDER BY revenue DESC 
LIMIT 100

## Window Functions (Test advanced features)
SELECT employee_id, full_name, salary, department,
       ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as dept_rank
FROM massive_employees.data 
WHERE department IN ('Engineering', 'Sales', 'Marketing')
LIMIT 1000
"""
    
    with open(massive_dir / 'stress_test_queries.txt', 'w') as f:
        f.write(test_queries)
    
    # Final summary
    total_size = sum(f.stat().st_size for f in massive_dir.glob('*.csv'))
    
    print("\n" + "=" * 80)
    print("✅ Massive Dataset Generation Complete!")
    print("=" * 80)
    print(f"\n📁 Files created in {massive_dir}:")
    print(f"   📊 massive_employees.csv     - {len(employees_df):,} rows, {len(employees_df.columns)} columns")
    print(f"   📊 massive_transactions.csv  - {len(transactions_df):,} rows, {len(transactions_df.columns)} columns")
    print(f"   📋 employee_summary.csv")
    print(f"   📋 transaction_summary.csv")
    print(f"   📝 stress_test_queries.txt")
    
    print(f"\n💾 Total size: {format_size(total_size)}")
    print(f"📊 Total records: {len(employees_df) + len(transactions_df):,}")
    
    print("\n🚀 Ready for stress testing!")
    print("   Run: python stress_test_benchmark.py")
    print()
    print("⚠️  Note: First load will take time to create SQLite cache")
    print("   Subsequent queries will be MUCH faster!")

if __name__ == '__main__':
    main()
