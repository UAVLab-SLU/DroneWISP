#!/bin/bash
# Script to fix all grid convergence study cases
# This ensures the 0 directory exists and is properly decomposed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source OpenFOAM
. /opt/openfoam10/etc/bashrc 2>/dev/null || {
    echo "Warning: Could not source OpenFOAM. Make sure OpenFOAM is installed."
}

CASES=("coarse" "medium" "fine")

for CASE in "${CASES[@]}"; do
    echo ""
    echo "=========================================="
    echo "Fixing case: $CASE"
    echo "=========================================="
    
    if [ ! -d "$CASE" ]; then
        echo "Error: Case directory '$CASE' not found!"
        exit 1
    fi
    
    cd "$CASE"
    
    # Ensure 0 directory exists
    if [ ! -d "0" ]; then
        echo "Copying 0 directory from tallBuilding..."
        cp -r "../tallBuilding/0" .
    fi
    
    # Clean processor directories and logs
    echo "Cleaning processor directories and logs..."
    rm -rf processor* log.* 2>/dev/null || true
    
    # Run blockMesh
    echo "Running blockMesh..."
    blockMesh > log.blockMesh 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ blockMesh completed"
    else
        echo "✗ blockMesh failed - check log.blockMesh"
        cd ..
        continue
    fi
    
    # Run decomposePar
    echo "Running decomposePar -copyZero..."
    decomposePar -copyZero > log.decomposePar 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ decomposePar completed"
    else
        echo "✗ decomposePar failed - check log.decomposePar"
        cd ..
        continue
    fi
    
    # Verify processor0/0/p exists
    if [ -f "processor0/0/p" ]; then
        echo "✓ Verified: processor0/0/p exists"
    else
        echo "✗ Warning: processor0/0/p not found after decomposePar"
    fi
    
    cd ..
    echo "✓ Case '$CASE' fixed"
done

echo ""
echo "=========================================="
echo "All cases fixed!"
echo "=========================================="
echo ""
echo "You can now run the simulations:"
echo "  bash ./run_all_simulations.sh"
echo ""

