"""Unit tests for DataFrame manager functionality."""

import pytest
import pandas as pd
import tempfile
import time
from pathlib import Path
from datetime import datetime

from excel_processor.dataframe_manager import DataFrameManager
from excel_processor.exceptions import (
    DatabaseDirectoryError, 
    TableNotFoundError, 
    FileLoadError,
    MemoryError as ProcessorMemoryError
)


class TestDataFrameManager:
    """Test cases for DataFrameManager class."""
    
    def test_init_valid_directory(self, temp_db_dir):
        """Test initialization with valid directory."""
        manager = DataFrameManager(temp_db_dir)
        assert manager.db_directory == temp_db_dir
        assert manager.memory_limit_mb == 1024.0
        assert len(manager.loaded_files) == 0
    
    def test_init_nonexistent_directory(self):
        """Test initialization with non-existent directory."""
        with pytest.raises(DatabaseDirectoryError) as exc_info:
            DataFrameManager("/nonexistent/directory")
        assert "does not exist" in str(exc_info.value)
    
    def test_init_file_instead_of_directory(self, temp_db_dir):
        """Test initialization with file instead of directory."""
        file_path = temp_db_dir / "test.txt"
        file_path.write_text("test")
        
        with pytest.raises(DatabaseDirectoryError) as exc_info:
            DataFrameManager(file_path)
        assert "not a directory" in str(exc_info.value)
    
    def test_scan_db_directory(self, temp_db_dir, sample_excel_file):
        """Test scanning database directory for Excel files."""
        manager = DataFrameManager(temp_db_dir)
        excel_files = manager.scan_db_directory()
        
        assert isinstance(excel_files, dict)
        assert "sample.xlsx" in excel_files
        assert isinstance(excel_files["sample.xlsx"], list)
        assert len(excel_files["sample.xlsx"]) >= 2
        assert "employees" in excel_files["sample.xlsx"]
        assert "orders" in excel_files["sample.xlsx"]
    
    def test_scan_empty_directory(self, temp_db_dir):
        """Test scanning empty directory."""
        manager = DataFrameManager(temp_db_dir)
        excel_files = manager.scan_db_directory()
        assert excel_files == {}
    
    def test_get_database_info(self, temp_db_dir, sample_excel_file):
        """Test getting database information."""
        manager = DataFrameManager(temp_db_dir)
        db_info = manager.get_database_info()
        
        assert db_info.directory_path == str(temp_db_dir)
        assert db_info.total_files >= 1
        assert db_info.loaded_files == 0
        assert "sample.xlsx" in db_info.excel_files
    
    def test_get_file_path_existing_file(self, temp_db_dir, sample_excel_file):
        """Test getting file path for existing file."""
        manager = DataFrameManager(temp_db_dir)
        
        # Test with full filename
        file_path = manager.get_file_path("sample.xlsx")
        assert file_path.exists()
        assert file_path.name == "sample.xlsx"
        
        # Test with filename without extension
        file_path = manager.get_file_path("sample")
        assert file_path.exists()
        assert file_path.name == "sample.xlsx"
    
    def test_get_file_path_nonexistent_file(self, temp_db_dir):
        """Test getting file path for non-existent file."""
        manager = DataFrameManager(temp_db_dir)
        file_path = manager.get_file_path("nonexistent.xlsx")
        assert not file_path.exists()
    
    def test_load_excel_file(self, temp_db_dir, sample_excel_file):
        """Test loading Excel file."""
        manager = DataFrameManager(temp_db_dir)
        excel_file = manager.load_excel_file("sample.xlsx")
        
        assert excel_file.file_name == "sample.xlsx"
        assert len(excel_file.sheets) >= 2
        assert "employees" in excel_file.sheets
        assert "orders" in excel_file.sheets
        assert excel_file.memory_usage > 0
        
        # Check that file is cached
        assert "sample.xlsx" in manager.loaded_files
    
    def test_load_excel_file_nonexistent(self, temp_db_dir):
        """Test loading non-existent Excel file."""
        manager = DataFrameManager(temp_db_dir)
        
        with pytest.raises(TableNotFoundError):
            manager.load_excel_file("nonexistent.xlsx")
    
    def test_load_excel_file_caching(self, temp_db_dir, sample_excel_file):
        """Test that Excel files are properly cached."""
        manager = DataFrameManager(temp_db_dir)
        
        # Load file first time
        excel_file1 = manager.load_excel_file("sample.xlsx")
        
        # Load file second time (should use cache)
        excel_file2 = manager.load_excel_file("sample.xlsx")
        
        # Should be the same object (cached)
        assert excel_file1 is excel_file2
    
    def test_load_excel_file_force_reload(self, temp_db_dir, sample_excel_file):
        """Test force reloading Excel file."""
        manager = DataFrameManager(temp_db_dir)
        
        # Load file first time
        excel_file1 = manager.load_excel_file("sample.xlsx")
        
        # Force reload
        excel_file2 = manager.load_excel_file("sample.xlsx", force_reload=True)
        
        # Should be different objects
        assert excel_file1 is not excel_file2
        assert excel_file1.file_name == excel_file2.file_name
    
    def test_get_dataframe(self, temp_db_dir, sample_excel_file):
        """Test getting specific DataFrame."""
        manager = DataFrameManager(temp_db_dir)
        
        # Get DataFrame by sheet name
        df = manager.get_dataframe("sample.xlsx", "employees")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "id" in df.columns
        
        # Get DataFrame by sheet index
        df2 = manager.get_dataframe("sample.xlsx", 0)
        assert isinstance(df2, pd.DataFrame)
        assert len(df2) > 0
    
    def test_get_dataframe_invalid_sheet(self, temp_db_dir, sample_excel_file):
        """Test getting DataFrame with invalid sheet."""
        manager = DataFrameManager(temp_db_dir)
        
        # Invalid sheet name
        with pytest.raises(TableNotFoundError) as exc_info:
            manager.get_dataframe("sample.xlsx", "nonexistent_sheet")
        assert "nonexistent_sheet" in str(exc_info.value)
        
        # Invalid sheet index
        with pytest.raises(TableNotFoundError) as exc_info:
            manager.get_dataframe("sample.xlsx", 999)
        assert "sheet index 999" in str(exc_info.value)
    
    def test_load_all_db_files(self, temp_db_dir, sample_excel_file):
        """Test loading all files in database directory."""
        manager = DataFrameManager(temp_db_dir)
        
        # Create another Excel file
        df2 = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        file2_path = temp_db_dir / "test2.xlsx"
        df2.to_excel(file2_path, index=False)
        
        # Load all files
        loaded_files = manager.load_all_db_files(show_progress=False)
        
        assert len(loaded_files) >= 2
        assert "sample.xlsx" in loaded_files
        assert "test2.xlsx" in loaded_files
        
        # Check that files are cached in manager
        assert len(manager.loaded_files) >= 2
    
    def test_get_memory_usage(self, temp_db_dir, sample_excel_file):
        """Test getting memory usage information."""
        manager = DataFrameManager(temp_db_dir)
        
        # Initially no memory usage
        usage = manager.get_memory_usage()
        assert usage['total_mb'] == 0.0
        assert usage['usage_percent'] == 0.0
        assert len(usage['files']) == 0
        
        # Load a file
        manager.load_excel_file("sample.xlsx")
        
        # Check memory usage
        usage = manager.get_memory_usage()
        assert usage['total_mb'] > 0.0
        assert usage['usage_percent'] > 0.0
        assert "sample.xlsx" in usage['files']
        assert usage['files']["sample.xlsx"] > 0.0
    
    def test_memory_limit_enforcement(self, temp_db_dir):
        """Test memory limit enforcement."""
        # Set very low memory limit
        manager = DataFrameManager(temp_db_dir, memory_limit_mb=0.001)  # 1KB limit
        
        # Create a larger DataFrame
        large_df = pd.DataFrame({
            'col1': range(1000),
            'col2': [f'text_{i}' for i in range(1000)]
        })
        large_file = temp_db_dir / "large.xlsx"
        large_df.to_excel(large_file, index=False)
        
        # Should raise memory error
        with pytest.raises(ProcessorMemoryError) as exc_info:
            manager.load_excel_file("large.xlsx")
        assert "Memory usage" in str(exc_info.value)
        assert "exceeds limit" in str(exc_info.value)
    
    def test_clear_cache(self, temp_db_dir, sample_excel_file):
        """Test clearing cache."""
        manager = DataFrameManager(temp_db_dir)
        
        # Load files
        manager.load_excel_file("sample.xlsx")
        assert len(manager.loaded_files) == 1
        
        # Clear specific file
        manager.clear_cache("sample.xlsx")
        assert len(manager.loaded_files) == 0
        
        # Load again and clear all
        manager.load_excel_file("sample.xlsx")
        manager.clear_cache()
        assert len(manager.loaded_files) == 0
    
    def test_get_column_info(self, temp_db_dir, sample_excel_file):
        """Test getting column information."""
        manager = DataFrameManager(temp_db_dir)
        
        column_info = manager.get_column_info("sample.xlsx", "employees")
        
        assert isinstance(column_info, dict)
        assert "id" in column_info
        assert "name" in column_info
        assert "age" in column_info
        
        # Check data type mapping
        assert column_info["id"] in ["integer", "float"]  # Could be either depending on pandas version
        assert column_info["name"] in ["text", "category"]
        assert column_info["age"] in ["integer", "float"]
    
    def test_get_table_reference_info(self, temp_db_dir, sample_excel_file):
        """Test parsing table references."""
        manager = DataFrameManager(temp_db_dir)
        
        # Test with extension
        file_name, sheet_name = manager.get_table_reference_info("sample.xlsx.employees")
        assert file_name == "sample.xlsx"
        assert sheet_name == "employees"
        
        # Test without extension
        file_name, sheet_name = manager.get_table_reference_info("sample.employees")
        assert file_name == "sample.xlsx"  # Should find the .xlsx file
        assert sheet_name == "employees"
    
    def test_get_table_reference_info_invalid(self, temp_db_dir):
        """Test parsing invalid table references."""
        manager = DataFrameManager(temp_db_dir)
        
        # No dot
        with pytest.raises(ValueError) as exc_info:
            manager.get_table_reference_info("invalid")
        assert "Invalid table reference" in str(exc_info.value)
    
    def test_validate_table_reference(self, temp_db_dir, sample_excel_file):
        """Test validating table references."""
        manager = DataFrameManager(temp_db_dir)
        
        # Valid reference
        assert manager.validate_table_reference("sample.xlsx.employees") is True
        assert manager.validate_table_reference("sample.employees") is True
        
        # Invalid references
        assert manager.validate_table_reference("nonexistent.sheet") is False
        assert manager.validate_table_reference("sample.xlsx.nonexistent") is False
    
    def test_refresh_file_cache(self, temp_db_dir, sample_excel_file):
        """Test refreshing file cache when files are modified."""
        manager = DataFrameManager(temp_db_dir)
        
        # Load file
        excel_file1 = manager.load_excel_file("sample.xlsx")
        original_modified = excel_file1.last_modified
        
        # Wait a bit and modify file
        time.sleep(0.1)
        
        # Create new data and overwrite file
        new_df = pd.DataFrame({'new_col': [1, 2, 3]})
        new_df.to_excel(sample_excel_file, index=False)
        
        # Refresh cache
        manager.refresh_file_cache()
        
        # File should be reloaded
        excel_file2 = manager.loaded_files["sample.xlsx"]
        assert excel_file2.last_modified > original_modified
    
    def test_corrupted_file_in_directory(self, temp_db_dir):
        """Test handling corrupted files during directory scan."""
        manager = DataFrameManager(temp_db_dir)
        
        # Create a corrupted "Excel" file
        corrupted_file = temp_db_dir / "corrupted.xlsx"
        corrupted_file.write_bytes(b"This is not an Excel file")
        
        # Should not crash, just skip the corrupted file
        excel_files = manager.scan_db_directory()
        assert "corrupted.xlsx" not in excel_files
    
    def test_multiple_file_types(self, temp_db_dir):
        """Test handling multiple Excel file types."""
        manager = DataFrameManager(temp_db_dir)
        
        # Create different types of files
        df = pd.DataFrame({'col': [1, 2, 3]})
        
        # Create .xlsx file
        xlsx_file = temp_db_dir / "test.xlsx"
        df.to_excel(xlsx_file, index=False)
        
        # Create .xlsm file (macro-enabled)
        xlsm_file = temp_db_dir / "test.xlsm"
        df.to_excel(xlsm_file, index=False)
        
        # Scan directory
        excel_files = manager.scan_db_directory()
        
        # Should find both files
        assert "test.xlsx" in excel_files
        assert "test.xlsm" in excel_files
    
    def test_file_with_dots_in_name(self, temp_db_dir):
        """Test handling files with dots in their names."""
        manager = DataFrameManager(temp_db_dir)
        
        # Create file with dots in name
        df = pd.DataFrame({'col': [1, 2, 3]})
        file_with_dots = temp_db_dir / "file.with.dots.xlsx"
        df.to_excel(file_with_dots, index=False, sheet_name="sheet1")
        
        # Test table reference parsing
        file_name, sheet_name = manager.get_table_reference_info("file.with.dots.xlsx.sheet1")
        assert file_name == "file.with.dots.xlsx"
        assert sheet_name == "sheet1"
        
        # Test loading
        excel_file = manager.load_excel_file("file.with.dots.xlsx")
        assert excel_file.file_name == "file.with.dots.xlsx"