"""REPL interface for Excel DataFrame Processor."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.shortcuts import confirm
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
import pandas as pd

from .dataframe_manager import DataFrameManager
from .sql_parser import SQLParser
from .exceptions import SQLSyntaxError, ExcelProcessorError, DatabaseDirectoryError


class SQLCompleter(Completer):
    """Custom completer for SQL queries with Excel context."""
    
    def __init__(self, df_manager: DataFrameManager):
        self.df_manager = df_manager
        self.sql_keywords = [
            'SELECT', 'FROM', 'WHERE', 'ORDER', 'BY', 'GROUP', 'HAVING',
            'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL',
            'ASC', 'DESC', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
            'INNER', 'LEFT', 'RIGHT', 'JOIN', 'ON', 'AS', 'CREATE', 'TABLE'
        ]
        self.operators = ['=', '!=', '<>', '<', '>', '<=', '>=', 'LIKE', 'IN', 'IS', 'IS NOT']
        
    def get_completions(self, document: Document, complete_event):
        """Generate completions based on current context."""
        text = document.text
        word_before_cursor = document.get_word_before_cursor()
        text_before_cursor = document.text_before_cursor
        
        # Get available tables and columns
        try:
            tables_info = self._get_tables_and_columns()
        except:
            tables_info = {}
        
        # Determine context
        context = self._determine_context(text_before_cursor)
        
        if context == 'table':
            # Complete table names (file.sheet format)
            for table_name in tables_info.keys():
                if table_name.lower().startswith(word_before_cursor.lower()):
                    yield Completion(table_name, start_position=-len(word_before_cursor))
        
        elif context == 'column':
            # Complete column names from available tables
            columns = set()
            for table_columns in tables_info.values():
                columns.update(table_columns.keys())
            
            for column in columns:
                if column.lower().startswith(word_before_cursor.lower()):
                    yield Completion(column, start_position=-len(word_before_cursor))
        
        elif context == 'value':
            # Check if we're after IS or IS NOT - suggest NULL
            if text_before_cursor.upper().endswith(' IS ') or text_before_cursor.upper().endswith(' IS NOT '):
                if 'NULL'.lower().startswith(word_before_cursor.lower()):
                    yield Completion('NULL', start_position=-len(word_before_cursor))
            else:
                # Complete values based on column context
                column_name = self._get_column_from_where_context(text_before_cursor)
                if column_name:
                    values = self._get_column_values(column_name, tables_info)
                    for value in values:
                        value_str = f"'{value}'" if isinstance(value, str) else str(value)
                        if value_str.lower().startswith(word_before_cursor.lower()):
                            yield Completion(value_str, start_position=-len(word_before_cursor))
        
        else:
            # Default: complete SQL keywords
            for keyword in self.sql_keywords:
                if keyword.lower().startswith(word_before_cursor.lower()):
                    yield Completion(keyword, start_position=-len(word_before_cursor))
    
    def _determine_context(self, text_before_cursor: str) -> str:
        """Determine what type of completion is needed based on context."""
        text_upper = text_before_cursor.upper()
        
        # Check if we're after FROM
        if 'FROM' in text_upper:
            from_pos = text_upper.rfind('FROM')
            after_from = text_before_cursor[from_pos + 4:].strip()
            
            # If we're right after FROM or after a comma, suggest table names
            if not after_from or after_from.endswith(','):
                return 'table'
        
        # Check if we're in a WHERE clause
        if 'WHERE' in text_upper:
            where_pos = text_upper.rfind('WHERE')
            after_where = text_before_cursor[where_pos + 5:].strip()
            
            # If we just typed an operator, suggest values
            for op in self.operators:
                if after_where.endswith(f' {op} ') or after_where.endswith(f' {op}'):
                    return 'value'
            
            # Otherwise suggest column names
            return 'column'
        
        # Check if we're in SELECT clause
        if 'SELECT' in text_upper and 'FROM' not in text_upper:
            return 'column'
        
        return 'keyword'
    
    def _get_tables_and_columns(self) -> Dict[str, Dict[str, str]]:
        """Get all available tables and their columns."""
        tables_info = {}
        
        try:
            files_and_sheets = self.df_manager.list_all_files_and_sheets()
            
            for file_name, sheet_names in files_and_sheets.items():
                for sheet_name in sheet_names:
                    table_name = f"{file_name.replace('.xlsx', '').replace('.xls', '')}.{sheet_name}"
                    try:
                        column_info = self.df_manager.get_column_info(file_name, sheet_name)
                        tables_info[table_name] = column_info
                    except:
                        continue
        except:
            pass
        
        return tables_info
    
    def _get_column_from_where_context(self, text_before_cursor: str) -> Optional[str]:
        """Extract column name from WHERE clause context."""
        text_upper = text_before_cursor.upper()
        
        if 'WHERE' not in text_upper:
            return None
        
        where_pos = text_upper.rfind('WHERE')
        after_where = text_before_cursor[where_pos + 5:].strip()
        
        # Look for pattern: column_name operator (with space after operator)
        for op in self.operators:
            pattern = f' {op} '
            if pattern in after_where.upper():
                parts = after_where.split()
                # Find the operator position
                for i, part in enumerate(parts):
                    if part.upper() == op:
                        if i > 0:
                            return parts[i-1]  # Return the column name before the operator
        
        # Also check for operators without spaces (like =)
        for op in ['=', '!=', '<>', '<', '>', '<=', '>=']:
            if op in after_where:
                op_pos = after_where.find(op)
                if op_pos > 0:
                    column_part = after_where[:op_pos].strip()
                    if column_part:
                        return column_part
        
        return None
    
    def _get_column_values(self, column_name: str, tables_info: Dict[str, Dict[str, str]]) -> list:
        """Get unique values for a column from loaded tables."""
        values = set()
        
        for table_name, columns in tables_info.items():
            if column_name in columns:
                try:
                    # Parse table name to get file and sheet
                    if '.' in table_name:
                        file_part, sheet_name = table_name.rsplit('.', 1)
                        file_name, _ = self.df_manager.get_table_reference_info(table_name)
                        
                        df = self.df_manager.get_dataframe(file_name, sheet_name)
                        if column_name in df.columns:
                            unique_values = df[column_name].dropna().unique()
                            # Limit to reasonable number of values
                            for val in list(unique_values)[:20]:
                                if pd.notna(val):
                                    values.add(val)
                except:
                    continue
        
        return sorted(list(values))


class ExcelREPL:
    """Interactive REPL for Excel DataFrame Processor."""
    
    def __init__(self, db_directory: Path, memory_limit_mb: float = 1024.0):
        """Initialize the REPL.
        
        Args:
            db_directory: Path to directory containing Excel files
            memory_limit_mb: Memory limit in MB for loaded DataFrames
        """
        self.db_directory = Path(db_directory)
        self.memory_limit_mb = memory_limit_mb
        
        # Initialize components
        try:
            self.df_manager = DataFrameManager(self.db_directory, memory_limit_mb)
            self.sql_parser = SQLParser()
        except Exception as e:
            raise DatabaseDirectoryError(str(self.db_directory), str(e))
        
        # Setup console and history
        self.console = Console()
        self.history_file = self.db_directory / '.history'
        self.history = FileHistory(str(self.history_file))
        
        # Setup intelligent SQL completion
        self.sql_completer = SQLCompleter(self.df_manager)
        
        # Setup command completion for special commands
        self.special_commands = [
            'SHOW DB', 'LOAD DB', 'HELP', 'EXIT', 'QUIT'
        ]
        self.command_completer = WordCompleter(self.special_commands, ignore_case=True)
        
        # Create combined completer
        self.completer = self._create_combined_completer()
        
        # Track loaded files for completion
        self.available_tables = set()
        self._update_table_completion()
    
    def _create_combined_completer(self):
        """Create a completer that combines SQL and command completion."""
        class CombinedCompleter(Completer):
            def __init__(self, sql_completer, command_completer):
                self.sql_completer = sql_completer
                self.command_completer = command_completer
            
            def get_completions(self, document, complete_event):
                text = document.text.strip().upper()
                
                # If it looks like a special command, use command completer
                if (text.startswith('SHOW') or text.startswith('LOAD') or 
                    text.startswith('HELP') or text.startswith('EXIT') or 
                    text.startswith('QUIT')):
                    yield from self.command_completer.get_completions(document, complete_event)
                else:
                    # Otherwise use SQL completer
                    yield from self.sql_completer.get_completions(document, complete_event)
        
        return CombinedCompleter(self.sql_completer, self.command_completer)
    
    def start(self):
        """Start the REPL interface."""
        self._show_welcome()
        
        while True:
            try:
                # Get user input
                user_input = prompt(
                    'excel> ',
                    history=self.history,
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=self.completer,
                    complete_while_typing=True
                ).strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if self._handle_special_command(user_input):
                    continue
                
                # Handle SQL queries
                self._handle_sql_query(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n👋 Use 'EXIT' or 'QUIT' to leave gracefully.")
                continue
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"❌ Unexpected error: {e}", style="red")
                continue
        
        self._show_goodbye()
    
    def _show_welcome(self):
        """Display welcome message."""
        welcome_text = Text()
        welcome_text.append("🔍 Excel DataFrame Processor", style="bold blue")
        welcome_text.append("\nQuery Excel files with SQL syntax\n", style="dim")
        
        info_text = f"""
📁 Database Directory: {self.db_directory}
💾 Memory Limit: {self.memory_limit_mb} MB
📋 History File: {self.history_file}

Type 'HELP' for available commands or 'EXIT' to quit.
        """.strip()
        
        panel = Panel(
            welcome_text.append(info_text),
            title="Welcome",
            border_style="blue",
            box=box.ROUNDED
        )
        self.console.print(panel)
        self.console.print()
    
    def _show_goodbye(self):
        """Display goodbye message."""
        self.console.print("\n👋 Goodbye! Thanks for using Excel DataFrame Processor!", style="blue")
    
    def _handle_special_command(self, command: str) -> bool:
        """Handle special non-SQL commands.
        
        Args:
            command: User input command
            
        Returns:
            True if command was handled, False otherwise
        """
        cmd_upper = command.upper().strip()
        
        if cmd_upper in ('EXIT', 'QUIT'):
            return self._handle_exit()
        elif cmd_upper == 'HELP':
            self._handle_help()
            return True
        elif cmd_upper == 'SHOW DB':
            self._handle_show_db()
            return True
        elif cmd_upper == 'LOAD DB':
            self._handle_load_db()
            return True
        elif cmd_upper == 'SHOW MEMORY':
            self._handle_show_memory()
            return True
        elif cmd_upper.startswith('CLEAR CACHE'):
            self._handle_clear_cache(command)
            return True
        
        return False
    
    def _handle_exit(self) -> bool:
        """Handle EXIT command."""
        sys.exit(0)
    
    def _handle_help(self):
        """Display help information."""
        help_text = """
🔍 **SQL Query Examples:**
  SELECT * FROM employees.xlsx.staff
  SELECT name, salary FROM employees.staff WHERE salary > 70000
  SELECT * FROM employees.staff ORDER BY salary DESC
  SELECT * FROM employees.staff WHERE ROWNUM <= 10
  SELECT * FROM file1.sheet1, file2.sheet2 WHERE file1.sheet1.id = file2.sheet2.id
  SELECT name, department FROM employees.staff > output.csv

📋 **Special Commands:**
  SHOW DB          - List all Excel files and sheets
  LOAD DB          - Load all Excel files into memory
  SHOW MEMORY      - Display current memory usage
  CLEAR CACHE      - Clear DataFrame cache
  HELP             - Show this help message
  EXIT / QUIT      - Exit the application

🔧 **SQL Features:**
  • SELECT with column names or *
  • FROM with file.sheet notation
  • WHERE with comparison operators (=, !=, <, >, <=, >=)
  • ORDER BY with ASC/DESC
  • ROWNUM for limiting results
  • JOIN operations (basic support)
  • CSV export with > filename.csv

💡 **Tips:**
  • Use tab completion for commands and table names
  • Arrow keys navigate command history
  • File names can omit .xlsx extension
  • Use quotes for files/sheets with spaces
        """.strip()
        
        panel = Panel(
            help_text,
            title="Help - Excel DataFrame Processor",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)
    
    def _handle_show_db(self):
        """Handle SHOW DB command."""
        try:
            db_info = self.df_manager.get_database_info()
            
            if not db_info.excel_files:
                self.console.print("📁 No Excel files found in database directory.", style="yellow")
                return
            
            # Create table for files and sheets
            table = Table(title="📊 Database Contents", box=box.ROUNDED)
            table.add_column("📄 Excel File", style="cyan", no_wrap=True)
            table.add_column("📋 Sheets", style="green")
            table.add_column("📊 Status", style="yellow")
            
            for file_name, sheets in db_info.excel_files.items():
                status = "✅ Loaded" if file_name in self.df_manager.loaded_files else "⏳ Not Loaded"
                sheets_str = ", ".join(sheets)
                table.add_row(file_name, sheets_str, status)
            
            self.console.print(table)
            self.console.print(f"\n📈 Summary: {db_info.total_files} files, {db_info.loaded_files} loaded")
            
            # Show temporary tables if any exist
            temp_tables = self.df_manager.list_temp_tables()
            if temp_tables:
                temp_table = Table(title="💾 In-Memory Temporary Tables", box=box.ROUNDED)
                temp_table.add_column("📋 Table Name", style="magenta", no_wrap=True)
                temp_table.add_column("📊 Rows", style="cyan")
                temp_table.add_column("📊 Columns", style="cyan")
                
                for table_name in temp_tables:
                    temp_df = self.df_manager.get_temp_table(table_name)
                    if temp_df is not None:
                        temp_table.add_row(table_name, str(len(temp_df)), str(len(temp_df.columns)))
                
                self.console.print("\n")
                self.console.print(temp_table)
                self.console.print(f"💾 Temporary tables: {len(temp_tables)}")
            
            # Update completion
            self._update_table_completion()
            
        except Exception as e:
            self.console.print(f"❌ Error scanning database: {e}", style="red")
    
    def _handle_load_db(self):
        """Handle LOAD DB command."""
        try:
            with self.console.status("[bold green]Loading Excel files..."):
                loaded_files = self.df_manager.load_all_db_files(show_progress=False)
            
            total_memory = sum(f.memory_usage for f in loaded_files.values())
            
            self.console.print(f"✅ Loaded {len(loaded_files)} files ({total_memory:.2f} MB)", style="green")
            
            # Update completion
            self._update_table_completion()
            
        except Exception as e:
            self.console.print(f"❌ Error loading files: {e}", style="red")
    
    def _handle_show_memory(self):
        """Handle SHOW MEMORY command."""
        try:
            memory_info = self.df_manager.get_memory_usage()
            
            # Create memory usage table
            table = Table(title="💾 Memory Usage", box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Memory", f"{memory_info['total_mb']:.2f} MB")
            table.add_row("Memory Limit", f"{memory_info['limit_mb']:.2f} MB")
            table.add_row("Usage Percentage", f"{memory_info['usage_percent']:.1f}%")
            table.add_row("Files Loaded", str(len(memory_info['files'])))
            
            self.console.print(table)
            
            if memory_info['files']:
                self.console.print("\n📄 Memory by file:")
                for file_name, usage in memory_info['files'].items():
                    self.console.print(f"  • {file_name}: {usage:.2f} MB")
            
        except Exception as e:
            self.console.print(f"❌ Error getting memory info: {e}", style="red")
    
    def _handle_clear_cache(self, command: str):
        """Handle CLEAR CACHE command."""
        try:
            parts = command.split()
            if len(parts) > 2:
                file_name = parts[2]
                self.df_manager.clear_cache(file_name)
                self.console.print(f"✅ Cleared cache for {file_name}", style="green")
            else:
                self.df_manager.clear_cache()
                self.console.print("✅ Cleared all cache", style="green")
                
        except Exception as e:
            self.console.print(f"❌ Error clearing cache: {e}", style="red")
    
    def _handle_sql_query(self, query: str):
        """Handle SQL query execution.
        
        Args:
            query: SQL query string
        """
        try:
            # Parse the query
            parsed_query = self.sql_parser.parse(query)
            
            # Execute the query (basic implementation)
            result_df = self._execute_query(parsed_query)
            
            # Handle CSV export
            if parsed_query.output_file:
                self._export_to_csv(result_df, parsed_query.output_file)
            else:
                # Display results
                self._display_results(result_df, query)
                
        except SQLSyntaxError as e:
            self.console.print(f"❌ SQL Syntax Error: {e.message}", style="red")
            if e.suggestion:
                self.console.print(f"💡 Suggestion: {e.suggestion}", style="yellow")
        except ExcelProcessorError as e:
            self.console.print(f"❌ Error: {e.message}", style="red")
        except Exception as e:
            self.console.print(f"❌ Unexpected error: {e}", style="red")
    
    def _execute_query(self, parsed_query) -> pd.DataFrame:
        """Execute a parsed SQL query (basic implementation).
        
        Args:
            parsed_query: Parsed SQL query object
            
        Returns:
            DataFrame with query results
        """
        # Handle CREATE TABLE AS statements
        if parsed_query.query_type == "CREATE_TABLE_AS":
            return self._execute_create_table_as(parsed_query)
        
        # Basic implementation - will be enhanced when QueryExecutor is implemented
        if not parsed_query.from_node or not parsed_query.from_node.tables:
            raise ExcelProcessorError("Query must specify a table in FROM clause")
        
        # For now, handle single table queries
        if len(parsed_query.from_node.tables) > 1:
            raise ExcelProcessorError("Multi-table queries not yet fully implemented")
        
        table_ref = parsed_query.from_node.tables[0]
        
        # Load the DataFrame
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
        
        return df
    
    def _execute_create_table_as(self, parsed_query) -> pd.DataFrame:
        """Execute a CREATE TABLE AS statement.
        
        Args:
            parsed_query: Parsed CREATE TABLE AS query
            
        Returns:
            DataFrame with the created table data
        """
        create_node = parsed_query.create_table_as_node
        table_name = create_node.table_name
        select_query = create_node.select_query
        
        # Execute the SELECT query to get the data
        result_df = self._execute_query(select_query)
        
        # Store as temporary table
        self.df_manager.create_temp_table(table_name, result_df)
        
        # Display success message
        self.console.print(f"✅ Created temporary table '{table_name}' with {len(result_df)} rows and {len(result_df.columns)} columns", style="green")
        
        return result_df
    
    def _display_results(self, df: pd.DataFrame, query: str):
        """Display query results in a formatted table.
        
        Args:
            df: DataFrame to display
            query: Original query string
        """
        if len(df) == 0:
            self.console.print("📊 Query returned no results.", style="yellow")
            return
        
        # Create rich table
        table = Table(
            title=f"📊 Query Results ({len(df)} rows × {len(df.columns)} columns)",
            box=box.ROUNDED,
            show_lines=True
        )
        
        # Add columns
        for col in df.columns:
            table.add_column(str(col), style="cyan", no_wrap=False)
        
        # Add rows (limit to first 50 for display)
        display_limit = 50
        for i, (_, row) in enumerate(df.head(display_limit).iterrows()):
            row_data = []
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    row_data.append("[dim]NULL[/dim]")
                else:
                    # Format different data types
                    if isinstance(value, (int, float)):
                        if isinstance(value, float) and value.is_integer():
                            row_data.append(str(int(value)))
                        else:
                            row_data.append(str(value))
                    else:
                        # Truncate long strings
                        str_value = str(value)
                        if len(str_value) > 50:
                            str_value = str_value[:47] + "..."
                        row_data.append(str_value)
            
            table.add_row(*row_data)
        
        self.console.print(table)
        
        # Show truncation message if needed
        if len(df) > display_limit:
            self.console.print(f"📋 Showing first {display_limit} rows of {len(df)} total rows", style="dim")
        
        # Show query info
        self.console.print(f"🔍 Query: {query}", style="dim")
    
    def _export_to_csv(self, df: pd.DataFrame, filename: str):
        """Export DataFrame to CSV file.
        
        Args:
            df: DataFrame to export
            filename: Output filename
        """
        try:
            output_path = Path(filename)
            
            # Create directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists and ask for confirmation
            if output_path.exists():
                if not confirm(f"File '{filename}' already exists. Overwrite?"):
                    self.console.print("❌ Export cancelled.", style="yellow")
                    return
            
            # Export to CSV
            df.to_csv(output_path, index=False)
            
            self.console.print(f"✅ Exported {len(df)} rows to {filename}", style="green")
            
        except Exception as e:
            self.console.print(f"❌ Export failed: {e}", style="red")
    
    def _update_table_completion(self):
        """Update command completion with available table names."""
        try:
            db_info = self.df_manager.get_database_info()
            
            # Add table references to completion
            for file_name, sheets in db_info.excel_files.items():
                # Add file.sheet combinations
                for sheet in sheets:
                    self.available_tables.add(f"{file_name}.{sheet}")
                    # Also add without extension if it's .xlsx
                    if file_name.endswith('.xlsx'):
                        base_name = file_name[:-5]  # Remove .xlsx
                        self.available_tables.add(f"{base_name}.{sheet}")
            
            # Add temporary tables to completion
            temp_tables = self.df_manager.list_temp_tables()
            for table_name in temp_tables:
                self.available_tables.add(table_name)
            
            # Update completer
            all_completions = self.commands + list(self.available_tables)
            self.completer = WordCompleter(all_completions, ignore_case=True)
            
        except Exception:
            # Ignore errors in completion update
            pass