#!/usr/bin/env python
"""Test REPL with simulated interactive input."""

import sys
import time
from pathlib import Path
from io import StringIO
from unittest.mock import patch

# Simulate user typing commands
simulated_input = """SHOW CACHE
EXIT
"""

print("Testing REPL with simulated input...")
print("=" * 80)
print("Simulated commands:")
print(simulated_input)
print("=" * 80)

# Patch stdin to simulate user input
with patch('sys.stdin', StringIO(simulated_input)):
    try:
        from excel_processor.repl import ExcelREPL
        repl = ExcelREPL(db_directory=Path("sample_data"), memory_limit_mb=1024.0)
        
        print("\n✅ REPL initialized")
        print("Starting REPL loop...")
        
        # This should process the commands and exit
        repl.start()
        
        print("\n✅ REPL completed successfully!")
    except EOFError:
        print("\n✅ REPL exited (EOF reached)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
