#!/bin/bash
# Backend API Surface Analysis
# FIXED: Uses -E flag for extended regex

echo "======================================================================"
echo "BACKEND API SURFACE ANALYSIS"
echo "======================================================================"

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

echo -e "\n📋 Analyzing backend API methods..."

# FIXED: Use -E for extended regex (OR operator)
grep -R -n -E 'def (run|simulate|calculate|export|generate)\b' \
    backend apps --include="*.py" > backend_api_surface.txt

if [ -s backend_api_surface.txt ]; then
    echo "✅ Found API methods (saved to backend_api_surface.txt):"
    head -20 backend_api_surface.txt
    line_count=$(wc -l < backend_api_surface.txt)
    if [ "$line_count" -gt 20 ]; then
        echo "... and $((line_count - 20)) more"
    fi
else
    echo "⚠️  No API methods found"
fi

echo -e "\n📋 Analyzing data structures (Config, Result, Response classes)..."

# FIXED: Use -E for extended regex
grep -R -n -E 'class.*(Config|Result|Response|Schema)\b' \
    backend apps src --include="*.py" > backend_data_structures.txt

if [ -s backend_data_structures.txt ]; then
    echo "✅ Found data structures (saved to backend_data_structures.txt):"
    cat backend_data_structures.txt
else
    echo "⚠️  No explicit data structure classes found"
    echo "   (Implementation may use plain dicts)"
fi

echo -e "\n======================================================================"
echo "✅ Analysis complete"
echo "======================================================================"
echo ""
echo "Output files:"
echo "  - backend_api_surface.txt"
echo "  - backend_data_structures.txt"
echo ""
