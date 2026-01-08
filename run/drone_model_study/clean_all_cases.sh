#!/bin/bash
# Clean all OpenFOAM cases in the drone_model_study directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Cleaning all OpenFOAM cases"
echo "=========================================="
echo ""

CASES=("case_front_back" "case_left_right" "case_top_down")

for case in "${CASES[@]}"; do
    if [ -d "$case" ]; then
        echo "Cleaning $case..."
        if [ -f "$case/Allclean" ]; then
            cd "$case"
            bash ./Allclean
            cd ..
            echo "  $case cleaned successfully"
        else
            echo "  Warning: Allclean not found in $case"
        fi
        echo ""
    else
        echo "  Warning: Case directory $case not found"
        echo ""
    fi
done

echo "=========================================="
echo "All cases cleaned"
echo "=========================================="

