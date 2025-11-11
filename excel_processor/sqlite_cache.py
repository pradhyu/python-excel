"""
SQLite caching layer for Excel DataFrame Processor
Converts Excel/CSV files to SQLite for faster query performance
"""

import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SQLiteCache:
    """
    SQLite-based caching layer for Excel/CSV files
    Provides significant performance improvements for repeated queries
    """
    
    def __init__(self, cache_dir: str = '.excel_cache', enabled: bool = True):
        """
        Initialize SQLite cache
        
        Args:
            cache_dir: Directory to store SQLite cache files
            enabled: Whether caching is enabled
        """
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        self.connections: Dict[str, sqlite3.Connection] = {}
        self.metadata: Dict[str, dict] = {}
        
        if self.enabled:
            self.cache_dir.mkdir(exist_ok=True)
            logger.info(f"SQLite cache initialized at {self.cache_dir}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Generate hash of file for cache validation"""
        stat = file_path.stat()
        hash_input = f"{file_path.name}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _get_cache_path(self, file_name: str) -> Path:
        """Get SQLite cache file path for given Excel file"""
        safe_name = file_name.replace('.', '_').replace(' ', '_')
        return self.cache_dir / f"{safe_name}.db"
    
    def _get_metadata_path(self, file_name: str) -> Path:
        """Get metadata file path"""
        safe_name = file_name.replace('.', '_').replace(' ', '_')
        return self.cache_dir / f"{safe_name}.meta.json"
    
    def is_cached(self, file_path: Path) -> bool:
        """Check if file is cached and cache is valid"""
        if not self.enabled:
            return False
        
        cache_path = self._get_cache_path(file_path.name)
        meta_path = self._get_metadata_path(file_path.name)
        
        if not cache_path.exists() or not meta_path.exists():
            return False
        
        # Check if cache is still valid
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            current_hash = self._get_file_hash(file_path)
            return metadata.get('file_hash') == current_hash
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
            return False
    
    def cache_file(self, file_path: Path, sheets_data: Dict[str, pd.DataFrame]) -> bool:
        """
        Cache Excel file data to SQLite
        
        Args:
            file_path: Path to Excel/CSV file
            sheets_data: Dictionary of sheet_name -> DataFrame
            
        Returns:
            True if caching successful
        """
        if not self.enabled:
            return False
        
        try:
            cache_path = self._get_cache_path(file_path.name)
            
            # Remove existing cache
            if cache_path.exists():
                cache_path.unlink()
            
            # Create SQLite database
            conn = sqlite3.connect(str(cache_path))
            
            # Store each sheet as a table
            for sheet_name, df in sheets_data.items():
                # Sanitize table name
                table_name = sheet_name.replace(' ', '_').replace('.', '_')
                
                # Convert DataFrame to SQLite
                df.to_sql(table_name, conn, index=False, if_exists='replace')
                
                # Create indexes on common columns
                self._create_indexes(conn, table_name, df)
            
            conn.commit()
            conn.close()
            
            # Save metadata
            metadata = {
                'file_name': file_path.name,
                'file_hash': self._get_file_hash(file_path),
                'cached_at': datetime.now().isoformat(),
                'sheets': list(sheets_data.keys()),
                'row_counts': {name: len(df) for name, df in sheets_data.items()}
            }
            
            with open(self._get_metadata_path(file_path.name), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Cached {file_path.name} with {len(sheets_data)} sheets to SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Error caching file {file_path.name}: {e}")
            return False
    
    def _create_indexes(self, conn: sqlite3.Connection, table_name: str, df: pd.DataFrame):
        """Create indexes on numeric and date columns for faster queries"""
        try:
            cursor = conn.cursor()
            
            # Get column types
            for col in df.columns:
                dtype = df[col].dtype
                
                # Create index on numeric columns
                if pd.api.types.is_numeric_dtype(dtype):
                    safe_col = col.replace(' ', '_').replace('.', '_')
                    index_name = f"idx_{table_name}_{safe_col}"
                    try:
                        cursor.execute(f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table_name}" ("{col}")')
                    except:
                        pass  # Column name might have special characters
                
                # Create index on datetime columns
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    safe_col = col.replace(' ', '_').replace('.', '_')
                    index_name = f"idx_{table_name}_{safe_col}"
                    try:
                        cursor.execute(f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table_name}" ("{col}")')
                    except:
                        pass
            
            conn.commit()
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def get_connection(self, file_name: str) -> Optional[sqlite3.Connection]:
        """Get SQLite connection for cached file"""
        if not self.enabled:
            return None
        
        cache_path = self._get_cache_path(file_name)
        
        if not cache_path.exists():
            return None
        
        # Reuse existing connection or create new one
        if file_name not in self.connections:
            try:
                conn = sqlite3.connect(str(cache_path))
                # Enable query optimization
                conn.execute("PRAGMA query_only = ON")
                conn.execute("PRAGMA temp_store = MEMORY")
                conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
                self.connections[file_name] = conn
            except Exception as e:
                logger.error(f"Error connecting to cache: {e}")
                return None
        
        return self.connections.get(file_name)
    
    def query(self, file_name: str, sheet_name: str, sql_query: str) -> Optional[pd.DataFrame]:
        """
        Execute SQL query on cached data
        
        Args:
            file_name: Excel file name
            sheet_name: Sheet name
            sql_query: SQL query (without FROM clause)
            
        Returns:
            DataFrame with results or None if cache miss
        """
        if not self.enabled:
            return None
        
        conn = self.get_connection(file_name)
        if conn is None:
            return None
        
        try:
            # Sanitize table name
            table_name = sheet_name.replace(' ', '_').replace('.', '_')
            
            # Execute query
            df = pd.read_sql_query(sql_query, conn)
            return df
            
        except Exception as e:
            logger.warning(f"Cache query failed: {e}")
            return None
    
    def get_table_info(self, file_name: str, sheet_name: str) -> Optional[Dict]:
        """Get information about cached table"""
        conn = self.get_connection(file_name)
        if conn is None:
            return None
        
        try:
            table_name = sheet_name.replace(' ', '_').replace('.', '_')
            cursor = conn.cursor()
            
            # Get column info
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            row_count = cursor.fetchone()[0]
            
            return {
                'columns': [col[1] for col in columns],
                'row_count': row_count,
                'table_name': table_name
            }
            
        except Exception as e:
            logger.warning(f"Error getting table info: {e}")
            return None
    
    def clear_cache(self, file_name: Optional[str] = None):
        """Clear cache for specific file or all files"""
        if not self.enabled:
            return
        
        # Close connections
        if file_name:
            if file_name in self.connections:
                self.connections[file_name].close()
                del self.connections[file_name]
            
            # Remove cache files
            cache_path = self._get_cache_path(file_name)
            meta_path = self._get_metadata_path(file_name)
            
            if cache_path.exists():
                cache_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
            
            logger.info(f"Cleared cache for {file_name}")
        else:
            # Clear all
            for conn in self.connections.values():
                conn.close()
            self.connections.clear()
            
            # Remove all cache files
            for cache_file in self.cache_dir.glob("*.db"):
                cache_file.unlink()
            for meta_file in self.cache_dir.glob("*.meta.json"):
                meta_file.unlink()
            
            logger.info("Cleared all cache")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.enabled:
            return {'enabled': False}
        
        cache_files = list(self.cache_dir.glob("*.db"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        stats = {
            'enabled': True,
            'cache_dir': str(self.cache_dir),
            'cached_files': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'active_connections': len(self.connections)
        }
        
        # Get per-file stats
        file_stats = []
        for cache_file in cache_files:
            meta_file = cache_file.with_suffix('.meta.json')
            if meta_file.exists():
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                    
                    file_stats.append({
                        'file': metadata['file_name'],
                        'sheets': len(metadata['sheets']),
                        'rows': sum(metadata['row_counts'].values()),
                        'size_mb': cache_file.stat().st_size / (1024 * 1024),
                        'cached_at': metadata['cached_at']
                    })
                except:
                    pass
        
        stats['files'] = file_stats
        return stats
    
    def __del__(self):
        """Cleanup connections on deletion"""
        for conn in self.connections.values():
            try:
                conn.close()
            except:
                pass
