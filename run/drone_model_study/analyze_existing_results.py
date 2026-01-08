#!/usr/bin/env python3
"""
Analyze existing OpenFOAM simulation results without re-running.

This script:
1. Checks for existing postProcessing results
2. Extracts force data
3. Reports detailed information about what was found
4. Helps debug why forces might be zero
"""

import os
import sys
import re
from pathlib import Path

def analyze_case_results(case_dir):
    """
    Analyze existing results in a case directory.
    
    Args:
        case_dir: Path to OpenFOAM case directory
    """
    case_path = Path(case_dir)
    
    print(f"\n{'='*70}")
    print(f"Analyzing: {case_path.name}")
    print(f"{'='*70}")
    
    # Check for postProcessing
    postproc = case_path / "postProcessing"
    if not postproc.exists():
        print("[ERROR] No postProcessing directory found")
        return None
    
    print(f"[OK] Found postProcessing directory")
    
    # Check forces1
    forces_dir = postproc / "forces1"
    if not forces_dir.exists():
        print("[ERROR] No forces1 directory found")
        return None
    
    print(f"[OK] Found forces1 directory")
    
    # Find time directories
    time_dirs = sorted([d for d in forces_dir.iterdir() if d.is_dir()], 
                      key=lambda x: float(x.name) if x.name.replace('.', '').replace('-', '').isdigit() else 0)
    
    if not time_dirs:
        print("[ERROR] No time directories in forces1")
        return None
    
    print(f"[OK] Found {len(time_dirs)} time directories: {[d.name for d in time_dirs]}")
    
    # Check latest time directory
    latest_time = time_dirs[-1]
    print(f"[INFO] Analyzing latest time: {latest_time.name}")
    
    forces_file = latest_time / "forces.dat"
    if not forces_file.exists():
        print(f"[ERROR] forces.dat not found in {latest_time.name}")
        return None
    
    print(f"[OK] Found forces.dat")
    
    # Read and analyze forces.dat
    print(f"\nReading forces.dat...")
    with open(forces_file, 'r') as f:
        lines = f.readlines()
    
    # Find header
    header_idx = None
    for i, line in enumerate(lines):
        if 'Time' in line and ('force' in line.lower() or 'pressure' in line.lower()):
            header_idx = i
            break
    
    if header_idx is None:
        print("[ERROR] Could not find header in forces.dat")
        print("First 20 lines of file:")
        for i, line in enumerate(lines[:20]):
            print(f"  {i}: {line.rstrip()}")
        return None
    
    header = lines[header_idx].split()
    print(f"[OK] Found header at line {header_idx}: {header}")
    
    # Read all data lines
    data_lines = []
    for line in lines[header_idx + 1:]:
        if line.strip() and not line.strip().startswith('#'):
            values = line.split()
            if len(values) >= len(header):
                data_lines.append(values)
    
    if not data_lines:
        print("[ERROR] No data lines found")
        return None
    
    print(f"[OK] Found {len(data_lines)} data lines")
    
    # Show first and last few lines
    print(f"\nFirst data line:")
    print(f"  {data_lines[0]}")
    print(f"\nLast data line (time {data_lines[-1][0]}):")
    print(f"  {data_lines[-1]}")
    
    # Parse last line using regex (more reliable for nested vectors)
    last_line = data_lines[-1]
    
    # Join the data line back together to handle split vectors
    data_str = ' '.join(last_line[1:])  # Skip time value
    
    # Extract force vectors using regex
    import re
    
    # Find the first pair of vectors (forces)
    # Pattern: ((num num num) (num num num))
    force_match = re.search(r'\(\(([^)]+)\)\s+\(([^)]+)\)\)', data_str)
    if force_match:
        pressure_str = force_match.group(1)
        viscous_str = force_match.group(2)
        
        try:
            pressure_components = [float(x) for x in pressure_str.split()]
            viscous_components = [float(x) for x in viscous_str.split()]
            
            forces = {
                'forces(pressure)': pressure_components,
                'forces(viscous)': viscous_components
            }
            
            print(f"  forces(pressure): {pressure_components}")
            print(f"  forces(viscous): {viscous_components}")
        except Exception as e:
            print(f"  Error parsing vectors: {e}")
            forces = {}
    else:
        print(f"  Could not find force vectors in data")
        forces = {}
    
    # Calculate force components
    force_pressure = None
    force_viscous = None
    
    for key, value in forces.items():
        if isinstance(value, list) and len(value) >= 3:
            if 'pressure' in key.lower():
                force_pressure = value
            elif 'viscous' in key.lower():
                force_viscous = value
    
    force_x = 0.0
    force_y = 0.0
    force_z = 0.0
    
    if force_pressure:
        print(f"\nPressure force: {force_pressure}")
        force_x += force_pressure[0]
        force_y += force_pressure[1]
        force_z += force_pressure[2]
    
    if force_viscous:
        print(f"Viscous force: {force_viscous}")
        force_x += force_viscous[0]
        force_y += force_viscous[1]
        force_z += force_viscous[2]
    
    force_magnitude = (force_x**2 + force_y**2 + force_z**2)**0.5
    
    print(f"\n{'='*70}")
    print("FORCE SUMMARY:")
    print(f"{'='*70}")
    print(f"  Fx = {force_x:.6f} N")
    print(f"  Fy = {force_y:.6f} N")
    print(f"  Fz = {force_z:.6f} N")
    print(f"  |F| = {force_magnitude:.6f} N")
    
    # Check mesh and patch
    print(f"\n{'='*70}")
    print("MESH INFORMATION:")
    print(f"{'='*70}")
    
    boundary_file = case_path / "constant" / "polyMesh" / "boundary"
    if boundary_file.exists():
        print(f"[OK] Found boundary file")
        with open(boundary_file, 'r') as f:
            boundary_content = f.read()
            if 'combined' in boundary_content:
                print(f"[OK] 'combined' patch found in boundary file")
                # Extract combined patch info
                import re
                match = re.search(r'combined\s*\{[^}]*nFaces\s+(\d+)', boundary_content)
                if match:
                    n_faces = match.group(1)
                    print(f"[INFO] Combined patch has {n_faces} faces")
            else:
                print(f"[WARNING] 'combined' patch NOT found in boundary file")
                # List all patches
                patches = re.findall(r'(\w+)\s*\{[^}]*type', boundary_content)
                print(f"[INFO] Available patches: {patches}")
    else:
        print(f"[ERROR] Boundary file not found")
    
    # Check forces configuration
    forces_config = case_path / "system" / "forces"
    if forces_config.exists():
        print(f"\n[OK] Found forces configuration")
        with open(forces_config, 'r') as f:
            forces_config_content = f.read()
            if 'combined' in forces_config_content:
                print(f"[OK] 'combined' patch configured in forces")
            else:
                print(f"[WARNING] 'combined' patch NOT in forces configuration")
                print(f"Forces config content:")
                print(forces_config_content)
    
    return {
        'force_x': force_x,
        'force_y': force_y,
        'force_z': force_z,
        'force_magnitude': force_magnitude,
        'forces': forces
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_existing_results.py <case_directory>")
        print("Example: python3 analyze_existing_results.py case_front_back")
        sys.exit(1)
    
    case_dir = sys.argv[1]
    result = analyze_case_results(case_dir)
    
    if result is None:
        print("\n[ERROR] Analysis failed")
        sys.exit(1)
    else:
        print("\n[OK] Analysis complete")

