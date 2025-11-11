#!/usr/bin/env python
"""Test script to demonstrate auto-caching in REPL."""

import subprocess
import time

print("=" * 80)
print("Testing REPL Auto-Cache Feature")
print("=" * 80)
print()
print("Starting REPL with massive dataset...")
print("The REPL will automatically cache all CSV files to SQLite on startup.")
print()
print("Once loaded, try these commands:")
print("  SHOW DB          - See all available files")
print("  SHOW CACHE       - View cache statistics")
print("  SELECT COUNT(*) as total FROM massive_employees.csv.default")
print("  SELECT department, COUNT(*) as count FROM massive_employees.csv.default GROUP BY department")
print()
print("=" * 80)
print()

# Start the REPL
subprocess.run(["python", "-m", "excel_processor", "--db", "massive_data"])
