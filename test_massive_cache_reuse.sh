#!/bin/bash

echo "================================================================================"
echo "Testing Cache Reuse with Massive Dataset"
echo "================================================================================"
echo ""
echo "This test demonstrates:"
echo "  1. First run: Caches massive dataset (2M employees + 4M transactions)"
echo "  2. Second run: Reuses existing cache (instant startup)"
echo "  3. Query performance: Sub-second queries on 6M+ rows"
echo ""
echo "================================================================================"
echo ""

# Check if cache exists
if [ -d "massive_data/.excel_cache" ]; then
    echo "✓ Cache directory exists: massive_data/.excel_cache"
    echo ""
    echo "Cache contents:"
    ls -lh massive_data/.excel_cache/ | grep -E "\.db$|\.meta\.json$" | head -10
    echo ""
    echo "To test first-run behavior, delete the cache:"
    echo "  rm -rf massive_data/.excel_cache"
    echo ""
else
    echo "⚠ No cache found. This will be a first run (will take ~2 minutes to cache)."
    echo ""
fi

echo "================================================================================"
echo "Starting REPL..."
echo "================================================================================"
echo ""
echo "Try these commands once the REPL starts:"
echo "  SHOW CACHE"
echo "  SELECT COUNT(*) as total FROM massive_employees.csv.default"
echo "  SELECT department, COUNT(*) as count FROM massive_employees.csv.default GROUP BY department LIMIT 5"
echo "  EXIT"
echo ""
echo "================================================================================"
echo ""

# Start the REPL
python -m excel_processor --db massive_data
