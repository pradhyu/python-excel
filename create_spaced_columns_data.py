#!/usr/bin/env python3
"""Create test data with column names containing spaces."""
import pandas as pd
from pathlib import Path

def create_spaced_columns_data():
    """Create Excel file with column names containing spaces."""
    # Create test data with spaced column names
    data = {
        'Employee ID': [1, 2, 3, 4, 5],
        'Full Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson'],
        'Job Title': ['Software Engineer', 'Data Analyst', 'Project Manager', 'UX Designer', 'DevOps Engineer'],
        'Annual Salary': [75000, 65000, 85000, 70000, 80000],
        'Years of Experience': [3, 2, 8, 4, 6],
        'Performance Rating': [4.2, 4.5, 3.8, 4.7, 4.1]
    }
    
    df = pd.DataFrame(data)
    
    # Create directory if it doesn't exist
    Path('sample_data').mkdir(exist_ok=True)
    
    # Save to Excel file
    with pd.ExcelWriter('sample_data/spaced_columns.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='employee_data', index=False)
    
    print("✅ Created spaced_columns.xlsx with column names containing spaces")
    print(f"📊 Data shape: {df.shape}")
    print("📋 Columns with spaces:")
    for col in df.columns:
        print(f"  - '{col}'")
    print("\n📋 Sample data:")
    print(df.head())

if __name__ == "__main__":
    create_spaced_columns_data()