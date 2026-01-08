#!/usr/bin/env python3
"""
Convert OBJ files to STL format.
"""

import os
import trimesh
from pathlib import Path

def convert_obj_to_stl(obj_dir, stl_dir):
    """
    Convert all OBJ files in obj_dir to STL format and save to stl_dir.
    
    Args:
        obj_dir: Directory containing OBJ files
        stl_dir: Directory to save STL files
    """
    # Create stl directory if it doesn't exist
    os.makedirs(stl_dir, exist_ok=True)
    
    # Find all OBJ files
    obj_files = list(Path(obj_dir).glob("*.OBJ")) + list(Path(obj_dir).glob("*.obj"))
    
    if not obj_files:
        print(f"No OBJ files found in {obj_dir}")
        return
    
    print(f"Found {len(obj_files)} OBJ file(s) to convert")
    
    for obj_file in obj_files:
        try:
            print(f"Converting {obj_file.name}...")
            
            # Load OBJ file
            mesh = trimesh.load(str(obj_file))
            
            # Handle case where trimesh returns a Scene (multiple meshes)
            if isinstance(mesh, trimesh.Scene):
                # Combine all meshes in the scene
                mesh = trimesh.util.concatenate([m for m in mesh.geometry.values() if isinstance(m, trimesh.Trimesh)])
            
            # Generate STL filename (replace .obj/.OBJ with .stl)
            stl_filename = obj_file.stem + ".stl"
            stl_path = os.path.join(stl_dir, stl_filename)
            
            # Export as STL
            mesh.export(stl_path, file_type='stl')
            
            print(f"  ✓ Saved to {stl_path}")
            
        except Exception as e:
            print(f"  ✗ Error converting {obj_file.name}: {e}")

if __name__ == "__main__":
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    obj_dir = os.path.join(script_dir, "obj")
    stl_dir = os.path.join(script_dir, "stl")
    
    convert_obj_to_stl(obj_dir, stl_dir)
    print("\nConversion complete!")

