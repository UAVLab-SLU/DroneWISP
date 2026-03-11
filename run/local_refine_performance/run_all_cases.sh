#!/bin/bash
# Run both cases and record timing for performance comparison

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Local Refinement Performance Comparison"
echo "=========================================="
echo ""

CASES=("fine_uniform" "coarse_local_wake")
TIMING_FILE="$SCRIPT_DIR/results/timing.txt"
mkdir -p results

> "$TIMING_FILE"

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
    echo "$CASE $ELAPSED" >> "$TIMING_FILE"

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
echo "Timing saved to results/timing.txt"
echo ""
echo "Next step: Run the analysis:"
echo "  cd $SCRIPT_DIR"
echo "  python performance_analysis.py"
echo ""
