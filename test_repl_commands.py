#!/usr/bin/env python3
"""Test script for REPL commands without interactive input."""

from excel_processor.repl import ExcelREPL
from pathlib import Path
import sys

def test_repl_commands():
    """Test REPL commands programmatically."""
    print("🧪 Testing REPL commands...")
    
    try:
        # Initialize REPL
        repl = ExcelREPL(Path('sample_data'))
        print("✅ REPL initialized")
        
        # Test special commands
        print("\n📋 Testing SHOW DB command...")
        repl._handle_show_db()
        
        print("\n💾 Testing SHOW MEMORY command...")
        repl._handle_show_memory()
        
        print("\n📚 Testing LOAD DB command...")
        repl._handle_load_db()
        
        print("\n💾 Testing SHOW MEMORY after loading...")
        repl._handle_show_memory()
        
        print("\n🔍 Testing SQL query...")
        repl._handle_sql_query("SELECT * FROM employees.staff")
        
        print("\n🔍 Testing filtered SQL query...")
        repl._handle_sql_query("SELECT name, salary FROM employees.staff WHERE salary > 70000")
        
        print("\n🔍 Testing ORDER BY query...")
        repl._handle_sql_query("SELECT name, department, salary FROM employees.staff ORDER BY salary DESC")
        
        print("\n🎉 All REPL commands tested successfully!")
        
    except Exception as e:
        print(f"❌ REPL testing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_repl_commands()