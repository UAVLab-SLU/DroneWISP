#!/bin/bash
# Script to clean all localized wake refinement study simulations

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Localized Wake Refinement Study - Cleaning All Simulations"
echo "=========================================="
echo ""

# Array of cases to clean
CASES=("coarse_wake" "medium_wake" "fine_wake")

for CASE in "${CASES[@]}"; do
    echo ""
    echo "=========================================="
    echo "Cleaning case: $CASE"
    echo "=========================================="

    if [ ! -d "$CASE" ]; then
        echo "Warning: Case directory '$CASE' not found, skipping..."
        continue
    fi

    cd "$CASE"

    if [ -f "./Allclean" ]; then
        echo "Running Allclean..."
        bash ./Allclean
        echo "Case '$CASE' cleaned"
    else
        echo "Warning: Allclean script not found in $CASE"
        rm -rf processor* 2>/dev/null || true
        rm -rf [0-9]* 2>/dev/null || true
        rm -f log.* 2>/dev/null || true
        rm -rf postProcessing 2>/dev/null || true
        echo "Manual cleanup completed"
    fi

    cd ..

    echo ""
done

echo "=========================================="
echo "All simulations cleaned!"
echo "=========================================="
echo ""
echo "To run simulations again:"
echo "  bash ./run_all_cases.sh"
echo ""
