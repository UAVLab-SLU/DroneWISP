#!/bin/bash
# Setup script to make Windows ParaView the default for paraFoam in WSL
# This script configures your shell to use Windows ParaView instead of WSL ParaView

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASHRC="$HOME/.bashrc"

echo "Setting up Windows ParaView as default for paraFoam..."
echo ""

# Function to find ParaView installation
find_paraview() {
    local found_path=""
    
    # Search in common Windows drive mount points (C through Z)
    for drive_letter in c d e f g h i j k l m n o p q r s t u v w x y z; do
        local drive="/mnt/$drive_letter"
        if [ -d "$drive" ]; then
            # Search for ParaView in common locations
            local search_paths=(
                "$drive/ParaView"*
                "$drive/Program Files/ParaView"*
                "$drive/Program Files (x86)/ParaView"*
            )
            
            for base_path in "${search_paths[@]}"; do
                # Expand glob pattern
                for pv_dir in $base_path; do
                    if [ -d "$pv_dir" ]; then
                        local exe_path="$pv_dir/bin/paraview.exe"
                        if [ -f "$exe_path" ]; then
                            found_path="$exe_path"
                            break 2
                        fi
                    fi
                done
            done
            
            # Also try direct find as fallback
            if [ -z "$found_path" ]; then
                local result=$(find "$drive" -maxdepth 5 -type f -name "paraview.exe" -path "*/ParaView*/bin/*" 2>/dev/null | head -1)
                if [ -n "$result" ] && [ -f "$result" ]; then
                    found_path="$result"
                    break
                fi
            fi
        fi
    done
    
    echo "$found_path"
}

# Find ParaView installation
echo "Searching for ParaView installation on Windows..."
PARAVIEW_EXE=$(find_paraview)

if [ -z "$PARAVIEW_EXE" ] || [ ! -f "$PARAVIEW_EXE" ]; then
    echo "Warning: Windows ParaView not found automatically."
    echo ""
    echo "Searched in: /mnt/c through /mnt/z"
    echo "Looking for: ParaView*/bin/paraview.exe"
    echo ""
    read -p "Enter ParaView path manually (e.g., /mnt/g/ParaView 5.13.2/bin/paraview.exe) or press Enter to skip: " manual_path
    if [ -n "$manual_path" ] && [ -f "$manual_path" ]; then
        PARAVIEW_EXE="$manual_path"
    elif [ -n "$manual_path" ]; then
        echo "Error: File not found at $manual_path"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        PARAVIEW_EXE="$manual_path"
    else
        echo "No ParaView path provided. The script will fall back to WSL paraFoam."
        PARAVIEW_EXE=""
    fi
else
    echo "Found ParaView at: $PARAVIEW_EXE"
fi
echo ""

# Get WSL distribution name
WSL_DISTRO=$(echo $WSL_DISTRO_NAME 2>/dev/null || echo "Ubuntu-22.04")
echo "Detected WSL distribution: $WSL_DISTRO"
echo ""

# Check if paraFoam function already exists in bashrc
if grep -q "^paraFoam()" "$BASHRC" 2>/dev/null; then
    echo "paraFoam function already exists in $BASHRC"
    read -p "Replace it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old paraFoam function
        sed -i '/^# Override paraFoam/,/^}$/d' "$BASHRC"
        echo "Removed old paraFoam function"
    else
        echo "Keeping existing function. Exiting."
        exit 0
    fi
fi

# Add paraFoam function to bashrc
cat >> "$BASHRC" << EOF

# Override paraFoam to use Windows ParaView (configured by setup_paraview_windows.sh)
paraFoam() {
    local CASE_DIR="\${1:-\$(pwd)}"
    CASE_DIR=\$(realpath "\$CASE_DIR" 2>/dev/null || echo "\$CASE_DIR")
    
    # Get WSL distribution name
    local WSL_DISTRO=\$(echo \$WSL_DISTRO_NAME 2>/dev/null || echo "$WSL_DISTRO")
    
    # Windows ParaView executable (configured during setup)
    local PARAVIEW_EXE="$PARAVIEW_EXE"
    
    # Check if Windows ParaView exists
    if [ ! -f "\$PARAVIEW_EXE" ]; then
        echo "Error: Windows ParaView not found at \$PARAVIEW_EXE"
        echo "Falling back to WSL paraFoam..."
        if command -v /opt/openfoam10/bin/paraFoam >/dev/null 2>&1; then
            /opt/openfoam10/bin/paraFoam "\$@"
        else
            echo "Error: Neither Windows ParaView nor WSL paraFoam found"
            return 1
        fi
        return \$?
    fi
    
    # Ensure results.foam exists
    if [ ! -f "\$CASE_DIR/results.foam" ]; then
        echo "Creating results.foam file..."
        touch "\$CASE_DIR/results.foam"
    fi
    
    # Convert WSL path to Windows network path
    local WIN_PATH_RAW=\$(echo "\$CASE_DIR" | sed 's|/|\\\\|g')
    local WIN_PATH="\\\\\\\\wsl.localhost\\\\\${WSL_DISTRO}\${WIN_PATH_RAW}"
    
    # Launch ParaView with the case file
    echo "Opening Windows ParaView with case: \$CASE_DIR"
    "\$PARAVIEW_EXE" "\${WIN_PATH}\\\\results.foam" &
}
EOF

echo "Successfully added paraFoam function to $BASHRC"
echo ""
echo "The function will:"
echo "  1. Use Windows ParaView at: $PARAVIEW_EXE"
echo "  2. Automatically convert WSL paths to Windows network paths"
echo "  3. Fall back to WSL paraFoam if Windows ParaView is not found"
echo ""
echo "To use it in the current shell, run:"
echo "  source $BASHRC"
echo ""
echo "Or open a new terminal window."
echo ""
echo "Usage:"
echo "  cd /path/to/openfoam/case"
echo "  paraFoam"

