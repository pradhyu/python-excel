"""Jupyter notebook interface for Excel DataFrame Processor."""

import pandas as pd
from pathlib import Path
from typing import Union, Optional, Dict, Any
from IPython.display import display, HTML
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from IPython.core.magic_arguments import argument, magic_arguments
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic

from .dataframe_manager import DataFrameManager
from .sql_parser import SQLParser
from .exceptions import SQLSyntaxError, ExcelProcessorError


class ExcelProcessor:
    """Main interface for using Excel DataFrame Processor in notebooks and scripts."""
    
    def __init__(self, db_directory: Union[str, Path], memory_limit_mb: float = 1024.0):
        """Initialize the Excel processor.
        
        Args:
            db_directory: Path to directory containing Excel files
            memory_limit_mb: Memory limit in MB for loaded DataFrames
        """
        self.db_directory = Path(db_directory)
        self.df_manager = DataFrameManager(self.db_directory, memory_limit_mb)
        self.sql_parser = SQLParser()
        
    def query(self, sql: str, display_result: bool = True) -> pd.DataFrame:
        """Execute a SQL query and return the result as a DataFrame.
        
        Args:
            sql: SQL query string
            display_result: Whether to display the result in notebook
            
        Returns:
            pandas DataFrame with query results
        """
        try:
            # Parse the SQL query
            parsed_query = self.sql_parser.parse(sql)
            
            # For now, we'll implement basic SELECT functionality
            # Full query execution will be implemented in later tasks
            if parsed_query.from_node and len(parsed_query.from_node.tables) == 1:
                table_ref = parsed_query.from_node.tables[0]
                df = self.df_manager.get_dataframe(table_ref.file_name, table_ref.sheet_name)
                
                # Apply column selection
                if parsed_query.select_node and not parsed_query.select_node.is_wildcard:
                    columns = [str(col) for col in parsed_query.select_node.columns]
                    # Filter out columns that don't exist
                    available_columns = [col for col in columns if col in df.columns]
                    if available_columns:
                        df = df[available_columns]
                
                # Apply WHERE clause (basic implementation)
                if parsed_query.where_node:
                    conditions = parsed_query.where_node.where_clause.conditions
                    for condition in conditions:
                        if str(condition.left).upper() == 'ROWNUM':
                            if condition.operator in ['<', '<=']:
                                limit = int(condition.right)
                                df = df.head(limit)
                        elif str(condition.left) in df.columns:
                            if condition.operator == '>':
                                df = df[df[str(condition.left)] > condition.right]
                            elif condition.operator == '<':
                                df = df[df[str(condition.left)] < condition.right]
                            elif condition.operator == '=':
                                df = df[df[str(condition.left)] == condition.right]
                            elif condition.operator == '>=':
                                df = df[df[str(condition.left)] >= condition.right]
                            elif condition.operator == '<=':
                                df = df[df[str(condition.left)] <= condition.right]
                            elif condition.operator in ['!=', '<>']:
                                df = df[df[str(condition.left)] != condition.right]
                            elif condition.operator == 'IS':
                                if str(condition.right).upper() == 'NULL':
                                    df = df[df[str(condition.left)].isna()]
                            elif condition.operator == 'IS NOT':
                                if str(condition.right).upper() == 'NULL':
                                    df = df[df[str(condition.left)].notna()]
                
                # Apply ORDER BY
                if parsed_query.order_by_node:
                    order_clause = parsed_query.order_by_node.order_by_clause
                    for i, column in enumerate(order_clause.columns):
                        if column in df.columns:
                            ascending = order_clause.directions[i] == 'ASC' if i < len(order_clause.directions) else True
                            df = df.sort_values(by=column, ascending=ascending)
                

                
                # Handle CSV export
                if parsed_query.output_file:
                    output_path = Path(parsed_query.output_file)
                    df.to_csv(output_path, index=False)
                    print(f"✅ Exported {len(df)} rows to {output_path}")
                
                # Display result in notebook
                if display_result and not parsed_query.output_file:
                    self._display_dataframe(df, sql)
                
                return df
            else:
                raise NotImplementedError("Complex queries with joins not yet implemented in notebook interface")
                
        except Exception as e:
            if isinstance(e, (SQLSyntaxError, ExcelProcessorError)):
                raise
            else:
                raise ExcelProcessorError(f"Query execution failed: {str(e)}")
    
    def show_db(self) -> Dict[str, Any]:
        """Show all available Excel files and sheets."""
        db_info = self.df_manager.get_database_info()
        
        print(f"📁 Database Directory: {db_info.directory_path}")
        print(f"📄 Total Files: {db_info.total_files}")
        print(f"💾 Loaded Files: {db_info.loaded_files}")
        print()
        
        if db_info.excel_files:
            print("Available Files and Sheets:")
            for file_name, sheets in db_info.excel_files.items():
                print(f"  📄 {file_name}")
                for sheet in sheets:
                    print(f"    📋 {sheet}")
        else:
            print("No Excel files found in database directory.")
        
        return {
            'directory': db_info.directory_path,
            'total_files': db_info.total_files,
            'loaded_files': db_info.loaded_files,
            'files': db_info.excel_files
        }
    
    def load_db(self, show_progress: bool = True) -> Dict[str, Any]:
        """Load all Excel files in the database directory."""
        loaded_files = self.df_manager.load_all_db_files(show_progress=show_progress)
        
        total_memory = sum(f.memory_usage for f in loaded_files.values())
        print(f"\n✅ Loaded {len(loaded_files)} files ({total_memory:.2f} MB total)")
        
        return {
            'loaded_files': len(loaded_files),
            'total_memory_mb': total_memory,
            'files': list(loaded_files.keys())
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information."""
        return self.df_manager.get_memory_usage()
    
    def get_file_info(self, file_name: str) -> Dict[str, Any]:
        """Get information about a specific Excel file."""
        try:
            excel_file = self.df_manager.load_excel_file(file_name)
            return {
                'file_name': excel_file.file_name,
                'sheets': excel_file.get_sheet_names(),
                'memory_usage_mb': excel_file.memory_usage,
                'last_modified': excel_file.last_modified
            }
        except Exception as e:
            raise ExcelProcessorError(f"Failed to get file info: {str(e)}")
    
    def get_sheet_info(self, file_name: str, sheet_name: str) -> Dict[str, Any]:
        """Get information about a specific sheet."""
        try:
            df = self.df_manager.get_dataframe(file_name, sheet_name)
            column_info = self.df_manager.get_column_info(file_name, sheet_name)
            
            return {
                'shape': df.shape,
                'columns': list(df.columns),
                'column_types': column_info,
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024)
            }
        except Exception as e:
            raise ExcelProcessorError(f"Failed to get sheet info: {str(e)}")
    
    def _display_dataframe(self, df: pd.DataFrame, query: str = None):
        """Display DataFrame in notebook with rich formatting."""
        if len(df) == 0:
            print("📊 Query returned no results.")
            return
        
        # Show query info
        if query:
            print(f"📊 Query Results ({len(df)} rows × {len(df.columns)} columns)")
            print(f"🔍 Query: {query}")
            print()
        
        # Display the DataFrame (Jupyter will automatically format it nicely)
        display(df)
        
        # Show summary info
        if len(df) > 10:
            print(f"\n📈 Showing all {len(df)} rows")


@magics_class
class ExcelMagics(Magics):
    """IPython magic commands for Excel DataFrame Processor."""
    
    def __init__(self, shell=None, **kwargs):
        super().__init__(shell=shell, **kwargs)
        self.processor = None
    
    @line_magic
    def excel_init(self, line):
        """Initialize Excel processor with database directory.
        
        Usage: %excel_init --db /path/to/excel/files [--memory-limit 1024]
        """
        # Simple argument parsing
        parts = line.strip().split()
        db_path = None
        memory_limit = 1024.0
        
        i = 0
        while i < len(parts):
            if parts[i] == '--db' and i + 1 < len(parts):
                db_path = parts[i + 1]
                i += 2
            elif parts[i] == '--memory-limit' and i + 1 < len(parts):
                try:
                    memory_limit = float(parts[i + 1])
                except ValueError:
                    print(f"❌ Invalid memory limit: {parts[i + 1]}")
                    return
                i += 2
            else:
                i += 1
        
        if not db_path:
            print("❌ Error: --db parameter is required")
            print("Usage: %excel_init --db /path/to/excel/files [--memory-limit 1024]")
            return
        
        try:
            self.processor = ExcelProcessor(db_path, memory_limit)
            print(f"✅ Excel processor initialized with database: {db_path}")
            print(f"💾 Memory limit: {memory_limit} MB")
        except Exception as e:
            print(f"❌ Error initializing Excel processor: {e}")
    
    @line_magic
    def excel_show_db(self, line):
        """Show all available Excel files and sheets.
        
        Usage: %excel_show_db
        """
        if not self.processor:
            print("❌ Excel processor not initialized. Use %excel_init first.")
            return
        
        self.processor.show_db()
    
    @line_magic
    def excel_load_db(self, line):
        """Load all Excel files into memory.
        
        Usage: %excel_load_db
        """
        if not self.processor:
            print("❌ Excel processor not initialized. Use %excel_init first.")
            return
        
        self.processor.load_db()
    
    @cell_magic
    def excel_sql(self, line, cell):
        """Execute SQL query on Excel files.
        
        Usage: 
        %%excel_sql
        SELECT * FROM employees.staff WHERE salary > 70000
        """
        if not self.processor:
            print("❌ Excel processor not initialized. Use %excel_init first.")
            return
        
        try:
            result = self.processor.query(cell.strip())
            return result
        except Exception as e:
            print(f"❌ Query error: {e}")
            return None
    
    @line_magic
    def excel_memory(self, line):
        """Show current memory usage.
        
        Usage: %excel_memory
        """
        if not self.processor:
            print("❌ Excel processor not initialized. Use %excel_init first.")
            return
        
        usage = self.processor.get_memory_usage()
        print(f"💾 Memory Usage:")
        print(f"  Total: {usage['total_mb']:.2f} MB")
        print(f"  Limit: {usage['limit_mb']:.2f} MB")
        print(f"  Usage: {usage['usage_percent']:.1f}%")
        print(f"  Files loaded: {len(usage['files'])}")


def load_ipython_extension(ipython):
    """Load the Excel magic commands in IPython/Jupyter."""
    magics = ExcelMagics(ipython)
    ipython.register_magic_function(magics.excel_init, 'line', 'excel_init')
    ipython.register_magic_function(magics.excel_show_db, 'line', 'excel_show_db')
    ipython.register_magic_function(magics.excel_load_db, 'line', 'excel_load_db')
    ipython.register_magic_function(magics.excel_sql, 'cell', 'excel_sql')
    ipython.register_magic_function(magics.excel_memory, 'line', 'excel_memory')


def unload_ipython_extension(ipython):
    """Unload the Excel magic commands."""
    pass