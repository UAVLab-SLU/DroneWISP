import pyvista as pv
import numpy as np
import trimesh
# Assuming you have a binary mask with the shape of (50, 50, 25)
# For demonstration, let's create a dummy 3D binary mask with a simple object.
# In your case, this would be your actual binary mask.
# binary_mask = np.zeros((50, 50, 25), dtype=np.uint8)
# binary_mask[20:30, 20:30, 10:20] = 1  # Simulating a simple object within the binary mask



def create_cube_at_position(position, cube_size=1):
    """
    Create a cube mesh at a given position.

    Parameters:
    - position: The (x, y, z) coordinates where the cube will be placed.
    - cube_size: The size of the cube edge.

    Returns:
    - cube_mesh: A trimesh.Primitive object representing the cube.
    """
    # Create a cube centered at the origin
    cube_mesh = trimesh.creation.box(extents=(cube_size, cube_size, cube_size))
    # Translate the cube to the specified position
    cube_mesh.apply_translation(np.array(position) * cube_size)
    return cube_mesh


def binary_mask_to_stl(binary_mask, output_filename="output_scene.stl"):
    """
    Convert a binary mask to an STL file by generating a cube for each '1'.

    Parameters:
    - binary_mask: A 3D numpy array representing the binary mask.
    - output_filename: The name of the output STL file.
    """
    cubes = []
    # Iterate through the binary mask
    for z in range(binary_mask.shape[2]):
        for y in range(binary_mask.shape[1]):
            for x in range(binary_mask.shape[0]):
                if binary_mask[x, y, z] == 1:
                    # Create a cube for each '1' and add it to the list
                    cube = create_cube_at_position((x, y, z))
                    cubes.append(cube)
    # Combine all cubes into a single mesh
    combined_mesh = trimesh.util.concatenate(cubes)
    # Export the combined mesh as an STL file
    combined_mesh.export(output_filename)
    return combined_mesh


# Example usage
binary_mask = np.load("csv/train/surface_only/binary_mask/binary_mask_2.npy")
# binary_mask = np.zeros((50, 50, 25), dtype=np.uint8)
# binary_mask[20:30, 20:30, 10:20] = 1  # Add a block to the binary mask for demonstration
mesh = binary_mask_to_stl(binary_mask, "output_scene.stl")
# visualize the STL file
plotter = pv.Plotter()
plotter.add_mesh(mesh, color="lightblue", show_edges=True)
plotter.show()

