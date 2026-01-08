#!/usr/bin/env python3
"""
Analyze drone model by running 3 principal direction simulations.

This script:
1. Takes a drone STL model name
2. Copies STL to 3 pre-existing OpenFOAM cases (front_back, left_right, top_down)
3. Runs each simulation
4. Extracts force magnitudes from each simulation
5. Calculates force coefficients and reports results

Usage:
    ../../python/venv/bin/python3 analyze_drone_model.py <stl_file>
"""

import os
import sys
import math
import shutil
import subprocess
from pathlib import Path

# Case directories for principal directions
CASES = {
    'front_back': {
        'name': 'Front-Back (X-direction)',
        'case_dir': 'case_front_back',
        'description': 'Wind along X-axis (forward/backward)'
    },
    'left_right': {
        'name': 'Left-Right (Y-direction)',
        'case_dir': 'case_left_right',
        'description': 'Wind along Y-axis (left/right)'
    },
    'top_down': {
        'name': 'Top-Down (Z-direction)',
        'case_dir': 'case_top_down',
        'description': 'Wind along Z-axis (up/down)'
    }
}

def clean_case(case_dir):
    """
    Clean an OpenFOAM case by running Allclean script.
    
    Args:
        case_dir: Path to OpenFOAM case directory
    
    Returns:
        bool: True if cleaning succeeded or Allclean doesn't exist
    """
    case_path = Path(case_dir).resolve()
    allclean = case_path / "Allclean"
    
    if not allclean.exists():
        # If Allclean doesn't exist, that's okay - just return True
        return True
    
    try:
        result = subprocess.run(
            ['bash', './Allclean'],
            cwd=str(case_path),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for cleaning
        )
        
        if result.returncode == 0:
            print(f"[OK] Cleaned {case_path.name}")
            return True
        else:
            print(f"[WARNING] Allclean exited with code {result.returncode} for {case_path.name}")
            return True  # Continue anyway
    except subprocess.TimeoutExpired:
        print(f"[WARNING] Allclean timed out for {case_path.name}")
        return True  # Continue anyway
    except Exception as e:
        print(f"[WARNING] Error cleaning {case_path.name}: {e}")
        return True  # Continue anyway

def restore_initial_conditions(case_dir):
    """
    Restore initial condition files after cleaning.
    Each case should have its own 0/ directory with correct boundary conditions.
    
    Args:
        case_dir: Path to OpenFOAM case directory
    """
    case_path = Path(case_dir)
    case_name = case_path.name
    
    # Check if case has its own 0/ backup or use template
    zero_backup = case_path / "0.backup"
    template_dir = case_path.parent / "openfoam_case"
    template_zero = template_dir / "0"
    
    zero_dir = case_path / "0"
    
    # If 0/ doesn't exist, restore it
    if not zero_dir.exists():
        # First try case-specific backup
        if zero_backup.exists():
            import shutil
            shutil.copytree(zero_backup, zero_dir)
            print(f"[OK] Restored initial conditions from case backup")
        # Otherwise use template
        elif template_zero.exists():
            import shutil
            shutil.copytree(template_zero, zero_dir)
            print(f"[OK] Restored initial conditions from template")
        else:
            print(f"[WARNING] No source for initial conditions found")
            return
    else:
        # Check if required files exist
        required_files = ['p', 'U.orig', 'k', 'omega', 'nut']
        missing = [f for f in required_files if not (zero_dir / f).exists()]
        if missing:
            # Try to restore from backup first
            if zero_backup.exists():
                import shutil
                for file in missing:
                    src = zero_backup / file
                    dst = zero_dir / file
                    if src.exists():
                        shutil.copy2(src, dst)
                print(f"[OK] Restored missing files from backup: {', '.join(missing)}")
            elif template_zero.exists():
                import shutil
                for file in missing:
                    src = template_zero / file
                    dst = zero_dir / file
                    if src.exists():
                        shutil.copy2(src, dst)
                print(f"[OK] Restored missing files from template: {', '.join(missing)}")

def copy_stl_to_case(case_dir, stl_file):
    """
    Copy STL file to case geometry directory.
    
    Args:
        case_dir: Path to OpenFOAM case directory
        stl_file: Path to STL file
    """
    geometry_dir = Path(case_dir) / "constant" / "geometry"
    geometry_dir.mkdir(parents=True, exist_ok=True)
    target_stl = geometry_dir / "combined.stl"
    shutil.copy2(stl_file, target_stl)
    print(f"[OK] Copied STL to {Path(case_dir).name}")

def run_openfoam_case(case_dir):
    """
    Run an OpenFOAM case.
    
    Args:
        case_dir: Path to OpenFOAM case directory
    
    Returns:
        bool: True if simulation succeeded
    """
    case_path = Path(case_dir).resolve()
    allrun = case_path / "Allrun"
    
    if not allrun.exists():
        print(f"[ERROR] Allrun script not found in {case_dir}")
        return False
    
    print(f"Running OpenFOAM case: {case_path.name}...")
    
    try:
        # Run Allrun script using bash (it sources OpenFOAM itself)
        # Change to case directory and run Allrun with bash
        result = subprocess.run(
            ['bash', 'Allrun'],
            cwd=str(case_path),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        # Check for postProcessing directory (indicates simulation ran)
        postproc = case_path / "postProcessing"
        if postproc.exists():
            print(f"[OK] Simulation completed successfully")
            return True
        
        # Even if return code is non-zero, check if results exist
        if result.returncode != 0:
            print(f"[WARNING] Simulation exited with code {result.returncode}")
            if result.stdout:
                # Show last few lines of output
                lines = result.stdout.split('\n')
                print("Last output lines:")
                for line in lines[-5:]:
                    if line.strip():
                        print(f"  {line}")
            if result.stderr:
                print(f"Error output: {result.stderr[:500]}")
        
        # Check if any time directories exist (might indicate partial success)
        time_dirs = [d for d in case_path.iterdir() if d.is_dir() and d.name.replace('.', '').isdigit()]
        if time_dirs:
            print(f"[WARNING] Found time directories but no postProcessing - simulation may have failed")
        
        return False
            
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Simulation timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Error running simulation: {e}")
        return False

def extract_forces_from_case(case_dir):
    """
    Extract force data from OpenFOAM case results.
    
    Args:
        case_dir: Path to OpenFOAM case
    
    Returns:
        dict: Force data or None if not found
    """
    case_path = Path(case_dir)
    forces_dir = case_path / "postProcessing" / "forces1"
    
    if not forces_dir.exists():
        return None
    
    # Find latest time directory
    time_dirs = sorted([d for d in forces_dir.iterdir() if d.is_dir()], 
                      key=lambda x: float(x.name) if x.name.replace('.', '').replace('-', '').isdigit() else 0)
    if not time_dirs:
        return None
    
    time_dir = time_dirs[-1]
    forces_file = time_dir / "forces.dat"
    
    if not forces_file.exists():
        return None
    
    try:
        with open(forces_file, 'r') as f:
            lines = f.readlines()
        
        # Find header - look for line with Time and forces
        header_idx = None
        for i, line in enumerate(lines):
            if 'Time' in line and ('force' in line.lower() or 'pressure' in line.lower()):
                header_idx = i
                break
        
        if header_idx is None:
            return None
        
        # Parse header - it may have split fields like "forces(pressure" and "viscous)"
        header_line = lines[header_idx]
        # The header format is typically: "# Time forces(pressure viscous) moments(pressure viscous)"
        # When split, this becomes: ['#', 'Time', 'forces(pressure', 'viscous)', 'moments(pressure', 'viscous)']
        
        # Read last data line
        data_line = None
        for line in reversed(lines[header_idx + 1:]):
            if line.strip() and not line.strip().startswith('#'):
                values = line.split()
                if len(values) >= 2:  # At least Time and some data
                    data_line = values
                    break
        
        if data_line is None:
            return None
        
        # Parse the data line - it contains vectors in parentheses
        # Format: "Time ((px py pz) (vx vy vz)) ((mx my mz) (mx my mz))"
        # The forces are in the first pair: ((pressure) (viscous))
        
        # Join the data line back together to handle split vectors
        data_str = ' '.join(data_line[1:])  # Skip time value
        
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
                
                # Store with keys that match what calculate_force_magnitude expects
                forces = {
                    'forces(pressure)': pressure_components,
                    'forces(viscous)': viscous_components
                }
            except Exception as e:
                print(f"[DEBUG] Error parsing vectors: {e}")
                return None
        else:
            print(f"[DEBUG] Could not find force vectors in: {data_str[:200]}")
            return None
        
        return forces
        
    except Exception as e:
        print(f"Error reading forces: {e}")
        return None

def calculate_force_magnitude(forces):
    """
    Calculate force magnitude from forces dictionary.
    
    Args:
        forces: Dictionary of force data
    
    Returns:
        tuple: (force_magnitude, force_x, force_y, force_z)
    """
    force_x = 0.0
    force_y = 0.0
    force_z = 0.0
    
    if not forces:
        return 0.0, 0.0, 0.0, 0.0
    
    # Look for force vectors
    force_pressure = None
    force_viscous = None
    
    for key, value in forces.items():
        if 'forces(pressure)' in key.lower() or ('force' in key.lower() and 'pressure' in key.lower()):
            if isinstance(value, list) and len(value) >= 3:
                force_pressure = value
        elif 'forces(viscous)' in key.lower() or ('force' in key.lower() and 'viscous' in key.lower()):
            if isinstance(value, list) and len(value) >= 3:
                force_viscous = value
    
    if force_pressure:
        force_x += force_pressure[0]
        force_y += force_pressure[1]
        force_z += force_pressure[2]
    
    if force_viscous:
        force_x += force_viscous[0]
        force_y += force_viscous[1]
        force_z += force_viscous[2]
    
    if force_x != 0 or force_y != 0 or force_z != 0:
        force_magnitude = math.sqrt(force_x**2 + force_y**2 + force_z**2)
    else:
        force_magnitude = 0.0
    
    return force_magnitude, force_x, force_y, force_z

def run_case_and_extract(base_dir, case_key, case_info, stl_file, wind_speed=10.0):
    """
    Run a case and extract force results.
    
    Args:
        base_dir: Base directory
        case_key: Case key
        case_info: Case information dict
        stl_file: Path to STL file
        wind_speed: Wind speed (for reference)
    
    Returns:
        dict: Results or None if failed
    """
    case_dir = Path(base_dir) / case_info['case_dir']
    
    print(f"\n{'='*70}")
    print(f"Case: {case_info['name']}")
    print(f"Directory: {case_info['case_dir']}")
    print(f"{'='*70}")
    
    if not case_dir.exists():
        print(f"[ERROR] Case directory not found: {case_dir}")
        return None
    
    # Clean case first
    clean_case(str(case_dir))
    
    # Copy STL file
    copy_stl_to_case(str(case_dir), stl_file)
    
    # Run simulation
    success = run_openfoam_case(str(case_dir))
    
    if not success:
        return None
    
    # Extract forces
    forces = extract_forces_from_case(str(case_dir))
    force_magnitude, force_x, force_y, force_z = calculate_force_magnitude(forces)
    
    print(f"  Force components: Fx={force_x:.6f} N, Fy={force_y:.6f} N, Fz={force_z:.6f} N")
    print(f"  Force magnitude: {force_magnitude:.6f} N")
    
    return {
        'direction': case_info['name'],
        'wind_speed': wind_speed,
        'force_magnitude': force_magnitude,
        'force_x': force_x,
        'force_y': force_y,
        'force_z': force_z,
        'forces': forces
    }

def calculate_coefficients(results):
    """
    Calculate force coefficients from results.
    
    Args:
        results: Dictionary of results for each case
    
    Returns:
        dict: Force coefficients
    """
    coefficients = {}
    
    for case_key, case_info in CASES.items():
        if case_key not in results or results[case_key] is None:
            print(f"[WARNING] No result for {case_key}")
            coefficients[case_key] = {'simple': 0.0, 'force_at_10ms': 0.0}
            continue
        
        result = results[case_key]
        wind_speed = result['wind_speed']
        force_magnitude = result['force_magnitude']
        
        if wind_speed > 0:
            # Drag coefficient: D = F / V^2
            # This gives N/(m/s)^2 - drag coefficient for the blended drag model
            # Note: D includes the effect of (1/2 * rho * A) implicitly
            coeff_simple = force_magnitude / (wind_speed**2)
            
            # Calculate component-wise drag coefficients (D_x, D_y, D_z)
            # These are used in the corrected formula: F = -||V|| * [D_x*V_x, D_y*V_y, D_z*V_z]
            if case_key == 'front_back':
                # X-direction: D_x = F_x / V^2
                Dx = result['force_x'] / (wind_speed**2)
                Dy = 0.0
                Dz = 0.0
            elif case_key == 'left_right':
                # Y-direction: D_y = F_y / V^2
                Dx = 0.0
                Dy = result['force_y'] / (wind_speed**2)
                Dz = 0.0
            elif case_key == 'top_down':
                # Z-direction: D_z = F_z / V^2
                Dx = 0.0
                Dy = 0.0
                Dz = result['force_z'] / (wind_speed**2)
            else:
                Dx = Dy = Dz = 0.0
            
            coefficients[case_key] = {
                'simple': coeff_simple,
                'force_at_test_speed': force_magnitude,
                'Dx': Dx if case_key == 'front_back' else None,
                'Dy': Dy if case_key == 'left_right' else None,
                'Dz': Dz if case_key == 'top_down' else None,
                'force_x': result.get('force_x', 0.0) if case_key == 'front_back' else None,
                'force_y': result.get('force_y', 0.0) if case_key == 'left_right' else None,
                'force_z': result.get('force_z', 0.0) if case_key == 'top_down' else None
            }
        else:
            coefficients[case_key] = {'simple': 0.0, 'force_at_10ms': 0.0}
    
    return coefficients

def generate_formula(coefficients):
    """
    Generate wind force calculation formula.
    
    Args:
        coefficients: Dictionary of force coefficients
    
    Returns:
        str: Formula description
    """
    # Get component-wise coefficients
    front_back = coefficients.get('front_back', {})
    left_right = coefficients.get('left_right', {})
    top_down = coefficients.get('top_down', {})
    
    if isinstance(front_back, dict):
        Dx = front_back.get('Dx', front_back.get('simple', 0.0))
        Fx_ref = front_back.get('force_x', front_back.get('force_at_test_speed', 0.0))
    else:
        Dx = 0.0
        Fx_ref = 0.0
    
    if isinstance(left_right, dict):
        Dy = left_right.get('Dy', left_right.get('simple', 0.0))
        Fy_ref = left_right.get('force_y', left_right.get('force_at_test_speed', 0.0))
    else:
        Dy = 0.0
        Fy_ref = 0.0
    
    if isinstance(top_down, dict):
        Dz = top_down.get('Dz', top_down.get('simple', 0.0))
        Fz_ref = top_down.get('force_z', top_down.get('force_at_test_speed', 0.0))
    else:
        Dz = 0.0
        Fz_ref = 0.0
    
    formula = f"""
Wind Force Calculation Formula (Blended Drag Model):
====================================================

PHYSICS CORRECTION:
-------------------
The previous formula treated X, Y, Z drag independently, which is physically flawed.
The corrected formula uses TOTAL velocity magnitude to scale drag energy, while using
component velocities for direction and proportion.

WHAT THE NUMBERS MEAN:
----------------------
The simulations measure forces at 15 m/s wind in each principal direction:
  - Front-Back: Fx = {Fx_ref:.2f} N at 15 m/s → Dx = {Dx:.6f} N/(m/s)^2
  - Left-Right: Fy = {Fy_ref:.2f} N at 15 m/s → Dy = {Dy:.6f} N/(m/s)^2
  - Top-Down:   Fz = {Fz_ref:.2f} N at 15 m/s → Dz = {Dz:.6f} N/(m/s)^2

The drag coefficients (Dx, Dy, Dz) include the effect of (1/2 * rho * A) implicitly.
They represent the drag per (m/s)^2 when wind is purely in that direction.

CORRECTED FORMULA (Blended Drag Model):
---------------------------------------
For a wind with velocity components (vx, vy, vz) and total speed ||V|| = sqrt(vx^2 + vy^2 + vz^2):

  F_drag = -||V|| * [Dx*vx, Dy*vy, Dz*vz]

Component-wise:
  Fx = -||V|| * Dx * vx
  Fy = -||V|| * Dy * vy
  Fz = -||V|| * Dz * vz

Total force magnitude:
  F = sqrt(Fx^2 + Fy^2 + Fz^2)

Where:
  - Dx = {Dx:.6f} N/(m/s)^2  (Front-Back drag coefficient)
  - Dy = {Dy:.6f} N/(m/s)^2  (Left-Right drag coefficient)
  - Dz = {Dz:.6f} N/(m/s)^2  (Top-Down drag coefficient)
  - ||V|| = sqrt(vx^2 + vy^2 + vz^2) is the total wind speed magnitude

WHY THIS IS BETTER:
-------------------
Example: Drone falling at 20 m/s (vz=-20) while moving forward at 1 m/s (vx=1)
  - Old formula: Fx based only on 1 m/s → predicts almost zero X-drag
  - New formula: Fx = -||V|| * Dx * vx = -sqrt(1^2 + 20^2) * Dx * 1 ≈ -20 * Dx
  - Reality: The 20 m/s vertical flow creates turbulent wake, increasing X-drag
  - The new formula correctly accounts for total airflow energy

EXAMPLE: 15 m/s wind from 45 degrees (+x +y direction):
-------------------------------------------------------
  Wind vector: (10.607, 10.607, 0) m/s
  Total speed: ||V|| = 15.0 m/s
  
  Fx = -15.0 * {Dx:.6f} * 10.607 = {-15.0 * Dx * 10.607:.2f} N
  Fy = -15.0 * {Dy:.6f} * 10.607 = {-15.0 * Dy * 10.607:.2f} N
  Fz = -15.0 * {Dz:.6f} * 0.000 = 0.00 N
  
  Total force = sqrt(Fx^2 + Fy^2 + Fz^2)

Python implementation:
   import math
   
   def calculate_wind_force(vx, vy, vz, Dx={Dx:.6f}, Dy={Dy:.6f}, Dz={Dz:.6f}):
       V_mag = math.sqrt(vx**2 + vy**2 + vz**2)
       if V_mag == 0:
           return 0.0, 0.0, 0.0, 0.0
       
       # Blended drag model: F = -||V|| * [Dx*vx, Dy*vy, Dz*vz]
       Fx = -V_mag * Dx * vx
       Fy = -V_mag * Dy * vy
       Fz = -V_mag * Dz * vz
       
       F_magnitude = math.sqrt(Fx**2 + Fy**2 + Fz**2)
       
       return Fx, Fy, Fz, F_magnitude
"""
    return formula

def analyze_drone_model(stl_filename, base_dir=None, wind_speed=15.0):
    """
    Main function to analyze a drone model.
    
    Args:
        stl_filename: Name of STL file to analyze
        base_dir: Base directory (default: script directory)
        wind_speed: Reference wind speed (m/s)
    
    Returns:
        dict: Analysis results
    """
    if base_dir is None:
        base_dir = Path(__file__).parent
    else:
        base_dir = Path(base_dir)
    
    stl_source = Path(stl_filename)
    
    # Find STL file
    if not stl_source.is_absolute():
        stl_dir = base_dir / "stl"
        potential_path = stl_dir / stl_source
        if potential_path.exists():
            stl_source = potential_path
        elif not stl_source.exists():
            potential_path = stl_dir / f"{stl_source}.stl"
            if potential_path.exists():
                stl_source = potential_path
    
    if not stl_source.exists():
        raise FileNotFoundError(f"STL file not found: {stl_filename}")
    
    print("="*70)
    print("Drone Model Wind Force Analysis")
    print("="*70)
    print(f"STL Model: {stl_source.name}")
    print(f"Base Directory: {base_dir}")
    print(f"Reference Wind Speed: {wind_speed} m/s")
    
    # Run simulations for all cases
    print("\n[1/2] Running simulations...")
    results = {}
    
    for case_key, case_info in CASES.items():
        result = run_case_and_extract(
            str(base_dir),
            case_key,
            case_info,
            str(stl_source),
            wind_speed
        )
        results[case_key] = result
    
    # Calculate coefficients
    print("\n[2/2] Calculating coefficients and generating report...")
    coefficients = calculate_coefficients(results)
    
    # Generate report
    print("\n" + "="*70)
    print("ANALYSIS RESULTS")
    print("="*70)
    
    print("\nDrag Coefficients (N/(m/s)^2):")
    print("-" * 70)
    for case_key, case_info in CASES.items():
        coeff_data = coefficients.get(case_key, {})
        if isinstance(coeff_data, dict):
            simple_coeff = coeff_data.get('simple', 0.0)
            force_ref = coeff_data.get('force_at_test_speed', 0.0)
        else:
            simple_coeff = 0.0
            force_ref = 0.0
        
        print(f"{case_info['name']:30s}: D = {simple_coeff:10.6f}  (Force at 15 m/s: {force_ref:8.4f} N)")

    # Print formula
    formula = generate_formula(coefficients)
    print(formula)
    
    # Save results
    output_file = base_dir / f"{stl_source.stem}_analysis.txt"
    with open(output_file, 'w') as f:
        f.write("Drone Model Wind Force Analysis\n")
        f.write("="*70 + "\n\n")
        f.write(f"STL Model: {stl_source.name}\n")
        f.write(f"Reference Wind Speed: {wind_speed} m/s\n\n")
        
        f.write("Drag Coefficients:\n")
        f.write("-" * 70 + "\n")
        for case_key, case_info in CASES.items():
            coeff_data = coefficients.get(case_key, {})
            if isinstance(coeff_data, dict):
                simple_coeff = coeff_data.get('simple', 0.0)
                force_ref = coeff_data.get('force_at_test_speed', 0.0)
            else:
                simple_coeff = 0.0
                force_ref = 0.0
            f.write(f"{case_info['name']:30s}: D = {simple_coeff:10.6f}  (Force at 15 m/s: {force_ref:8.4f} N)\n")
    
        f.write("\n" + formula)
    
    print(f"\n[OK] Results saved to: {output_file}")
    
    return {
        'stl_filename': str(stl_source),
        'wind_speed': wind_speed,
        'results': results,
        'coefficients': coefficients,
        'formula': formula,
        'output_file': str(output_file)
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze drone model wind force characteristics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a model from stl/ directory
  ../../python/venv/bin/python3 analyze_drone_model.py AureliaX6Pro2_core_Internal.stl
  
  # Analyze with custom wind speed
  ../../python/venv/bin/python3 analyze_drone_model.py WhiteQuadrotor1_Internal.stl --wind-speed 15.0
        """
    )
    
    parser.add_argument('stl_file', type=str,
                       help='STL filename (can be in stl/ directory or full path)')
    parser.add_argument('--wind-speed', type=float,
                       default=15.0,
                       help='Reference wind speed in m/s (default: 15.0)')
    
    args = parser.parse_args()
    
    try:
        result = analyze_drone_model(
            args.stl_file,
            wind_speed=args.wind_speed
        )
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
