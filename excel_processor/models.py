"""Core data models for Excel DataFrame Processor."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Union
import pandas as pd


@dataclass
class ExcelFile:
    """Represents a loaded Excel file with its sheets."""
    file_name: str  # Just filename, not full path
    file_path: str  # Full path within db directory
    sheets: Dict[str, pd.DataFrame]
    last_modified: datetime
    memory_usage: float
    
    def get_sheet_names(self) -> List[str]:
        """Get list of sheet names in this Excel file."""
        return list(self.sheets.keys())
    
    def get_sheet(self, sheet_name: Union[str, int]) -> Optional[pd.DataFrame]:
        """Get a specific sheet by name or index."""
        if isinstance(sheet_name, int):
            sheet_names = list(self.sheets.keys())
            if 0 <= sheet_name < len(sheet_names):
                return self.sheets[sheet_names[sheet_name]]
            return None
        return self.sheets.get(sheet_name)


@dataclass
class QueryResult:
    """Represents the result of a SQL query execution."""
    dataframe: pd.DataFrame
    execution_time: float
    row_count: int
    column_count: int
    query: str
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, execution_time: float, query: str) -> 'QueryResult':
        """Create QueryResult from a DataFrame."""
        return cls(
            dataframe=df,
            execution_time=execution_time,
            row_count=len(df),
            column_count=len(df.columns),
            query=query
        )


@dataclass
class REPLSession:
    """Represents the current REPL session state."""
    db_directory: str
    loaded_files: Dict[str, ExcelFile]
    query_history: List[str]
    history_file_path: str
    color_enabled: bool
    
    def add_to_history(self, command: str) -> None:
        """Add a command to the history."""
        if command.strip() and (not self.query_history or self.query_history[-1] != command):
            self.query_history.append(command)
    
    def get_loaded_file_names(self) -> List[str]:
        """Get list of loaded file names."""
        return list(self.loaded_files.keys())


@dataclass
class DatabaseInfo:
    """Information about the database directory."""
    directory_path: str
    excel_files: Dict[str, List[str]]  # filename -> sheet names
    total_files: int
    loaded_files: int
    temp_tables: List[str] = None  # List of temporary table names
    
    @classmethod
    def create_empty(cls, directory_path: str) -> 'DatabaseInfo':
        """Create empty database info."""
        return cls(
            directory_path=directory_path,
            excel_files={},
            total_files=0,
            loaded_files=0,
            temp_tables=[]
        )


@dataclass
class TableReference:
    """Represents a table reference in SQL (file.sheet notation)."""
    file_name: str
    sheet_name: str
    alias: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of table reference."""
        base = f"{self.file_name}.{self.sheet_name}"
        return f"{base} AS {self.alias}" if self.alias else base


@dataclass
class ColumnReference:
    """Represents a column reference in SQL."""
    column_name: str
    table_alias: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of column reference."""
        if self.table_alias:
            return f"{self.table_alias}.{self.column_name}"
        return self.column_name


@dataclass
class Condition:
    """Represents a WHERE condition."""
    left: Union[str, ColumnReference]
    operator: str  # =, !=, <, >, <=, >=, LIKE, IN, etc.
    right: Union[str, int, float, List]
    
    def __str__(self) -> str:
        """String representation of condition."""
        return f"{self.left} {self.operator} {self.right}"


@dataclass
class JoinClause:
    """Represents a JOIN clause in SQL."""
    join_type: str  # INNER, LEFT, RIGHT, OUTER
    left_table: TableReference
    right_table: TableReference
    on_condition: Condition
    
    def __str__(self) -> str:
        """String representation of join clause."""
        return f"{self.join_type} JOIN {self.right_table} ON {self.on_condition}"


@dataclass
class WhereClause:
    """Represents a WHERE clause with multiple conditions."""
    conditions: List[Condition]
    logical_operators: List[str]  # AND, OR between conditions
    
    def __str__(self) -> str:
        """String representation of where clause."""
        if not self.conditions:
            return ""
        
        result = str(self.conditions[0])
        for i, condition in enumerate(self.conditions[1:], 1):
            if i - 1 < len(self.logical_operators):
                result += f" {self.logical_operators[i - 1]} {condition}"
            else:
                result += f" AND {condition}"
        return result


@dataclass
class OrderByClause:
    """Represents an ORDER BY clause."""
    columns: List[str]
    directions: List[str]  # ASC, DESC
    
    def __str__(self) -> str:
        """String representation of order by clause."""
        parts = []
        for i, column in enumerate(self.columns):
            direction = self.directions[i] if i < len(self.directions) else "ASC"
            parts.append(f"{column} {direction}")
        return "ORDER BY " + ", ".join(parts)