# Design Document

## Overview

The Excel DataFrame Processor is a Python application that provides a REPL interface for executing Oracle-like SQL queries on Excel files. The application loads Excel sheets into pandas DataFrames and translates SQL queries into DataFrame operations. It features colorful tabular output and supports direct CSV export using shell-like redirection syntax.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    A[REPL Interface] --> B[SQL Parser]
    B --> C[Query Executor]
    C --> D[DataFrame Manager]
    D --> E[Excel Loader]
    C --> F[Result Formatter]
    F --> G[Colorful Table Display]
    F --> H[CSV Exporter]
    
    subgraph "Data Layer"
        I[Excel Files]
        J[Pandas DataFrames]
        K[CSV Output]
    end
    
    E --> I
    D --> J
    H --> K
```

### Component Interaction Flow

1. **User Input**: REPL receives SQL query from user
2. **Parsing**: SQL Parser tokenizes and validates query syntax
3. **Execution**: Query Executor translates SQL to pandas operations
4. **Data Management**: DataFrame Manager handles Excel loading and caching
5. **Output**: Result Formatter displays colorful tables or exports CSV

## Components and Interfaces

### 1. REPL Interface (`repl.py`)

**Responsibilities:**
- Provide interactive command-line interface with --db directory support
- Handle user input with arrow key history navigation
- Manage session state and database directory
- Support special commands (SHOW DB, LOAD DB, HELP, EXIT)
- Maintain persistent command history in .history file

**Key Methods:**
```python
class ExcelREPL:
    def __init__(self, db_directory: str) -> None
    def start_session(self) -> None
    def process_command(self, command: str) -> None
    def handle_sql_query(self, query: str) -> None
    def handle_special_command(self, command: str) -> None
    def show_db_contents(self) -> None
    def load_all_db_files(self) -> None
    def show_help(self) -> None
    def load_history(self) -> List[str]
    def save_history(self, command: str) -> None
    def display_prompt(self) -> str
```

### 2. SQL Parser (`sql_parser.py`)

**Responsibilities:**
- Parse Oracle-like SQL syntax
- Validate query structure and syntax
- Extract table references (file.sheet notation)
- Handle JOIN conditions and WHERE clauses

**Key Classes:**
```python
class SQLQuery:
    select_columns: List[str]
    from_tables: List[TableReference]
    where_conditions: Optional[WhereClause]
    join_conditions: List[JoinClause]
    order_by: Optional[OrderByClause]
    output_file: Optional[str]  # For > redirection

class TableReference:
    file_path: str
    sheet_name: str
    alias: Optional[str]

class SQLParser:
    def parse(self, query: str) -> SQLQuery
    def validate_syntax(self, query: str) -> List[str]  # Returns errors
```

### 3. Query Executor (`query_executor.py`)

**Responsibilities:**
- Translate SQL queries to pandas operations
- Execute DataFrame operations (joins, filters, sorts)
- Handle aggregations and grouping
- Manage ROWNUM functionality

**Key Methods:**
```python
class QueryExecutor:
    def execute_query(self, query: SQLQuery) -> pd.DataFrame
    def apply_select(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame
    def apply_where(self, df: pd.DataFrame, conditions: WhereClause) -> pd.DataFrame
    def apply_joins(self, tables: List[pd.DataFrame], joins: List[JoinClause]) -> pd.DataFrame
    def apply_order_by(self, df: pd.DataFrame, order: OrderByClause) -> pd.DataFrame
    def apply_rownum_limit(self, df: pd.DataFrame, limit: int) -> pd.DataFrame
```

### 4. DataFrame Manager (`dataframe_manager.py`)

**Responsibilities:**
- Load and cache Excel files from database directory
- Manage DataFrame lifecycle and memory usage
- Handle file path resolution within db directory
- Provide sheet metadata and database overview
- Support bulk loading of all files in directory

**Key Methods:**
```python
class DataFrameManager:
    def __init__(self, db_directory: str) -> None
    def scan_db_directory(self) -> Dict[str, List[str]]  # file -> sheets
    def load_excel_file(self, file_name: str) -> Dict[str, pd.DataFrame]
    def load_all_db_files(self) -> None
    def get_dataframe(self, file_name: str, sheet_name: str) -> pd.DataFrame
    def list_all_files_and_sheets(self) -> Dict[str, List[str]]
    def get_file_path(self, file_name: str) -> str
    def clear_cache(self) -> None
    def get_column_info(self, file_name: str, sheet_name: str) -> Dict[str, str]
    def get_memory_usage(self) -> Dict[str, float]
```

### 5. Excel Loader (`excel_loader.py`)

**Responsibilities:**
- Handle Excel file reading with openpyxl/xlrd
- Manage different Excel formats (.xlsx, .xls)
- Handle data type inference
- Provide error handling for corrupted files

**Key Methods:**
```python
class ExcelLoader:
    def load_file(self, file_path: str) -> Dict[str, pd.DataFrame]
    def load_sheet(self, file_path: str, sheet_identifier: Union[str, int]) -> pd.DataFrame
    def get_sheet_names(self, file_path: str) -> List[str]
    def validate_file(self, file_path: str) -> bool
```

### 6. Result Formatter (`result_formatter.py`)

**Responsibilities:**
- Format DataFrames for colorful display
- Generate ASCII tables with proper alignment
- Handle color coding for different data types
- Manage terminal width and pagination

**Key Methods:**
```python
class ResultFormatter:
    def format_table(self, df: pd.DataFrame) -> str
    def apply_column_colors(self, df: pd.DataFrame) -> str
    def create_ascii_table(self, df: pd.DataFrame) -> str
    def detect_terminal_capabilities(self) -> bool
    def paginate_results(self, formatted_table: str) -> None
```

### 7. CSV Exporter (`csv_exporter.py`)

**Responsibilities:**
- Export DataFrames to CSV with proper escaping
- Handle special characters and quotes
- Manage file creation and overwrite protection
- Provide export confirmation

**Key Methods:**
```python
class CSVExporter:
    def export_dataframe(self, df: pd.DataFrame, file_path: str) -> bool
    def escape_csv_field(self, field: str) -> str
    def check_file_exists(self, file_path: str) -> bool
    def create_output_directory(self, file_path: str) -> None
```

## Data Models

### Core Data Structures

```python
@dataclass
class ExcelFile:
    file_name: str  # Just filename, not full path
    file_path: str  # Full path within db directory
    sheets: Dict[str, pd.DataFrame]
    last_modified: datetime
    memory_usage: float
    
@dataclass
class QueryResult:
    dataframe: pd.DataFrame
    execution_time: float
    row_count: int
    column_count: int
    
@dataclass
class REPLSession:
    db_directory: str
    loaded_files: Dict[str, ExcelFile]
    query_history: List[str]
    history_file_path: str
    color_enabled: bool
    
@dataclass
class DatabaseInfo:
    directory_path: str
    excel_files: Dict[str, List[str]]  # filename -> sheet names
    total_files: int
    loaded_files: int
```

### SQL AST Nodes

```python
class ASTNode:
    pass

class SelectNode(ASTNode):
    columns: List[str]
    
class FromNode(ASTNode):
    tables: List[TableReference]
    
class WhereNode(ASTNode):
    conditions: List[Condition]
    
class JoinNode(ASTNode):
    join_type: str  # INNER, LEFT, RIGHT, OUTER
    left_table: str
    right_table: str
    on_condition: str
```

## Error Handling

### Error Categories

1. **File Errors**
   - File not found
   - Permission denied
   - Corrupted Excel files
   - Unsupported file formats

2. **SQL Syntax Errors**
   - Invalid query syntax
   - Unknown column names
   - Invalid table references
   - Malformed JOIN conditions

3. **Data Errors**
   - Type conversion failures
   - Missing columns in JOIN operations
   - Empty result sets
   - Memory limitations for large files

### Error Handling Strategy

```python
class ExcelProcessorError(Exception):
    pass

class FileLoadError(ExcelProcessorError):
    pass

class SQLSyntaxError(ExcelProcessorError):
    pass

class DataProcessingError(ExcelProcessorError):
    pass

# Error handling in REPL
try:
    result = query_executor.execute_query(parsed_query)
except SQLSyntaxError as e:
    display_error(f"SQL Syntax Error: {e.message}")
    suggest_correction(e.query, e.position)
except FileLoadError as e:
    display_error(f"File Error: {e.message}")
    suggest_file_check(e.file_path)
```

## Testing Strategy

### Unit Testing Approach

1. **Component Testing**
   - SQL Parser: Test query parsing with various SQL constructs
   - Query Executor: Test DataFrame operations and transformations
   - Excel Loader: Test file loading with different Excel formats
   - Result Formatter: Test table formatting and color output

2. **Integration Testing**
   - End-to-end query execution with sample Excel files
   - REPL command processing and state management
   - CSV export with various data types and special characters

3. **Test Data Strategy**
   - Sample Excel files with multiple sheets
   - Files with different data types (text, numbers, dates)
   - Files with special characters and edge cases
   - Large files for performance testing

### Test Structure

```python
# Test categories
tests/
├── unit/
│   ├── test_sql_parser.py
│   ├── test_query_executor.py
│   ├── test_excel_loader.py
│   └── test_result_formatter.py
├── integration/
│   ├── test_repl_commands.py
│   ├── test_query_execution.py
│   └── test_csv_export.py
├── fixtures/
│   ├── sample_data.xlsx
│   ├── multi_sheet.xlsx
│   └── special_chars.xlsx
└── conftest.py
```

### Performance Considerations

1. **Memory Management**
   - Lazy loading of Excel sheets
   - DataFrame caching with LRU eviction
   - Streaming for large result sets

2. **Query Optimization**
   - Early filtering before joins
   - Column selection optimization
   - Index usage for common operations

3. **File Handling**
   - Asynchronous file loading
   - Progress indicators for large files
   - Efficient Excel parsing with openpyxl

## Dependencies and Technology Stack

### Core Dependencies (pyproject.toml)

```toml
[project]
dependencies = [
    "pandas>=2.0.0",
    "openpyxl>=3.1.0",
    "xlrd>=2.0.0",
    "rich>=13.0.0",        # For colorful terminal output
    "click>=8.0.0",        # For CLI interface
    "prompt-toolkit>=3.0.0", # For REPL with history
    "sqlparse>=0.4.0",     # For SQL parsing assistance
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

### Key Technology Choices

1. **pandas**: Core DataFrame operations and Excel reading
2. **rich**: Colorful terminal output and table formatting
3. **prompt-toolkit**: Advanced REPL with history and auto-completion
4. **sqlparse**: SQL parsing utilities and syntax validation
5. **openpyxl**: Modern Excel file reading (.xlsx)
6. **xlrd**: Legacy Excel file support (.xls)

## Implementation Notes

### Command Line Interface

The application starts with database directory specification:
```bash
python excel_processor.py --db /path/to/excel/files
```

### Special Commands

```python
# Database management commands
SHOW DB          # List all Excel files and sheets in db directory
LOAD DB          # Load all Excel files into memory
HELP             # Show command examples and help
EXIT             # Exit the REPL

# Example help output
"""
Available Commands:
  SHOW DB                           - List all Excel files and sheets
  LOAD DB                          - Load all files into memory
  SELECT * FROM file.sheet         - Select all columns
  SELECT col1, col2 FROM file.sheet WHERE col1 > 10
  SELECT * FROM file1.sheet1, file2.sheet2 WHERE file1.sheet1.id = file2.sheet2.id
  SELECT * FROM file.sheet ORDER BY col1 DESC
  SELECT * FROM file.sheet > output.csv
  HELP                             - Show this help
  EXIT                             - Exit application
"""
```

### SQL to Pandas Translation

The core challenge is translating SQL operations to pandas operations:

```python
# SQL: SELECT col1, col2 FROM file.sheet WHERE col1 > 10
# Pandas: df[['col1', 'col2']][df['col1'] > 10]

# SQL: SELECT * FROM file1.sheet1 INNER JOIN file2.sheet2 ON file1.sheet1.id = file2.sheet2.id
# Pandas: pd.merge(df1, df2, left_on='id', right_on='id', how='inner')
```

### REPL State Management

The REPL maintains session state including:
- Database directory path and scanned Excel files
- Loaded Excel files and their DataFrames
- Query history stored in {db_directory}/.history file
- Arrow key navigation through command history
- Color preferences and terminal capabilities
- Memory usage tracking for loaded DataFrames

### History Management

```python
# History file format: {db_directory}/.history
# Each line is a previous command
# prompt-toolkit handles arrow key navigation
class HistoryManager:
    def load_history(self, db_directory: str) -> FileHistory
    def save_command(self, command: str) -> None
    def get_history_file_path(self, db_directory: str) -> str
```

### Performance Optimization

- **Lazy Loading**: Excel sheets loaded only when referenced or with LOAD DB
- **Caching**: Parsed DataFrames cached until file modification
- **Memory Monitoring**: Track memory usage and provide warnings
- **Query Planning**: Optimize join order and filter application
- **Directory Scanning**: Cache file listings and update on demand