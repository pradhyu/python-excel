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
            
            # Handle CREATE TABLE AS statements
            if parsed_query.query_type == "CREATE_TABLE_AS":
                return self._execute_create_table_as(parsed_query, display_result)
            
            # For now, we'll implement basic SELECT functionality
            # Full query execution will be implemented in later tasks
            if parsed_query.from_node and len(parsed_query.from_node.tables) == 1:
                table_ref = parsed_query.from_node.tables[0]
                
                # Check if this is a temporary table (no sheet name)
                if table_ref.sheet_name == "":
                    # This is a temporary table
                    temp_df = self.df_manager.get_temp_table(table_ref.file_name)
                    if temp_df is None:
                        raise ExcelProcessorError(f"Temporary table '{table_ref.file_name}' not found")
                    df = temp_df
                else:
                    # Load the DataFrame from Excel file
                    df = self.df_manager.get_dataframe(table_ref.file_name, table_ref.sheet_name)
                
                # Handle GROUP BY queries differently
                if parsed_query.group_by_node:
                    df = self._execute_group_by_query(df, parsed_query)
                else:
                    # Check if we have window functions in SELECT
                    has_window_functions = False
                    if parsed_query.select_node:
                        from .sql_ast import WindowFunctionNode
                        for col in parsed_query.select_node.columns:
                            if isinstance(col, WindowFunctionNode):
                                has_window_functions = True
                                break
                    
                    if has_window_functions:
                        df = self._execute_window_functions(df, parsed_query)
                    else:
                        # Apply column selection for non-GROUP BY, non-window queries
                        if parsed_query.select_node and not parsed_query.select_node.is_wildcard:
                            df = self._apply_column_selection(df, parsed_query.select_node.columns)
                
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
    
    def _execute_create_table_as(self, parsed_query, display_result: bool = True) -> pd.DataFrame:
        """Execute a CREATE TABLE AS statement in notebook.
        
        Args:
            parsed_query: Parsed CREATE TABLE AS query
            display_result: Whether to display the result
            
        Returns:
            DataFrame with the created table data
        """
        create_node = parsed_query.create_table_as_node
        table_name = create_node.table_name
        select_query = create_node.select_query
        
        # Execute the SELECT query to get the data
        result_df = self.query(str(select_query), display_result=False)
        
        # Store as temporary table
        self.df_manager.create_temp_table(table_name, result_df)
        
        # Display success message
        if display_result:
            print(f"✅ Created temporary table '{table_name}' with {len(result_df)} rows and {len(result_df.columns)} columns")
            self._display_dataframe(result_df, f"CREATE TABLE {table_name} AS ...")
        
        return result_df
    
    def _execute_group_by_query(self, df: pd.DataFrame, parsed_query) -> pd.DataFrame:
        """Execute a GROUP BY query with aggregation functions.
        
        Args:
            df: Source DataFrame
            parsed_query: Parsed SQL query with GROUP BY
            
        Returns:
            DataFrame with aggregated results
        """
        from .sql_ast import AggregateFunctionNode
        
        group_columns = parsed_query.group_by_node.columns
        select_columns = parsed_query.select_node.columns
        
        # Validate group columns exist
        for col in group_columns:
            if col not in df.columns:
                raise ExcelProcessorError(f"GROUP BY column '{col}' not found in table")
        
        # Separate aggregate functions from regular columns
        agg_functions = {}
        regular_columns = []
        
        for col in select_columns:
            if isinstance(col, AggregateFunctionNode):
                # Handle aggregate function
                func_name = col.function_name.lower()
                target_col = col.column
                
                if target_col == '*' and func_name == 'count':
                    # COUNT(*) - count rows
                    agg_functions['count'] = 'size'
                elif target_col in df.columns:
                    # Map SQL functions to pandas functions
                    if func_name == 'count':
                        agg_functions[f"{func_name}_{target_col}"] = (target_col, 'count')
                    elif func_name == 'sum':
                        agg_functions[f"{func_name}_{target_col}"] = (target_col, 'sum')
                    elif func_name == 'avg':
                        agg_functions[f"avg_{target_col}"] = (target_col, 'mean')
                    elif func_name == 'min':
                        agg_functions[f"{func_name}_{target_col}"] = (target_col, 'min')
                    elif func_name == 'max':
                        agg_functions[f"{func_name}_{target_col}"] = (target_col, 'max')
                    elif func_name == 'stddev':
                        agg_functions[f"stddev_{target_col}"] = (target_col, 'std')
                    elif func_name == 'variance':
                        agg_functions[f"variance_{target_col}"] = (target_col, 'var')
                else:
                    raise ExcelProcessorError(f"Column '{target_col}' not found for {func_name.upper()} function")
            else:
                # Regular column - must be in GROUP BY
                col_str = str(col)
                if col_str not in group_columns:
                    raise ExcelProcessorError(f"Column '{col_str}' must be in GROUP BY clause or be an aggregate function")
                regular_columns.append(col_str)
        
        # Perform grouping and aggregation
        if agg_functions:
            # Build aggregation dictionary for pandas
            pandas_agg = {}
            result_columns = group_columns.copy()
            
            for agg_name, agg_spec in agg_functions.items():
                if agg_spec == 'size':
                    # COUNT(*) - handle separately
                    continue
                else:
                    col_name, func_name = agg_spec
                    if col_name not in pandas_agg:
                        pandas_agg[col_name] = []
                    pandas_agg[col_name].append(func_name)
                    result_columns.append(agg_name)
            
            # Perform aggregation
            if pandas_agg:
                result_df = df.groupby(group_columns, observed=False).agg(pandas_agg).reset_index()
                
                # Flatten column names
                new_columns = group_columns.copy()
                for col in result_df.columns[len(group_columns):]:
                    if isinstance(col, tuple):
                        # Find the corresponding agg_name
                        col_name, func_name = col
                        for agg_name, agg_spec in agg_functions.items():
                            if agg_spec != 'size':
                                target_col, target_func = agg_spec
                                if target_col == col_name and target_func == func_name:
                                    new_columns.append(agg_name)
                                    break
                        else:
                            new_columns.append(f"{func_name}_{col_name}")
                    else:
                        new_columns.append(str(col))
                
                result_df.columns = new_columns
            else:
                result_df = df.groupby(group_columns, observed=False).first().reset_index()
            
            # Add COUNT(*) if present
            if 'count' in agg_functions and agg_functions['count'] == 'size':
                count_df = df.groupby(group_columns, observed=False).size().reset_index(name='count')
                if len(result_df) == 0:
                    result_df = count_df
                else:
                    result_df = result_df.merge(count_df, on=group_columns)
        else:
            # No aggregation functions, just grouping (like DISTINCT)
            result_df = df.groupby(group_columns, observed=False).first().reset_index()
        
        # Apply HAVING clause if present
        if parsed_query.having_node:
            # Apply HAVING conditions (similar to WHERE but on aggregated data)
            conditions = parsed_query.having_node.where_clause.conditions
            for condition in conditions:
                col_name = str(condition.left)
                if col_name in result_df.columns:
                    if condition.operator == '>':
                        result_df = result_df[result_df[col_name] > condition.right]
                    elif condition.operator == '<':
                        result_df = result_df[result_df[col_name] < condition.right]
                    elif condition.operator == '=':
                        result_df = result_df[result_df[col_name] == condition.right]
                    elif condition.operator == '>=':
                        result_df = result_df[result_df[col_name] >= condition.right]
                    elif condition.operator == '<=':
                        result_df = result_df[result_df[col_name] <= condition.right]
                    elif condition.operator in ['!=', '<>']:
                        result_df = result_df[result_df[col_name] != condition.right]
        
        return result_df
    
    def _execute_window_functions(self, df: pd.DataFrame, parsed_query) -> pd.DataFrame:
        """Execute window functions in SELECT clause."""
        from .sql_ast import WindowFunctionNode
        
        result_df = df.copy()
        select_columns = []
        
        for col in parsed_query.select_node.columns:
            if isinstance(col, WindowFunctionNode):
                # Execute window function
                window_result = self._calculate_window_function(result_df, col)
                
                # Add the result as a new column
                col_name = f"{col.function_name.lower()}"
                if col.column:
                    col_name += f"_{col.column}"
                
                result_df[col_name] = window_result
                select_columns.append(col_name)
            else:
                # Regular column
                col_str = str(col)
                if col_str == '*':
                    # Add all existing columns
                    select_columns.extend(result_df.columns.tolist())
                elif col_str in result_df.columns:
                    select_columns.append(col_str)
        
        # Select only the requested columns
        if select_columns:
            # Remove duplicates while preserving order
            unique_columns = []
            for col in select_columns:
                if col not in unique_columns:
                    unique_columns.append(col)
            result_df = result_df[unique_columns]
        
        return result_df
    
    def _calculate_window_function(self, df: pd.DataFrame, window_func):
        """Calculate a single window function."""
        func_name = window_func.function_name
        column = window_func.column
        partition_by = window_func.partition_by
        order_by = window_func.order_by
        order_directions = window_func.order_directions
        
        # Prepare grouping and sorting
        if partition_by:
            # Validate partition columns exist
            for col in partition_by:
                if col not in df.columns:
                    raise ExcelProcessorError(f"PARTITION BY column '{col}' not found")
        
        if order_by:
            # Validate order columns exist
            for col in order_by:
                if col not in df.columns:
                    raise ExcelProcessorError(f"ORDER BY column '{col}' not found")
        
        # Calculate window function (same logic as REPL)
        if func_name == 'ROW_NUMBER':
            if partition_by:
                if order_by:
                    ascending = [direction == 'ASC' for direction in order_directions]
                    result = df.sort_values(order_by, ascending=ascending).groupby(partition_by).cumcount() + 1
                else:
                    result = df.groupby(partition_by).cumcount() + 1
            else:
                if order_by:
                    ascending = [direction == 'ASC' for direction in order_directions]
                    sorted_df = df.sort_values(order_by, ascending=ascending)
                    result = pd.Series(range(1, len(df) + 1), index=sorted_df.index)
                    result = result.reindex(df.index)
                else:
                    result = pd.Series(range(1, len(df) + 1), index=df.index)
        
        elif func_name == 'RANK':
            if not order_by:
                raise ExcelProcessorError("RANK() requires ORDER BY clause")
            
            ascending = [direction == 'ASC' for direction in order_directions]
            
            if partition_by:
                def rank_group(group):
                    return group[order_by].rank(method='min', ascending=ascending[0] if len(ascending) == 1 else ascending)
                
                result = df.groupby(partition_by).apply(rank_group).reset_index(level=0, drop=True)
            else:
                result = df[order_by].rank(method='min', ascending=ascending[0] if len(ascending) == 1 else ascending)
        
        elif func_name == 'LAG':
            if not column or column not in df.columns:
                raise ExcelProcessorError(f"LAG() requires a valid column name")
            
            if partition_by:
                if order_by:
                    ascending = [direction == 'ASC' for direction in order_directions]
                    sorted_df = df.sort_values(partition_by + order_by, ascending=[True] * len(partition_by) + ascending)
                    result = sorted_df.groupby(partition_by)[column].shift(1)
                    result = result.reindex(df.index)
                else:
                    result = df.groupby(partition_by)[column].shift(1)
            else:
                if order_by:
                    ascending = [direction == 'ASC' for direction in order_directions]
                    sorted_df = df.sort_values(order_by, ascending=ascending)
                    result = sorted_df[column].shift(1)
                    result = result.reindex(df.index)
                else:
                    result = df[column].shift(1)
        
        else:
            raise ExcelProcessorError(f"Window function '{func_name}' not implemented")
        
        return result
    
    def _apply_column_selection(self, df: pd.DataFrame, columns) -> pd.DataFrame:
        """Apply column selection with support for aliases and quoted names."""
        from .sql_ast import ColumnReference, AggregateFunctionNode, WindowFunctionNode, ColumnAliasNode
        
        result_data = {}
        
        for col in columns:
            if isinstance(col, ColumnAliasNode):
                # Handle column alias (expression AS alias)
                expression = col.expression
                alias = col.alias
                
                if isinstance(expression, ColumnReference):
                    original_name = expression.column_name
                elif isinstance(expression, str):
                    original_name = expression
                else:
                    original_name = str(expression)
                
                if original_name in df.columns:
                    result_data[alias] = df[original_name]
                else:
                    # Try to find column with case-insensitive match
                    matched_col = None
                    for df_col in df.columns:
                        if df_col.lower() == original_name.lower():
                            matched_col = df_col
                            break
                    if matched_col:
                        result_data[alias] = df[matched_col]
            elif isinstance(col, ColumnReference):
                # Handle column reference with possible alias
                original_name = col.column_name
                alias = col.alias or original_name
                
                if original_name in df.columns:
                    result_data[alias] = df[original_name]
                else:
                    # Try to find column with case-insensitive match
                    matched_col = None
                    for df_col in df.columns:
                        if df_col.lower() == original_name.lower():
                            matched_col = df_col
                            break
                    if matched_col:
                        result_data[alias] = df[matched_col]
            elif isinstance(col, (AggregateFunctionNode, WindowFunctionNode)):
                # These should be handled elsewhere, but include for completeness
                pass
            else:
                # Regular string column name
                col_str = str(col)
                if col_str in df.columns:
                    result_data[col_str] = df[col_str]
                else:
                    # Try case-insensitive match
                    matched_col = None
                    for df_col in df.columns:
                        if df_col.lower() == col_str.lower():
                            matched_col = df_col
                            break
                    if matched_col:
                        result_data[col_str] = df[matched_col]
        
        # Create new DataFrame with selected columns
        if result_data:
            return pd.DataFrame(result_data)
        
        return df
    
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
        
        # Show temporary tables if any exist
        temp_tables = self.df_manager.list_temp_tables()
        if temp_tables:
            print("\n💾 In-Memory Temporary Tables:")
            for table_name in temp_tables:
                temp_df = self.df_manager.get_temp_table(table_name)
                if temp_df is not None:
                    print(f"  📋 {table_name} ({len(temp_df)} rows × {len(temp_df.columns)} columns)")
        
        return {
            'directory': db_info.directory_path,
            'total_files': db_info.total_files,
            'loaded_files': db_info.loaded_files,
            'files': db_info.excel_files,
            'temp_tables': temp_tables
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