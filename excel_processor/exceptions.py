"""Custom exceptions for Excel DataFrame Processor."""


class ExcelProcessorError(Exception):
    """Base exception for Excel DataFrame Processor."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


class FileLoadError(ExcelProcessorError):
    """Exception raised when Excel file loading fails."""
    
    def __init__(self, file_path: str, message: str, details: str = None):
        self.file_path = file_path
        super().__init__(message, details)
    
    def __str__(self) -> str:
        base_msg = f"Failed to load file '{self.file_path}': {self.message}"
        if self.details:
            base_msg += f"\nDetails: {self.details}"
        return base_msg


class SQLSyntaxError(ExcelProcessorError):
    """Exception raised when SQL syntax is invalid."""
    
    def __init__(self, query: str, message: str, position: int = None, suggestion: str = None):
        self.query = query
        self.position = position
        self.suggestion = suggestion
        super().__init__(message)
    
    def __str__(self) -> str:
        base_msg = f"SQL Syntax Error: {self.message}"
        if self.position is not None:
            base_msg += f" at position {self.position}"
        base_msg += f"\nQuery: {self.query}"
        if self.suggestion:
            base_msg += f"\nSuggestion: {self.suggestion}"
        return base_msg


class DataProcessingError(ExcelProcessorError):
    """Exception raised during data processing operations."""
    
    def __init__(self, operation: str, message: str, details: str = None):
        self.operation = operation
        super().__init__(message, details)
    
    def __str__(self) -> str:
        base_msg = f"Data Processing Error in {self.operation}: {self.message}"
        if self.details:
            base_msg += f"\nDetails: {self.details}"
        return base_msg


class TableNotFoundError(ExcelProcessorError):
    """Exception raised when a referenced table (file.sheet) is not found."""
    
    def __init__(self, file_name: str, sheet_name: str = None):
        self.file_name = file_name
        self.sheet_name = sheet_name
        
        if sheet_name:
            message = f"Sheet '{sheet_name}' not found in file '{file_name}'"
        else:
            message = f"File '{file_name}' not found in database directory"
        
        super().__init__(message)


class ColumnNotFoundError(ExcelProcessorError):
    """Exception raised when a referenced column is not found."""
    
    def __init__(self, column_name: str, table_ref: str = None, available_columns: list = None):
        self.column_name = column_name
        self.table_ref = table_ref
        self.available_columns = available_columns or []
        
        if table_ref:
            message = f"Column '{column_name}' not found in table '{table_ref}'"
        else:
            message = f"Column '{column_name}' not found"
        
        if self.available_columns:
            message += f"\nAvailable columns: {', '.join(self.available_columns)}"
        
        super().__init__(message)


class JoinError(DataProcessingError):
    """Exception raised during JOIN operations."""
    
    def __init__(self, message: str, left_table: str = None, right_table: str = None, details: str = None):
        self.left_table = left_table
        self.right_table = right_table
        super().__init__("JOIN", message, details)
    
    def __str__(self) -> str:
        base_msg = f"JOIN Error: {self.message}"
        if self.left_table and self.right_table:
            base_msg += f" between '{self.left_table}' and '{self.right_table}'"
        if self.details:
            base_msg += f"\nDetails: {self.details}"
        return base_msg


class DatabaseDirectoryError(ExcelProcessorError):
    """Exception raised when database directory operations fail."""
    
    def __init__(self, directory_path: str, message: str, details: str = None):
        self.directory_path = directory_path
        super().__init__(message, details)
    
    def __str__(self) -> str:
        base_msg = f"Database Directory Error for '{self.directory_path}': {self.message}"
        if self.details:
            base_msg += f"\nDetails: {self.details}"
        return base_msg


class MemoryError(ExcelProcessorError):
    """Exception raised when memory usage exceeds limits."""
    
    def __init__(self, current_usage: float, limit: float, operation: str = None):
        self.current_usage = current_usage
        self.limit = limit
        self.operation = operation
        
        message = f"Memory usage ({current_usage:.2f} MB) exceeds limit ({limit:.2f} MB)"
        if operation:
            message += f" during {operation}"
        
        super().__init__(message)


class CSVExportError(ExcelProcessorError):
    """Exception raised during CSV export operations."""
    
    def __init__(self, file_path: str, message: str, details: str = None):
        self.file_path = file_path
        super().__init__(message, details)
    
    def __str__(self) -> str:
        base_msg = f"CSV Export Error for '{self.file_path}': {self.message}"
        if self.details:
            base_msg += f"\nDetails: {self.details}"
        return base_msg