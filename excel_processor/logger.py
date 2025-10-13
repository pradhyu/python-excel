"""Logging utilities for Excel DataFrame Processor."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class REPLLogger:
    """Logger for REPL interactions and query history."""
    
    def __init__(self, db_directory: Path, log_level: str = "INFO"):
        """Initialize the REPL logger.
        
        Args:
            db_directory: Database directory path
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.db_directory = Path(db_directory)
        self.log_dir = self.db_directory / '.log'
        self.log_dir.mkdir(exist_ok=True)
        
        # Create session-specific log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log_file = self.log_dir / f"repl_session_{timestamp}.log"
        self.query_log_file = self.log_dir / "query_history.log"
        
        # Setup loggers
        self._setup_session_logger(log_level)
        self._setup_query_logger()
    
    def _setup_session_logger(self, log_level: str):
        """Setup session logger for general REPL activity."""
        self.session_logger = logging.getLogger(f"excel_repl_session_{id(self)}")
        self.session_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        for handler in self.session_logger.handlers[:]:
            self.session_logger.removeHandler(handler)
        
        # File handler for session log
        file_handler = logging.FileHandler(self.session_log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.session_logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.session_logger.propagate = False
    
    def _setup_query_logger(self):
        """Setup query logger for SQL query history."""
        self.query_logger = logging.getLogger(f"excel_query_history_{id(self)}")
        self.query_logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.query_logger.handlers[:]:
            self.query_logger.removeHandler(handler)
        
        # File handler for query history
        query_handler = logging.FileHandler(self.query_log_file, encoding='utf-8')
        query_formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        query_handler.setFormatter(query_formatter)
        self.query_logger.addHandler(query_handler)
        
        # Prevent propagation to root logger
        self.query_logger.propagate = False
    
    def log_session_start(self, memory_limit: float):
        """Log session start."""
        self.session_logger.info(f"=== REPL Session Started ===")
        self.session_logger.info(f"Database Directory: {self.db_directory}")
        self.session_logger.info(f"Memory Limit: {memory_limit} MB")
        self.session_logger.info(f"Log Directory: {self.log_dir}")
    
    def log_session_end(self):
        """Log session end."""
        self.session_logger.info("=== REPL Session Ended ===")
    
    def log_command(self, command: str, command_type: str = "COMMAND"):
        """Log a command execution.
        
        Args:
            command: The command that was executed
            command_type: Type of command (SQL, SHOW_DB, LOAD_DB, etc.)
        """
        self.session_logger.info(f"[{command_type}] {command}")
    
    def log_query(self, query: str, result_rows: int, execution_time: Optional[float] = None):
        """Log a SQL query execution.
        
        Args:
            query: SQL query that was executed
            result_rows: Number of rows returned
            execution_time: Execution time in seconds
        """
        time_info = f" ({execution_time:.3f}s)" if execution_time else ""
        log_message = f"QUERY: {query} | ROWS: {result_rows}{time_info}"
        
        self.query_logger.info(log_message)
        self.session_logger.info(f"[QUERY] {query} -> {result_rows} rows{time_info}")
    
    def log_error(self, error: str, query: Optional[str] = None):
        """Log an error.
        
        Args:
            error: Error message
            query: Query that caused the error (if applicable)
        """
        if query:
            self.session_logger.error(f"[ERROR] Query: {query} | Error: {error}")
            self.query_logger.error(f"ERROR: {query} | {error}")
        else:
            self.session_logger.error(f"[ERROR] {error}")
    
    def log_create_table(self, table_name: str, rows: int, columns: int):
        """Log CREATE TABLE AS execution.
        
        Args:
            table_name: Name of the created table
            rows: Number of rows in the table
            columns: Number of columns in the table
        """
        message = f"CREATED TABLE: {table_name} ({rows} rows × {columns} columns)"
        self.session_logger.info(f"[CREATE_TABLE] {message}")
        self.query_logger.info(message)
    
    def log_export(self, filename: str, rows: int):
        """Log CSV export.
        
        Args:
            filename: Name of the exported file
            rows: Number of rows exported
        """
        message = f"EXPORTED: {filename} ({rows} rows)"
        self.session_logger.info(f"[EXPORT] {message}")
        self.query_logger.info(message)
    
    def log_memory_usage(self, total_mb: float, usage_percent: float, files_loaded: int):
        """Log memory usage information.
        
        Args:
            total_mb: Total memory usage in MB
            usage_percent: Memory usage percentage
            files_loaded: Number of files loaded
        """
        message = f"MEMORY: {total_mb:.2f} MB ({usage_percent:.1f}%) | Files: {files_loaded}"
        self.session_logger.info(f"[MEMORY] {message}")
    
    def get_log_files(self) -> dict:
        """Get information about log files.
        
        Returns:
            Dictionary with log file information
        """
        log_files = {}
        
        if self.session_log_file.exists():
            log_files['session'] = {
                'path': str(self.session_log_file),
                'size': self.session_log_file.stat().st_size,
                'modified': datetime.fromtimestamp(self.session_log_file.stat().st_mtime)
            }
        
        if self.query_log_file.exists():
            log_files['query_history'] = {
                'path': str(self.query_log_file),
                'size': self.query_log_file.stat().st_size,
                'modified': datetime.fromtimestamp(self.query_log_file.stat().st_mtime)
            }
        
        return log_files
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files.
        
        Args:
            days_to_keep: Number of days to keep log files
        """
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in self.log_dir.glob("repl_session_*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    self.session_logger.info(f"Cleaned up old log file: {log_file.name}")
                except Exception as e:
                    self.session_logger.warning(f"Failed to clean up {log_file.name}: {e}")