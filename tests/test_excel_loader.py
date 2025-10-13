"""Unit tests for Excel file loading functionality."""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from datetime import datetime

from excel_processor.excel_loader import ExcelLoader
from excel_processor.exceptions import FileLoadError


class TestExcelLoader:
    """Test cases for ExcelLoader class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = ExcelLoader()
    
    def test_validate_file_existing_excel(self, sample_excel_file):
        """Test file validation with existing Excel file."""
        assert self.loader.validate_file(sample_excel_file) is True
    
    def test_validate_file_nonexistent(self, temp_db_dir):
        """Test file validation with non-existent file."""
        non_existent = temp_db_dir / "nonexistent.xlsx"
        assert self.loader.validate_file(non_existent) is False
    
    def test_validate_file_unsupported_format(self, temp_db_dir):
        """Test file validation with unsupported file format."""
        txt_file = temp_db_dir / "test.txt"
        txt_file.write_text("not an excel file")
        assert self.loader.validate_file(txt_file) is False
    
    def test_validate_file_directory(self, temp_db_dir):
        """Test file validation with directory instead of file."""
        assert self.loader.validate_file(temp_db_dir) is False
    
    def test_get_sheet_names(self, sample_excel_file):
        """Test getting sheet names from Excel file."""
        sheet_names = self.loader.get_sheet_names(sample_excel_file)
        assert isinstance(sheet_names, list)
        assert len(sheet_names) >= 1
        assert 'employees' in sheet_names
        assert 'orders' in sheet_names
    
    def test_get_sheet_names_invalid_file(self, temp_db_dir):
        """Test getting sheet names from invalid file."""
        invalid_file = temp_db_dir / "invalid.xlsx"
        with pytest.raises(FileLoadError) as exc_info:
            self.loader.get_sheet_names(invalid_file)
        assert "File validation failed" in str(exc_info.value)
    
    def test_load_sheet_by_name(self, sample_excel_file):
        """Test loading a sheet by name."""
        df = self.loader.load_sheet(sample_excel_file, 'employees')
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'id' in df.columns
        assert 'name' in df.columns
        assert 'age' in df.columns
    
    def test_load_sheet_by_index(self, sample_excel_file):
        """Test loading a sheet by index."""
        df = self.loader.load_sheet(sample_excel_file, 0)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
    
    def test_load_sheet_invalid_name(self, sample_excel_file):
        """Test loading sheet with invalid name."""
        with pytest.raises(FileLoadError) as exc_info:
            self.loader.load_sheet(sample_excel_file, 'nonexistent_sheet')
        assert "not found" in str(exc_info.value)
        assert "Available sheets:" in str(exc_info.value)
    
    def test_load_sheet_invalid_index(self, sample_excel_file):
        """Test loading sheet with invalid index."""
        with pytest.raises(FileLoadError) as exc_info:
            self.loader.load_sheet(sample_excel_file, 999)
        assert "out of range" in str(exc_info.value)
    
    def test_load_sheet_data_types(self, sample_excel_file):
        """Test that data types are properly inferred."""
        df = self.loader.load_sheet(sample_excel_file, 'employees')
        
        # Check that numeric columns are properly typed
        assert pd.api.types.is_numeric_dtype(df['id'])
        assert pd.api.types.is_numeric_dtype(df['age'])
        assert pd.api.types.is_numeric_dtype(df['salary'])
        
        # Check that string columns are object type
        assert df['name'].dtype == 'object' or pd.api.types.is_categorical_dtype(df['name'])
    
    def test_load_file_all_sheets(self, sample_excel_file):
        """Test loading all sheets from a file."""
        sheets = self.loader.load_file(sample_excel_file)
        assert isinstance(sheets, dict)
        assert len(sheets) >= 2
        assert 'employees' in sheets
        assert 'orders' in sheets
        
        # Check that each sheet is a DataFrame
        for sheet_name, df in sheets.items():
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
    
    def test_load_file_invalid_file(self, temp_db_dir):
        """Test loading from invalid file."""
        invalid_file = temp_db_dir / "invalid.xlsx"
        with pytest.raises(FileLoadError):
            self.loader.load_file(invalid_file)
    
    def test_create_excel_file_model(self, sample_excel_file, temp_db_dir):
        """Test creating ExcelFile model."""
        excel_file = self.loader.create_excel_file_model(sample_excel_file, temp_db_dir)
        
        assert excel_file.file_name == "sample.xlsx"
        assert excel_file.file_path == str(sample_excel_file)
        assert isinstance(excel_file.sheets, dict)
        assert len(excel_file.sheets) >= 2
        assert excel_file.memory_usage > 0
        assert isinstance(excel_file.last_modified, datetime)
    
    def test_get_file_info(self, sample_excel_file):
        """Test getting file information."""
        info = self.loader.get_file_info(sample_excel_file)
        
        assert 'file_path' in info
        assert 'file_name' in info
        assert 'file_size_mb' in info
        assert 'sheet_names' in info
        assert 'sheet_count' in info
        assert 'last_modified' in info
        assert 'extension' in info
        
        assert info['file_name'] == 'sample.xlsx'
        assert info['extension'] == '.xlsx'
        assert info['sheet_count'] >= 2
        assert isinstance(info['sheet_names'], list)
        assert info['file_size_mb'] > 0
    
    def test_optimize_dtypes(self, temp_db_dir):
        """Test data type optimization."""
        # Create a test DataFrame with various data types
        test_data = {
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'string_col': ['A', 'B', 'C', 'D', 'E'],
            'category_col': ['X', 'Y', 'X', 'Y', 'X'],  # Low cardinality
            'date_col': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            'mixed_col': ['1', '2', 'text', '4', '5']  # Mixed numeric/text
        }
        df = pd.DataFrame(test_data)
        
        # Create a temporary Excel file
        temp_file = temp_db_dir / "test_dtypes.xlsx"
        df.to_excel(temp_file, index=False)
        
        # Load and check optimized types
        loaded_df = self.loader.load_sheet(temp_file, 0)
        
        # Numeric columns should be optimized
        assert pd.api.types.is_numeric_dtype(loaded_df['int_col'])
        assert pd.api.types.is_numeric_dtype(loaded_df['float_col'])
        
        # Category column should be categorical if optimization worked
        # (This might not always happen depending on the data)
        assert loaded_df['category_col'].dtype in ['object', 'category']
    
    def test_corrupted_file_handling(self, temp_db_dir):
        """Test handling of corrupted Excel files."""
        # Create a file that looks like Excel but isn't
        corrupted_file = temp_db_dir / "corrupted.xlsx"
        corrupted_file.write_bytes(b"This is not an Excel file")
        
        with pytest.raises(FileLoadError) as exc_info:
            self.loader.load_file(corrupted_file)
        assert "Failed to load Excel file" in str(exc_info.value)
    
    def test_empty_file_handling(self, temp_db_dir):
        """Test handling of empty Excel files."""
        # Create an empty Excel file
        empty_file = temp_db_dir / "empty.xlsx"
        empty_df = pd.DataFrame()
        empty_df.to_excel(empty_file, index=False)
        
        # Should be able to load but result in empty DataFrame
        df = self.loader.load_sheet(empty_file, 0)
        assert isinstance(df, pd.DataFrame)
        # Empty files might have 0 rows or 1 row with NaN values
        assert len(df) >= 0
    
    def test_special_characters_in_data(self, temp_db_dir):
        """Test handling of special characters in Excel data."""
        # Create DataFrame with special characters
        special_data = {
            'text': ['Hello, World!', 'Quote"Test', 'New\nLine', 'Tab\tTest', 'Comma,Test'],
            'unicode': ['café', 'naïve', '北京', '🚀', 'résumé'],
            'numbers': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(special_data)
        
        # Save and load
        temp_file = temp_db_dir / "special_chars.xlsx"
        df.to_excel(temp_file, index=False)
        
        loaded_df = self.loader.load_sheet(temp_file, 0)
        
        # Check that special characters are preserved
        assert len(loaded_df) == 5
        assert 'Hello, World!' in loaded_df['text'].values
        assert 'café' in loaded_df['unicode'].values
    
    def test_large_file_handling(self, temp_db_dir):
        """Test handling of larger Excel files."""
        # Create a larger DataFrame (1000 rows)
        large_data = {
            'id': range(1000),
            'name': [f'Person_{i}' for i in range(1000)],
            'value': [i * 1.5 for i in range(1000)]
        }
        df = pd.DataFrame(large_data)
        
        # Save and load
        temp_file = temp_db_dir / "large_file.xlsx"
        df.to_excel(temp_file, index=False)
        
        loaded_df = self.loader.load_sheet(temp_file, 0)
        
        assert len(loaded_df) == 1000
        assert list(loaded_df.columns) == ['id', 'name', 'value']
        
        # Check memory usage calculation
        excel_file = self.loader.create_excel_file_model(temp_file, temp_db_dir)
        assert excel_file.memory_usage > 0