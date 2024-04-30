import pandas as pd

# Assuming StlMeshUtils has the height_mask_to_tall_cubes method implemented
from mesh_utils import StlMeshUtils


def generate_mesh_from_csv(csv_file):
    # Load the CSV file using pandas
    data = pd.read_csv(csv_file)

    # Extract the list of tuples (x, y, z) which represent the positions and heights
    height_mask = list(zip(data['x'], data['y'], data['z']))

    # Call the method to generate the mesh
    mesh = StlMeshUtils.height_mask_to_tall_cubes(height_mask, cube_size=1)  # Adjust cube_size if needed

    # Optional: Save the mesh to an STL file (not specified to be part of the function, but useful)
    output_filename = "output_mesh.stl"
    mesh.export(output_filename)
    print(f"Mesh exported to {output_filename}")


# Example usage
csv_file = "heightMask.csv"
generate_mesh_from_csv(csv_file)
