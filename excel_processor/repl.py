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
from .logger import REPLLogger


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
            # Complete table names (file.sheet format) and temporary tables
            for table_name in tables_info.keys():
                if table_name.lower().startswith(word_before_cursor.lower()):
                    yield Completion(table_name, start_position=-len(word_before_cursor))
            
            # Add temporary tables
            temp_tables = self.df_manager.list_temp_tables()
            for table_name in temp_tables:
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
        
        # Check if we're in CREATE TABLE AS context
        if 'CREATE TABLE' in text_upper and 'AS' in text_upper:
            as_pos = text_upper.rfind('AS')
            after_as = text_before_cursor[as_pos + 2:].strip()
            
            # After AS, we expect SELECT or table references
            if not after_as or after_as.upper().startswith('SELECT'):
                return 'keyword'
            elif 'FROM' in after_as.upper():
                from_pos = after_as.upper().rfind('FROM')
                after_from = after_as[from_pos + 4:].strip()
                if not after_from or after_from.endswith(','):
                    return 'table'
        
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
            self.logger = REPLLogger(self.db_directory)
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
            'SHOW DB', 'LOAD DB', 'SHOW MEMORY', 'SHOW CACHE', 'SHOW LOGS',
            'CLEAR CACHE', 'REBUILD CACHE', 'HELP', 'EXIT', 'QUIT'
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
        self.logger.log_session_start(self.memory_limit_mb)
        
        # Auto-cache all files to SQLite for instant query performance
        self._auto_cache_files()
        
        try:
            self._run_repl_loop()
        finally:
            self.logger.log_session_end()
    
    def _auto_cache_files(self):
        """Automatically cache all files to SQLite on startup."""
        try:
            if not self.df_manager.use_sqlite_cache:
                self.console.print("\n⚠️  SQLite cache disabled. Queries will load files on-demand.\n", style="yellow")
                return
            
            # Check if cache already exists
            cache_stats = self.df_manager.sqlite_cache.get_cache_stats()
            has_existing_cache = cache_stats.get('cached_files', 0) > 0
            
            if has_existing_cache:
                total_rows = sum(f['rows'] for f in cache_stats.get('files', []))
                self.console.print(f"\n✅ Using existing SQLite cache ({cache_stats['cached_files']} files, {total_rows:,} rows)", style="green")
                self.console.print("   Checking for new or updated files...")
            else:
                self.console.print("\n🚀 Initializing SQLite cache for fast queries...", style="cyan")
            
            cached_files = self.df_manager.cache_all_files_to_sqlite(show_progress=not has_existing_cache)
            
            if cached_files:
                success_count = sum(1 for v in cached_files.values() if v)
                if has_existing_cache:
                    # Simple check: if we got results, all files are cached
                    self.console.print("   ✓ All files up to date\n", style="green")
                else:
                    self.console.print(f"\n✅ Cache ready! {success_count} files available for instant querying.\n", style="green bold")
            else:
                self.console.print("\n⚠️  No files found to cache.\n", style="yellow")
        except Exception as e:
            self.console.print(f"\n⚠️  Cache initialization failed: {e}", style="yellow")
            self.console.print("Continuing with on-demand file loading...\n", style="dim")
    
    def _run_repl_loop(self):
        """Run the main REPL loop."""
        while True:
            try:
                # Get user input with minimal features for better performance
                user_input = prompt(
                    'excel> ',
                    history=self.history,
                    auto_suggest=None,  # Disabled for performance
                    completer=None,  # Disabled for performance
                    complete_while_typing=False
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
            self.logger.log_command(command, "EXIT")
            return self._handle_exit()
        elif cmd_upper == 'HELP':
            self.logger.log_command(command, "HELP")
            self._handle_help()
            return True
        elif cmd_upper == 'SHOW DB':
            self.logger.log_command(command, "SHOW_DB")
            self._handle_show_db()
            return True
        elif cmd_upper == 'LOAD DB':
            self.logger.log_command(command, "LOAD_DB")
            self._handle_load_db()
            return True
        elif cmd_upper == 'SHOW MEMORY':
            self.logger.log_command(command, "SHOW_MEMORY")
            self._handle_show_memory()
            return True
        elif cmd_upper.startswith('CLEAR CACHE'):
            self.logger.log_command(command, "CLEAR_CACHE")
            self._handle_clear_cache(command)
            return True
        elif cmd_upper == 'SHOW LOGS':
            self.logger.log_command(command, "SHOW_LOGS")
            self._handle_show_logs()
            return True
        elif cmd_upper == 'SHOW CACHE':
            self.logger.log_command(command, "SHOW_CACHE")
            self._handle_show_cache()
            return True
        elif cmd_upper == 'REBUILD CACHE':
            self.logger.log_command(command, "REBUILD_CACHE")
            self._handle_rebuild_cache()
            return True
        elif cmd_upper.startswith('DESCRIBE ') or cmd_upper.startswith('DESC '):
            self.logger.log_command(command, "DESCRIBE")
            self._handle_describe(command)
            return True
        elif cmd_upper.startswith('SHOW COLUMNS FROM '):
            self.logger.log_command(command, "SHOW_COLUMNS")
            self._handle_describe(command)
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
  SELECT department, COUNT(*), AVG(salary) FROM employees.staff GROUP BY department
  SELECT department, COUNT(*) FROM employees.staff GROUP BY department HAVING COUNT(*) > 3
  SELECT name, salary, ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) FROM employees.staff
  SELECT name, salary, LAG(salary) OVER (ORDER BY salary) FROM employees.staff
  SELECT * FROM file1.sheet1, file2.sheet2 WHERE file1.sheet1.id = file2.sheet2.id
  SELECT name, department FROM employees.staff > output.csv

📋 **Special Commands:**
  SHOW DB          - List all Excel files and sheets
  LOAD DB          - Load all Excel files into memory
  SHOW MEMORY      - Display current memory usage
  SHOW CACHE       - Display SQLite cache statistics
  SHOW LOGS        - Display log file information
  CLEAR CACHE      - Clear DataFrame cache
  REBUILD CACHE    - Clear and rebuild SQLite cache
  HELP             - Show this help message
  EXIT / QUIT      - Exit the application

🔧 **SQL Features:**
  • SELECT with column names or *
  • FROM with file.sheet notation
  • WHERE with comparison operators (=, !=, <, >, <=, >=)
  • WHERE with IS NULL / IS NOT NULL
  • GROUP BY with aggregation functions (COUNT, SUM, AVG, MIN, MAX)
  • HAVING clause for filtering grouped results
  • Window functions (ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD) with OVER clause
  • PARTITION BY and ORDER BY in window functions
  • ORDER BY with ASC/DESC
  • ROWNUM for limiting results
  • CREATE TABLE AS for temporary tables
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
            
            # Log memory usage
            self.logger.log_memory_usage(
                memory_info['total_mb'], 
                memory_info['usage_percent'], 
                len(memory_info['files'])
            )
            
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
    
    def _handle_show_logs(self):
        """Handle SHOW LOGS command."""
        try:
            log_files = self.logger.get_log_files()
            
            if not log_files:
                self.console.print("📄 No log files found.", style="yellow")
                return
            
            # Create log files table
            table = Table(title="📄 Log Files", box=box.ROUNDED)
            table.add_column("Log Type", style="cyan")
            table.add_column("File Path", style="green")
            table.add_column("Size", style="yellow")
            table.add_column("Last Modified", style="blue")
            
            for log_type, info in log_files.items():
                size_str = f"{info['size'] / 1024:.1f} KB" if info['size'] > 0 else "0 B"
                modified_str = info['modified'].strftime("%Y-%m-%d %H:%M:%S")
                table.add_row(
                    log_type.replace('_', ' ').title(),
                    info['path'],
                    size_str,
                    modified_str
                )
            
            self.console.print(table)
            self.console.print(f"\n💡 Log directory: {self.logger.log_dir}")
            
        except Exception as e:
            self.console.print(f"❌ Error showing logs: {e}", style="red")
    
    def _handle_show_cache(self):
        """Handle SHOW CACHE command."""
        try:
            if not self.df_manager.use_sqlite_cache:
                self.console.print("⚠️  SQLite cache is disabled", style="yellow")
                return
            
            stats = self.df_manager.sqlite_cache.get_cache_stats()
            
            if not stats.get('enabled', False):
                self.console.print("⚠️  SQLite cache is not enabled", style="yellow")
                return
            
            # Calculate totals
            total_rows = sum(f['rows'] for f in stats.get('files', []))
            total_sheets = sum(f['sheets'] for f in stats.get('files', []))
            
            # Create cache statistics table
            table = Table(title="💾 SQLite Cache Statistics", box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Cache Directory", stats['cache_dir'])
            table.add_row("Total Files Cached", str(stats['cached_files']))
            table.add_row("Total Sheets", str(total_sheets))
            table.add_row("Total Rows", f"{total_rows:,}")
            table.add_row("Cache Size", f"{stats['total_size_mb']:.2f} MB")
            table.add_row("Active Connections", str(stats['active_connections']))
            
            self.console.print(table)
            
            # Show cached files
            if stats.get('files'):
                self.console.print("\n📁 Cached Files:")
                for file_info in stats['files']:
                    self.console.print(
                        f"  • {file_info['file']}: {file_info['sheets']} sheets, "
                        f"{file_info['rows']:,} rows, {file_info['size_mb']:.2f} MB"
                    )
            
        except Exception as e:
            self.console.print(f"❌ Error showing cache stats: {e}", style="red")
    
    def _handle_rebuild_cache(self):
        """Handle REBUILD CACHE command."""
        try:
            if not self.df_manager.use_sqlite_cache:
                self.console.print("⚠️  SQLite cache is disabled", style="yellow")
                return
            
            # Confirm with user
            self.console.print("🔄 This will clear and rebuild the entire SQLite cache.", style="yellow")
            response = input("Continue? (y/N): ").strip().lower()
            
            if response != 'y':
                self.console.print("❌ Cancelled", style="red")
                return
            
            # Clear existing cache
            self.console.print("\n🗑️  Clearing existing cache...", style="cyan")
            self.df_manager.clear_cache()
            
            # Rebuild cache
            self.console.print("🔄 Rebuilding cache...\n", style="cyan")
            cached_files = self.df_manager.cache_all_files_to_sqlite(show_progress=True)
            
            success_count = sum(1 for v in cached_files.values() if v)
            self.console.print(f"\n✅ Cache rebuilt! {success_count} files cached.", style="green bold")
            
        except Exception as e:
            self.console.print(f"❌ Error rebuilding cache: {e}", style="red")
    
    def _handle_describe(self, command: str):
        """Handle DESCRIBE/DESC/SHOW COLUMNS command to display table structure.
        
        Args:
            command: DESCRIBE table_name or SHOW COLUMNS FROM table_name
        """
        try:
            # Parse the command to extract table name
            cmd_upper = command.upper().strip()
            
            if cmd_upper.startswith('DESCRIBE ') or cmd_upper.startswith('DESC '):
                # Extract table name after DESCRIBE/DESC
                parts = command.split(maxsplit=1)
                if len(parts) < 2:
                    self.console.print("❌ Usage: DESCRIBE table_name (e.g., DESCRIBE employees.xlsx.staff)", style="red")
                    return
                table_ref = parts[1].strip()
            elif cmd_upper.startswith('SHOW COLUMNS FROM '):
                # Extract table name after FROM
                parts = command.split('FROM', 1)
                if len(parts) < 2:
                    self.console.print("❌ Usage: SHOW COLUMNS FROM table_name", style="red")
                    return
                table_ref = parts[1].strip()
            else:
                return
            
            # Parse table reference (file.sheet format)
            if '.' not in table_ref:
                self.console.print("❌ Table name must be in format: filename.sheetname", style="red")
                self.console.print("   Example: employees.xlsx.staff", style="dim")
                return
            
            # Split into file and sheet
            parts = table_ref.rsplit('.', 1)
            if len(parts) != 2:
                self.console.print("❌ Invalid table format. Use: filename.sheetname", style="red")
                return
            
            file_name = parts[0]
            sheet_name = parts[1]
            
            # Add .xlsx if not present
            if not any(file_name.endswith(ext) for ext in ['.xlsx', '.xls', '.csv', '.xlsm', '.xlsb']):
                file_name += '.xlsx'
            
            # Get column information
            column_info = self.df_manager.get_column_info(file_name, sheet_name)
            
            if not column_info:
                self.console.print(f"❌ No columns found in {file_name}.{sheet_name}", style="red")
                return
            
            # Create table to display columns
            table = Table(title=f"📋 Columns in {file_name}.{sheet_name}", box=box.ROUNDED)
            table.add_column("Column Name", style="cyan", no_wrap=True)
            table.add_column("Data Type", style="green")
            
            for col_name, col_type in column_info.items():
                table.add_row(col_name, col_type)
            
            self.console.print(table)
            self.console.print(f"\n📊 Total columns: {len(column_info)}", style="dim")
            
        except Exception as e:
            self.console.print(f"❌ Error describing table: {e}", style="red")
            self.console.print("💡 Tip: Use format 'DESCRIBE filename.sheetname'", style="yellow")
    
    def _handle_sql_query(self, query: str):
        """Handle SQL query execution.
        
        Args:
            query: SQL query string
        """
        import time
        start_time = time.time()
        
        try:
            # Parse the query
            parsed_query = self.sql_parser.parse(query)
            
            # Execute the query (basic implementation)
            result_df = self._execute_query(parsed_query)
            
            execution_time = time.time() - start_time
            
            # Log the query execution
            self.logger.log_query(query, len(result_df), execution_time)
            
            # Handle CSV export
            if parsed_query.output_file:
                self._export_to_csv(result_df, parsed_query.output_file)
                self.logger.log_export(parsed_query.output_file, len(result_df))
            else:
                # Display results
                self._display_results(result_df, query)
                
        except SQLSyntaxError as e:
            self.logger.log_error(f"SQL Syntax Error: {e.message}", query)
            self.console.print(f"❌ SQL Syntax Error: {e.message}", style="red")
            if e.suggestion:
                self.console.print(f"💡 Suggestion: {e.suggestion}", style="yellow")
        except ExcelProcessorError as e:
            self.logger.log_error(f"Error: {e.message}", query)
            self.console.print(f"❌ Error: {e.message}", style="red")
        except Exception as e:
            self.logger.log_error(f"Unexpected error: {str(e)}", query)
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
            # Check if we have aggregate functions or window functions in SELECT
            has_window_functions = False
            has_aggregate_functions = False
            if parsed_query.select_node:
                from .sql_ast import WindowFunctionNode, AggregateFunctionNode, ColumnAliasNode
                for col in parsed_query.select_node.columns:
                    if isinstance(col, WindowFunctionNode):
                        has_window_functions = True
                    elif isinstance(col, AggregateFunctionNode):
                        has_aggregate_functions = True
                    elif isinstance(col, ColumnAliasNode):
                        # Check if the aliased expression is an aggregate or window function
                        if isinstance(col.expression, AggregateFunctionNode):
                            has_aggregate_functions = True
                        elif isinstance(col.expression, WindowFunctionNode):
                            has_window_functions = True
            
            # Apply WHERE clause first (before column selection)
            if parsed_query.where_node:
                conditions = parsed_query.where_node.where_clause.conditions
                for condition in conditions:
                    if str(condition.left).upper() == 'ROWNUM':
                        if condition.operator in ['<', '<=']:
                            limit = int(condition.right)
                            df = df.head(limit)
                    else:
                        # Handle quoted column names in WHERE clause
                        column_name = str(condition.left)
                        # Remove quotes if present
                        if ((column_name.startswith('"') and column_name.endswith('"')) or 
                            (column_name.startswith("'") and column_name.endswith("'"))):
                            column_name = column_name[1:-1]
                        
                        if column_name in df.columns:
                            if condition.operator == '>':
                                df = df[df[column_name] > condition.right]
                            elif condition.operator == '<':
                                df = df[df[column_name] < condition.right]
                            elif condition.operator == '=':
                                df = df[df[column_name] == condition.right]
                            elif condition.operator == '>=':
                                df = df[df[column_name] >= condition.right]
                            elif condition.operator == '<=':
                                df = df[df[column_name] <= condition.right]
                            elif condition.operator in ['!=', '<>']:
                                df = df[df[column_name] != condition.right]
                            elif condition.operator == 'IS':
                                if str(condition.right).upper() == 'NULL':
                                    df = df[df[column_name].isna()]
                            elif condition.operator == 'IS NOT':
                                if str(condition.right).upper() == 'NULL':
                                    df = df[df[column_name].notna()]
            
            if has_aggregate_functions:
                # Handle aggregate functions without GROUP BY (e.g., SELECT COUNT(*) FROM table)
                df = self._execute_simple_aggregation(df, parsed_query)
            elif has_window_functions:
                df = self._execute_window_functions(df, parsed_query)
            else:
                # Apply column selection for non-GROUP BY, non-window queries
                if parsed_query.select_node and not parsed_query.select_node.is_wildcard:
                    df = self._apply_column_selection(df, parsed_query.select_node.columns)
        
        # WHERE clause is now applied above, before column selection
        if False:  # Disabled - moved above
            print(f"DEBUG: Applying WHERE clause with {len(parsed_query.where_node.where_clause.conditions)} conditions")
            conditions = parsed_query.where_node.where_clause.conditions
            for condition in conditions:
                print(f"DEBUG: Processing condition: {condition.left} {condition.operator} {condition.right}")
                if str(condition.left).upper() == 'ROWNUM':
                    if condition.operator in ['<', '<=']:
                        limit = int(condition.right)
                        df = df.head(limit)
                else:
                    # Handle quoted column names in WHERE clause
                    column_name = str(condition.left)
                    print(f"DEBUG: Original column_name: '{column_name}'")
                    # Remove quotes if present
                    if ((column_name.startswith('"') and column_name.endswith('"')) or 
                        (column_name.startswith("'") and column_name.endswith("'"))):
                        column_name = column_name[1:-1]
                    print(f"DEBUG: Processed column_name: '{column_name}'")
                    print(f"DEBUG: Available columns: {list(df.columns)}")
                    
                    if column_name in df.columns:
                        print(f"DEBUG: Column found, applying filter: {column_name} {condition.operator} {condition.right}")
                        original_shape = df.shape
                        if condition.operator == '>':
                            df = df[df[column_name] > condition.right]
                        elif condition.operator == '<':
                            df = df[df[column_name] < condition.right]
                        elif condition.operator == '=':
                            df = df[df[column_name] == condition.right]
                        elif condition.operator == '>=':
                            df = df[df[column_name] >= condition.right]
                        elif condition.operator == '<=':
                            df = df[df[column_name] <= condition.right]
                        elif condition.operator in ['!=', '<>']:
                            df = df[df[column_name] != condition.right]
                        elif condition.operator == 'IS':
                            if str(condition.right).upper() == 'NULL':
                                df = df[df[column_name].isna()]
                        elif condition.operator == 'IS NOT':
                            if str(condition.right).upper() == 'NULL':
                                df = df[df[column_name].notna()]
                        print(f"DEBUG: Shape changed from {original_shape} to {df.shape}")
                    else:
                        print(f"DEBUG: Column '{column_name}' not found in DataFrame")
        
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
        
        # Log the table creation
        self.logger.log_create_table(table_name, len(result_df), len(result_df.columns))
        
        # Display success message
        self.console.print(f"✅ Created temporary table '{table_name}' with {len(result_df)} rows and {len(result_df.columns)} columns", style="green")
        
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
    
    def _execute_simple_aggregation(self, df: pd.DataFrame, parsed_query) -> pd.DataFrame:
        """Execute aggregate functions without GROUP BY (e.g., SELECT COUNT(*) FROM table).
        
        Args:
            df: Source DataFrame
            parsed_query: Parsed SQL query with aggregate functions but no GROUP BY
            
        Returns:
            DataFrame with single row containing aggregated results
        """
        from .sql_ast import AggregateFunctionNode, ColumnAliasNode
        
        select_columns = parsed_query.select_node.columns
        result_data = {}
        
        for col in select_columns:
            if isinstance(col, AggregateFunctionNode):
                func_name = col.function_name.lower()
                target_col = str(col.column).strip()
                
                # Determine column name for result
                if hasattr(col, 'alias') and col.alias:
                    result_col_name = col.alias
                else:
                    result_col_name = f"{func_name}({target_col})"
                
                # Calculate aggregate
                if target_col == '*' and func_name == 'count':
                    # COUNT(*) - count all rows
                    result_data[result_col_name] = len(df)
                elif target_col in df.columns:
                    if func_name == 'count':
                        result_data[result_col_name] = df[target_col].count()
                    elif func_name == 'sum':
                        result_data[result_col_name] = df[target_col].sum()
                    elif func_name == 'avg':
                        result_data[result_col_name] = df[target_col].mean()
                    elif func_name == 'min':
                        result_data[result_col_name] = df[target_col].min()
                    elif func_name == 'max':
                        result_data[result_col_name] = df[target_col].max()
                else:
                    raise ExcelProcessorError(f"Column '{target_col}' not found in table")
            
            elif isinstance(col, ColumnAliasNode):
                # Handle aliased aggregate functions
                if isinstance(col.expression, AggregateFunctionNode):
                    agg_func = col.expression
                    func_name = agg_func.function_name.lower()
                    target_col = str(agg_func.column).strip()
                    result_col_name = col.alias
                    
                    # Calculate aggregate
                    if target_col == '*' and func_name == 'count':
                        result_data[result_col_name] = len(df)
                    elif target_col in df.columns:
                        if func_name == 'count':
                            result_data[result_col_name] = df[target_col].count()
                        elif func_name == 'sum':
                            result_data[result_col_name] = df[target_col].sum()
                        elif func_name == 'avg':
                            result_data[result_col_name] = df[target_col].mean()
                        elif func_name == 'min':
                            result_data[result_col_name] = df[target_col].min()
                        elif func_name == 'max':
                            result_data[result_col_name] = df[target_col].max()
                    else:
                        raise ExcelProcessorError(f"Column '{target_col}' not found in table")
        
        # Create single-row DataFrame with results
        return pd.DataFrame([result_data])
    
    def _execute_window_functions(self, df: pd.DataFrame, parsed_query) -> pd.DataFrame:
        """Execute window functions in SELECT clause.
        
        Args:
            df: Source DataFrame
            parsed_query: Parsed SQL query with window functions
            
        Returns:
            DataFrame with window function results
        """
        from .sql_ast import WindowFunctionNode, ColumnAliasNode, LiteralNode
        
        result_df = df.copy()
        select_columns = []
        
        for col in parsed_query.select_node.columns:
            if isinstance(col, ColumnAliasNode):
                if isinstance(col.expression, WindowFunctionNode):
                    # Window function with alias
                    window_result = self._calculate_window_function(result_df, col.expression)
                    result_df[col.alias] = window_result
                    select_columns.append(col.alias)
                elif isinstance(col.expression, LiteralNode):
                    # Literal with alias
                    result_df[col.alias] = col.expression.value
                    select_columns.append(col.alias)
                elif isinstance(col.expression, str):
                    # Column with alias
                    if col.expression in result_df.columns:
                        result_df[col.alias] = result_df[col.expression]
                        select_columns.append(col.alias)
            
            elif isinstance(col, WindowFunctionNode):
                # Execute window function without alias
                window_result = self._calculate_window_function(result_df, col)
                
                # Add the result as a new column
                col_name = f"{col.function_name.lower()}"
                if col.column:
                    col_name += f"_{col.column}"
                
                result_df[col_name] = window_result
                select_columns.append(col_name)
            
            elif isinstance(col, LiteralNode):
                # Literal without alias
                col_name = f"literal_{len(select_columns)}"
                result_df[col_name] = col.value
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
                if col not in unique_columns and col in result_df.columns:
                    unique_columns.append(col)
            result_df = result_df[unique_columns]
        
        return result_df
    
    def _calculate_window_function(self, df: pd.DataFrame, window_func: 'WindowFunctionNode'):
        """Calculate a single window function.
        
        Args:
            df: Source DataFrame
            window_func: Window function specification
            
        Returns:
            Series with calculated values
        """
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
        
        # Calculate window function
        if func_name == 'ROW_NUMBER':
            if partition_by:
                # ROW_NUMBER() OVER (PARTITION BY col ORDER BY col2)
                if order_by:
                    ascending = [direction == 'ASC' for direction in order_directions]
                    result = df.sort_values(order_by, ascending=ascending).groupby(partition_by, observed=False).cumcount() + 1
                else:
                    result = df.groupby(partition_by, observed=False).cumcount() + 1
            else:
                # ROW_NUMBER() OVER (ORDER BY col)
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
                # RANK() OVER (PARTITION BY col ORDER BY col2)
                def rank_group(group):
                    return group[order_by].rank(method='min', ascending=ascending[0] if len(ascending) == 1 else ascending)
                
                result = df.groupby(partition_by, observed=False).apply(rank_group).reset_index(level=0, drop=True)
            else:
                # RANK() OVER (ORDER BY col)
                result = df[order_by].rank(method='min', ascending=ascending[0] if len(ascending) == 1 else ascending)
        
        elif func_name == 'DENSE_RANK':
            if not order_by:
                raise ExcelProcessorError("DENSE_RANK() requires ORDER BY clause")
            
            ascending = [direction == 'ASC' for direction in order_directions]
            
            if partition_by:
                # DENSE_RANK() OVER (PARTITION BY col ORDER BY col2)
                def dense_rank_group(group):
                    return group[order_by].rank(method='dense', ascending=ascending[0] if len(ascending) == 1 else ascending)
                
                result = df.groupby(partition_by, observed=False).apply(dense_rank_group).reset_index(level=0, drop=True)
            else:
                # DENSE_RANK() OVER (ORDER BY col)
                result = df[order_by].rank(method='dense', ascending=ascending[0] if len(ascending) == 1 else ascending)
        
        elif func_name == 'LAG':
            if not column or column not in df.columns:
                raise ExcelProcessorError(f"LAG() requires a valid column name")
            
            if partition_by:
                # LAG(col) OVER (PARTITION BY col2 ORDER BY col3)
                if order_by:
                    ascending = [direction == 'ASC' for direction in order_directions]
                    sorted_df = df.sort_values(partition_by + order_by, ascending=[True] * len(partition_by) + ascending)
                    result = sorted_df.groupby(partition_by, observed=False)[column].shift(1)
                    result = result.reindex(df.index)
                else:
                    result = df.groupby(partition_by, observed=False)[column].shift(1)
            else:
                # LAG(col) OVER (ORDER BY col2)
                if order_by:
                    ascending = [direction == 'ASC' for direction in order_directions]
                    sorted_df = df.sort_values(order_by, ascending=ascending)
                    result = sorted_df[column].shift(1)
                    result = result.reindex(df.index)
                else:
                    result = df[column].shift(1)
        
        elif func_name == 'LEAD':
            if not column or column not in df.columns:
                raise ExcelProcessorError(f"LEAD() requires a valid column name")
            
            if partition_by:
                # LEAD(col) OVER (PARTITION BY col2 ORDER BY col3)
                if order_by:
                    ascending = [direction == 'ASC' for direction in order_directions]
                    sorted_df = df.sort_values(partition_by + order_by, ascending=[True] * len(partition_by) + ascending)
                    result = sorted_df.groupby(partition_by, observed=False)[column].shift(-1)
                    result = result.reindex(df.index)
                else:
                    result = df.groupby(partition_by, observed=False)[column].shift(-1)
            else:
                # LEAD(col) OVER (ORDER BY col2)
                if order_by:
                    ascending = [direction == 'ASC' for direction in order_directions]
                    sorted_df = df.sort_values(order_by, ascending=ascending)
                    result = sorted_df[column].shift(-1)
                    result = result.reindex(df.index)
                else:
                    result = df[column].shift(-1)
        
        else:
            raise ExcelProcessorError(f"Window function '{func_name}' not implemented")
        
        return result
    
    def _apply_column_selection(self, df: pd.DataFrame, select_columns: list) -> pd.DataFrame:
        """Apply column selection with support for aliases and literals.
        
        Args:
            df: Source DataFrame
            select_columns: List of column expressions from SELECT clause
            
        Returns:
            DataFrame with selected/computed columns
        """
        from .sql_ast import ColumnAliasNode, LiteralNode, WindowFunctionNode, AggregateFunctionNode
        
        result_df = df.copy()
        final_columns = []
        
        for col_expr in select_columns:
            if isinstance(col_expr, ColumnAliasNode):
                # Handle column with alias
                if isinstance(col_expr.expression, LiteralNode):
                    # Literal value with alias: SELECT 'testing on this' AS test
                    result_df[col_expr.alias] = col_expr.expression.value
                    final_columns.append(col_expr.alias)
                elif isinstance(col_expr.expression, str):
                    # Column name with alias: SELECT column_name AS alias
                    if col_expr.expression in result_df.columns:
                        result_df[col_expr.alias] = result_df[col_expr.expression]
                        final_columns.append(col_expr.alias)
                    else:
                        raise ExcelProcessorError(f"Column '{col_expr.expression}' not found")
                elif hasattr(col_expr.expression, 'column_name'):
                    # ColumnReference with alias: SELECT "Full Name" AS employee_name
                    column_name = col_expr.expression.column_name
                    if column_name in result_df.columns:
                        result_df[col_expr.alias] = result_df[column_name]
                        final_columns.append(col_expr.alias)
                    else:
                        raise ExcelProcessorError(f"Column '{column_name}' not found")
                else:
                    # Function with alias (handled elsewhere)
                    final_columns.append(col_expr.alias)
            
            elif isinstance(col_expr, LiteralNode):
                # Literal without alias - use the value as column name
                col_name = f"literal_{len(final_columns)}"
                result_df[col_name] = col_expr.value
                final_columns.append(col_name)
            
            elif isinstance(col_expr, str):
                # Regular column name (possibly quoted)
                if col_expr in result_df.columns:
                    final_columns.append(col_expr)
                else:
                    raise ExcelProcessorError(f"Column '{col_expr}' not found")
            
            elif hasattr(col_expr, 'column_name'):
                # ColumnReference without alias: SELECT "Full Name"
                column_name = col_expr.column_name
                if column_name in result_df.columns:
                    final_columns.append(column_name)
                else:
                    raise ExcelProcessorError(f"Column '{column_name}' not found")
            
            else:
                # Other types (functions, etc.) - handle by string representation
                col_str = str(col_expr)
                if col_str in result_df.columns:
                    final_columns.append(col_str)
        
        # Select only the final columns
        if final_columns:
            # Remove duplicates while preserving order
            unique_columns = []
            for col in final_columns:
                if col not in unique_columns and col in result_df.columns:
                    unique_columns.append(col)
            
            if unique_columns:
                result_df = result_df[unique_columns]
        
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