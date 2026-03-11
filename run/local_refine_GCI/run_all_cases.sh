#!/bin/bash
# Script to run all localized wake refinement study simulations sequentially

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Localized Wake Refinement Study - Running Simulations"
echo "=========================================="
echo ""

# Array of cases to run (in order: coarse to fine wake refinement)
CASES=("coarse_wake" "medium_wake" "fine_wake")

for CASE in "${CASES[@]}"; do
    echo ""
    echo "=========================================="
    echo "Running case: $CASE"
    echo "=========================================="

    if [ ! -d "$CASE" ]; then
        echo "Error: Case directory '$CASE' not found!"
        exit 1
    fi

    cd "$CASE"

    echo "Cleaning previous results..."
    bash ./Allclean

    echo "Starting simulation..."
    START_TIME=$(date +%s)
    bash ./Allrun
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))

    echo ""
    echo "Case '$CASE' completed in $ELAPSED seconds ($(($ELAPSED / 60)) minutes)"

    # Check if results exist
    if [ -d "postProcessing/forceCoeffs1" ]; then
        echo "Results found in postProcessing/"
    else
        echo "Warning: No postProcessing results found!"
    fi

    cd ..

    echo ""
done

echo "=========================================="
echo "All simulations completed!"
echo "=========================================="
echo ""
echo "Next step: Run the convergence analysis:"
echo "  cd $SCRIPT_DIR"
echo "  python local_refine_analysis.py coarse_wake medium_wake fine_wake --output results"
echo ""
