"""DataFrame manager for handling Excel files in database directory."""

import os
import glob
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import pandas as pd
from datetime import datetime

from .excel_loader import ExcelLoader
from .models import ExcelFile, DatabaseInfo
from .sqlite_cache import SQLiteCache
from .exceptions import (
    DatabaseDirectoryError, 
    TableNotFoundError, 
    FileLoadError,
    MemoryError as ProcessorMemoryError
)


class DataFrameManager:
    """Manages Excel files and DataFrames within a database directory."""
    
    def __init__(self, db_directory: Union[str, Path], memory_limit_mb: float = 1024.0, 
                 use_sqlite_cache: bool = True, cache_dir: Optional[str] = None):
        """Initialize DataFrame manager with database directory.
        
        Args:
            db_directory: Path to directory containing Excel files
            memory_limit_mb: Memory limit in MB for loaded DataFrames
            use_sqlite_cache: Enable SQLite caching for faster queries
            cache_dir: Custom cache directory (default: .excel_cache in db_directory)
        """
        self.db_directory = Path(db_directory)
        self.memory_limit_mb = memory_limit_mb
        self.excel_loader = ExcelLoader()
        self.loaded_files: Dict[str, ExcelFile] = {}
        self._file_cache: Dict[str, datetime] = {}  # filename -> last_modified
        self.temp_tables: Dict[str, pd.DataFrame] = {}  # In-memory temporary tables
        
        # Initialize SQLite cache
        if cache_dir is None:
            cache_dir = str(self.db_directory / '.excel_cache')
        self.sqlite_cache = SQLiteCache(cache_dir=cache_dir, enabled=use_sqlite_cache)
        self.use_sqlite_cache = use_sqlite_cache
        
        # Validate database directory
        if not self.db_directory.exists():
            raise DatabaseDirectoryError(
                str(self.db_directory),
                "Database directory does not exist"
            )
        
        if not self.db_directory.is_dir():
            raise DatabaseDirectoryError(
                str(self.db_directory),
                "Database path is not a directory"
            )
    
    def scan_db_directory(self) -> Dict[str, List[str]]:
        """Scan database directory for Excel files and return file -> sheets mapping."""
        excel_files = {}
        
        # Supported file patterns (Excel and CSV)
        patterns = ['*.xlsx', '*.xls', '*.xlsm', '*.xlsb', '*.csv']
        
        for pattern in patterns:
            for file_path in self.db_directory.glob(pattern):
                if file_path.is_file():
                    try:
                        sheet_names = self.excel_loader.get_sheet_names(file_path)
                        excel_files[file_path.name] = sheet_names
                    except FileLoadError as e:
                        # Log warning but continue scanning
                        print(f"Warning: Could not read sheets from {file_path.name}: {e.message}")
                        continue
        
        return excel_files
    
    def get_database_info(self) -> DatabaseInfo:
        """Get information about the database directory."""
        excel_files = self.scan_db_directory()
        
        return DatabaseInfo(
            directory_path=str(self.db_directory),
            excel_files=excel_files,
            total_files=len(excel_files),
            loaded_files=len(self.loaded_files),
            temp_tables=list(self.temp_tables.keys())
        )
    
    def list_all_files_and_sheets(self) -> Dict[str, List[str]]:
        """List all Excel files and their sheets in the database directory."""
        return self.scan_db_directory()
    
    def get_file_path(self, file_name: str) -> Path:
        """Get full path for a file in the database directory."""
        file_path = self.db_directory / file_name
        
        # Also try without extension if not found
        if not file_path.exists():
            # Try adding common file extensions
            for ext in ['.xlsx', '.xls', '.xlsm', '.xlsb', '.csv']:
                test_path = self.db_directory / f"{file_name}{ext}"
                if test_path.exists():
                    return test_path
        
        return file_path
    
    def load_excel_file(self, file_name: str, force_reload: bool = False) -> ExcelFile:
        """Load an Excel file and return ExcelFile model.
        
        Args:
            file_name: Name of the Excel file (with or without extension)
            force_reload: Force reload even if already cached
            
        Returns:
            ExcelFile model with loaded sheets
        """
        file_path = self.get_file_path(file_name)
        
        if not file_path.exists():
            raise TableNotFoundError(file_name)
        
        # Check if file is already loaded and up-to-date
        if not force_reload and file_name in self.loaded_files:
            cached_file = self.loaded_files[file_name]
            current_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            if cached_file.last_modified >= current_modified:
                return cached_file
        
        # Check memory limit before loading
        current_memory = self.get_memory_usage()
        if current_memory['total_mb'] > self.memory_limit_mb * 0.8:  # 80% threshold
            print(f"Warning: Memory usage ({current_memory['total_mb']:.2f} MB) approaching limit ({self.memory_limit_mb} MB)")
        
        try:
            # Load the Excel file
            excel_file = self.excel_loader.create_excel_file_model(file_path, self.db_directory)
            
            # Check if loading this file would exceed memory limit
            total_memory = current_memory['total_mb'] + excel_file.memory_usage
            if total_memory > self.memory_limit_mb:
                raise ProcessorMemoryError(
                    total_memory,
                    self.memory_limit_mb,
                    f"loading file '{file_name}'"
                )
            
            # Cache to SQLite if enabled
            if self.use_sqlite_cache and not self.sqlite_cache.is_cached(file_path):
                print(f"  📦 Caching {file_name} to SQLite for faster queries...")
                self.sqlite_cache.cache_file(file_path, excel_file.sheets)
            
            # Cache the loaded file
            self.loaded_files[file_name] = excel_file
            self._file_cache[file_name] = excel_file.last_modified
            
            return excel_file
        
        except (FileLoadError, ProcessorMemoryError):
            raise
        except Exception as e:
            raise FileLoadError(
                str(file_path),
                f"Failed to load Excel file '{file_name}'",
                str(e)
            )
    
    def get_dataframe(self, file_name: str, sheet_name: Union[str, int]) -> pd.DataFrame:
        """Get a specific DataFrame from a file and sheet, or from temporary tables.
        
        Args:
            file_name: Name of the Excel file or temporary table
            sheet_name: Name or index of the sheet
            
        Returns:
            pandas DataFrame
        """
        # Check if this is a temporary table reference
        if file_name in self.temp_tables:
            return self.temp_tables[file_name]
        
        # Load the file if not already loaded
        excel_file = self.load_excel_file(file_name)
        
        # Get the specific sheet
        df = excel_file.get_sheet(sheet_name)
        if df is None:
            available_sheets = excel_file.get_sheet_names()
            if isinstance(sheet_name, int):
                raise TableNotFoundError(
                    file_name, 
                    f"sheet index {sheet_name} (available: 0-{len(available_sheets)-1})"
                )
            else:
                raise TableNotFoundError(
                    file_name,
                    f"sheet '{sheet_name}' (available: {', '.join(available_sheets)})"
                )
        
        return df
    
    def load_all_db_files(self, show_progress: bool = True) -> Dict[str, ExcelFile]:
        """Load all Excel files in the database directory.
        
        Args:
            show_progress: Whether to show loading progress
            
        Returns:
            Dictionary of file_name -> ExcelFile
        """
        excel_files = self.scan_db_directory()
        loaded_files = {}
        errors = []
        
        if show_progress:
            print(f"Loading {len(excel_files)} Excel files from {self.db_directory}")
        
        for i, (file_name, sheet_names) in enumerate(excel_files.items(), 1):
            try:
                if show_progress:
                    print(f"  [{i}/{len(excel_files)}] Loading {file_name} ({len(sheet_names)} sheets)...")
                
                excel_file = self.load_excel_file(file_name)
                loaded_files[file_name] = excel_file
                
                if show_progress:
                    print(f"    ✓ Loaded {len(excel_file.sheets)} sheets ({excel_file.memory_usage:.2f} MB)")
            
            except Exception as e:
                error_msg = f"Failed to load {file_name}: {str(e)}"
                errors.append(error_msg)
                if show_progress:
                    print(f"    ✗ {error_msg}")
                continue
        
        if show_progress:
            total_memory = sum(f.memory_usage for f in loaded_files.values())
            print(f"\nLoaded {len(loaded_files)} files successfully ({total_memory:.2f} MB total)")
            
            if errors:
                print(f"Failed to load {len(errors)} files:")
                for error in errors:
                    print(f"  - {error}")
        
        return loaded_files
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage information.
        
        Returns:
            Dictionary with memory usage details
        """
        file_usage = {}
        total_mb = 0.0
        
        for file_name, excel_file in self.loaded_files.items():
            file_usage[file_name] = excel_file.memory_usage
            total_mb += excel_file.memory_usage
        
        return {
            'total_mb': total_mb,
            'limit_mb': self.memory_limit_mb,
            'usage_percent': (total_mb / self.memory_limit_mb) * 100 if self.memory_limit_mb > 0 else 0,
            'files': file_usage
        }
    
    def clear_cache(self, file_name: Optional[str] = None) -> None:
        """Clear cached DataFrames and SQLite cache.
        
        Args:
            file_name: Specific file to clear, or None to clear all
        """
        if file_name:
            if file_name in self.loaded_files:
                del self.loaded_files[file_name]
            if file_name in self._file_cache:
                del self._file_cache[file_name]
            # Clear SQLite cache
            if self.use_sqlite_cache:
                self.sqlite_cache.clear_cache(file_name)
        else:
            self.loaded_files.clear()
            self._file_cache.clear()
            # Clear all SQLite cache
            if self.use_sqlite_cache:
                self.sqlite_cache.clear_cache()
    
    def get_column_info(self, file_name: str, sheet_name: Union[str, int]) -> Dict[str, str]:
        """Get column information for a specific sheet.
        
        Args:
            file_name: Name of the Excel file
            sheet_name: Name or index of the sheet
            
        Returns:
            Dictionary mapping column names to data types
        """
        df = self.get_dataframe(file_name, sheet_name)
        
        column_info = {}
        for column in df.columns:
            dtype = str(df[column].dtype)
            # Simplify dtype names for readability
            if 'int' in dtype:
                dtype = 'integer'
            elif 'float' in dtype:
                dtype = 'float'
            elif 'datetime' in dtype:
                dtype = 'datetime'
            elif 'bool' in dtype:
                dtype = 'boolean'
            elif dtype == 'category':
                dtype = 'category'
            else:
                dtype = 'text'
            
            column_info[column] = dtype
        
        return column_info
    
    def refresh_file_cache(self) -> None:
        """Refresh the file cache by checking for modified files."""
        files_to_reload = []
        
        for file_name in list(self.loaded_files.keys()):
            file_path = self.get_file_path(file_name)
            
            if not file_path.exists():
                # File was deleted
                self.clear_cache(file_name)
                continue
            
            current_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            cached_modified = self._file_cache.get(file_name)
            
            if cached_modified is None or current_modified > cached_modified:
                files_to_reload.append(file_name)
        
        # Reload modified files
        for file_name in files_to_reload:
            try:
                self.load_excel_file(file_name, force_reload=True)
                print(f"Reloaded modified file: {file_name}")
            except Exception as e:
                print(f"Failed to reload {file_name}: {e}")
                self.clear_cache(file_name)
    
    def get_table_reference_info(self, table_ref: str) -> Tuple[str, str]:
        """Parse table reference in format 'file.sheet' and return file_name, sheet_name.
        
        Args:
            table_ref: Table reference in format 'file.sheet' or 'file.xlsx.sheet'
            
        Returns:
            Tuple of (file_name, sheet_name)
        """
        if '.' not in table_ref:
            raise ValueError(f"Invalid table reference '{table_ref}'. Expected format: 'file.sheet'")
        
        # Split on the last dot to handle files with dots in names
        parts = table_ref.rsplit('.', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid table reference '{table_ref}'. Expected format: 'file.sheet'")
        
        file_part, sheet_name = parts
        
        # Check if file_part already has an extension
        file_path = self.get_file_path(file_part)
        if file_path.exists():
            return file_path.name, sheet_name  # Return the actual filename found
        
        # Try with common extensions
        for ext in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
            test_name = f"{file_part}{ext}"
            test_path = self.get_file_path(test_name)
            if test_path.exists():
                return test_path.name, sheet_name  # Return the actual filename found
        
        # Return original if no file found (will raise error later)
        return file_part, sheet_name
    
    def create_temp_table(self, table_name: str, df: pd.DataFrame) -> None:
        """Create a temporary in-memory table.
        
        Args:
            table_name: Name of the temporary table
            df: DataFrame to store as temporary table
        """
        self.temp_tables[table_name] = df.copy()
    
    def get_temp_table(self, table_name: str) -> Optional[pd.DataFrame]:
        """Get a temporary table by name.
        
        Args:
            table_name: Name of the temporary table
            
        Returns:
            DataFrame if found, None otherwise
        """
        return self.temp_tables.get(table_name)
    
    def list_temp_tables(self) -> List[str]:
        """List all temporary table names.
        
        Returns:
            List of temporary table names
        """
        return list(self.temp_tables.keys())
    
    def drop_temp_table(self, table_name: str) -> bool:
        """Drop a temporary table.
        
        Args:
            table_name: Name of the temporary table to drop
            
        Returns:
            True if table was dropped, False if not found
        """
        if table_name in self.temp_tables:
            del self.temp_tables[table_name]
            return True
        return False
    
    def clear_temp_tables(self) -> None:
        """Clear all temporary tables."""
        self.temp_tables.clear()
    
    def validate_table_reference(self, table_ref: str) -> bool:
        """Validate that a table reference exists.
        
        Args:
            table_ref: Table reference in format 'file.sheet'
            
        Returns:
            True if table reference is valid
        """
        try:
            file_name, sheet_name = self.get_table_reference_info(table_ref)
            df = self.get_dataframe(file_name, sheet_name)
            return True
        except:
            return False
 
   
    def get_cache_stats(self) -> Dict:
        """Get SQLite cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.use_sqlite_cache:
            return {'enabled': False}
        
        return self.sqlite_cache.get_cache_stats()
    
    def query_with_cache(self, file_name: str, sheet_name: str, sql_query: str) -> Optional[pd.DataFrame]:
        """
        Execute query using SQLite cache if available, fallback to DataFrame.
        
        Args:
            file_name: Excel file name
            sheet_name: Sheet name
            sql_query: SQL query to execute
            
        Returns:
            DataFrame with results
        """
        if self.use_sqlite_cache:
            # Try cache first
            result = self.sqlite_cache.query(file_name, sheet_name, sql_query)
            if result is not None:
                return result
        
        # Fallback to loading DataFrame
        return None
