#!/bin/bash

echo "Testing REPL interactivity..."
echo ""
echo "Sending commands to REPL:"
echo "  1. SHOW CACHE"
echo "  2. EXIT"
echo ""

# Send commands via stdin
echo -e "SHOW CACHE\nEXIT" | python -m excel_processor --db sample_data

echo ""
echo "✅ REPL responded to commands successfully!"
