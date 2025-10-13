"""Pytest configuration and fixtures for Excel DataFrame Processor tests."""

import pytest
import tempfile
import os
from pathlib import Path
import pandas as pd


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for test database files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'age': [25, 30, 35, 28, 32],
        'salary': [50000, 60000, 70000, 55000, 65000],
        'department': ['IT', 'HR', 'IT', 'Finance', 'HR']
    })


@pytest.fixture
def sample_excel_file(temp_db_dir, sample_dataframe):
    """Create a sample Excel file for testing."""
    file_path = temp_db_dir / "sample.xlsx"
    
    # Create multiple sheets
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        sample_dataframe.to_excel(writer, sheet_name='employees', index=False)
        
        # Second sheet with different data
        orders_df = pd.DataFrame({
            'order_id': [101, 102, 103, 104],
            'employee_id': [1, 2, 1, 3],
            'amount': [1000, 1500, 2000, 1200],
            'date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'])
        })
        orders_df.to_excel(writer, sheet_name='orders', index=False)
    
    return file_path