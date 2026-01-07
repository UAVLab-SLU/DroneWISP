#!/bin/bash
# Script to run all grid convergence study simulations sequentially

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Grid Convergence Study - Running Simulations"
echo "=========================================="
echo ""

# Array of cases to run (in order: coarse to fine)
CASES=("coarse" "medium" "fine")

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
    echo "✓ Case '$CASE' completed in $ELAPSED seconds ($(($ELAPSED / 60)) minutes)"
    
    # Check if results exist
    if [ -d "postProcessing/forceCoeffs1" ]; then
        echo "✓ Results found in postProcessing/"
    else
        echo "⚠ Warning: No postProcessing results found!"
    fi
    
    cd ..
    
    echo ""
done

echo "=========================================="
echo "All simulations completed!"
echo "=========================================="
echo ""
echo "Next step: Run the convergence analysis:"
echo "  cd /home/bohanzhang/DroneWISP/run"
echo "  python grid_convergence_analysis.py \\"
echo "      grid_conv_study/coarse \\"
echo "      grid_conv_study/medium \\"
echo "      grid_conv_study/fine \\"
echo "      --output grid_conv_study/results"
echo ""

