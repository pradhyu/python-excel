#!/bin/bash

echo "================================================================================"
echo "Testing REPL Typing Responsiveness"
echo "================================================================================"
echo ""
echo "This test simulates typing commands to verify the REPL is responsive."
echo ""

# Test 1: Simple command
echo "Test 1: Typing 'SHOW CACHE'"
echo "----------------------------"
echo "SHOW CACHE" | timeout 3 python -m excel_processor --db sample_data 2>&1 | grep -E "excel>|Cache Statistics" | head -5
echo ""

# Test 2: SQL query
echo "Test 2: Typing SQL query"
echo "-------------------------"
echo "SELECT COUNT(*) FROM employees.xlsx.staff" | timeout 3 python -m excel_processor --db sample_data 2>&1 | grep -E "excel>|count" | head -5
echo ""

# Test 3: Multiple commands
echo "Test 3: Multiple commands in sequence"
echo "--------------------------------------"
(echo "SHOW DB"; sleep 0.5; echo "EXIT") | timeout 5 python -m excel_processor --db sample_data 2>&1 | grep -E "excel>|Database Contents" | head -5
echo ""

echo "================================================================================"
echo "✅ All tests completed!"
echo ""
echo "If you can see command responses above, the REPL is working."
echo "Try running manually: python -m excel_processor --db sample_data"
echo "================================================================================"
