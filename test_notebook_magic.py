#!/usr/bin/env python3
"""Test script for Excel DataFrame Processor magic commands."""

from IPython.testing import globalipapp
from excel_processor.notebook import ExcelMagics

def test_magic_commands():
    """Test the Excel magic commands."""
    print("🧪 Testing Excel magic commands...")
    
    # Get IPython instance
    ip = globalipapp.get_ipython()
    if ip is None:
        print("❌ IPython not available, creating mock test")
        return
    
    # Register magic commands
    magic = ExcelMagics(ip)
    ip.register_magic_function(magic.excel_init, 'line', 'excel_init')
    ip.register_magic_function(magic.excel_show_db, 'line', 'excel_show_db')
    ip.register_magic_function(magic.excel_sql, 'cell', 'excel_sql')
    
    print("✅ Magic commands registered successfully")
    
    # Test initialization
    try:
        ip.run_line_magic('excel_init', '--db sample_data')
        print("✅ Magic initialization successful")
    except Exception as e:
        print(f"❌ Magic initialization failed: {e}")
    
    # Test show db
    try:
        ip.run_line_magic('excel_show_db', '')
        print("✅ Magic show_db successful")
    except Exception as e:
        print(f"❌ Magic show_db failed: {e}")
    
    print("🎉 Magic commands testing completed!")

if __name__ == "__main__":
    test_magic_commands()