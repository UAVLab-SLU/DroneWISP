#!/usr/bin/env python3
"""
Scale STL files to meters.

The STL files appear to be in centimeters, but OpenFOAM expects meters.
This script scales them by 0.01 (cm to m).
"""

import sys
import trimesh
from pathlib import Path

def scale_stl_to_meters(stl_path, output_path=None, scale_factor=0.01):
    """
    Scale STL file to meters.
    
    Args:
        stl_path: Path to input STL file
        output_path: Path to output STL file (default: overwrite input)
        scale_factor: Scale factor (0.01 for cm to m)
    """
    stl_path = Path(stl_path)
    
    if not stl_path.exists():
        print(f"[ERROR] STL file not found: {stl_path}")
        return False
    
    # Load mesh
    mesh = trimesh.load(str(stl_path))
    
    # Check current size
    bounds = mesh.bounds
    size = bounds[1] - bounds[0]
    area = mesh.area
    
    print(f"Original STL: {stl_path.name}")
    print(f"  Dimensions: {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f}")
    print(f"  Area: {area:.2f}")
    
    # Scale mesh
    mesh.apply_scale(scale_factor)
    
    # Check new size
    bounds_new = mesh.bounds
    size_new = bounds_new[1] - bounds_new[0]
    area_new = mesh.area
    
    print(f"Scaled STL:")
    print(f"  Dimensions: {size_new[0]:.2f} x {size_new[1]:.2f} x {size_new[2]:.2f} m")
    print(f"  Area: {area_new:.2f} m²")
    
    # Save
    if output_path is None:
        output_path = stl_path
    
    mesh.export(str(output_path))
    print(f"[OK] Saved to: {output_path}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scale_stl_to_meters.py <stl_file> [output_file]")
        print("Example: python3 scale_stl_to_meters.py stl/AureliaX6Pro2_core_Internal.stl")
        sys.exit(1)
    
    stl_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    scale_stl_to_meters(stl_file, output_file)

