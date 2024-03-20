import numpy as np
import pyvista as pv


def mask_mesh_by_surface(grid_image_data, mesh_surface):
    grid = grid_image_data.copy()

    # Assign unique identifiers to each point and cell in the mesh
    grid["point_ids"] = np.arange(grid.n_points)
    grid["cell_ids"] = np.arange(grid.n_cells)

    # Clip the mesh by the surface from both sides (inside and outside of the surface)
    inside_surface = grid.clip_surface(mesh_surface, invert=False, compute_distance=True)
    outside_surface = grid.clip_surface(mesh_surface, invert=True, compute_distance=True)

    # Create a mask for the cells in the mesh
    grid["cell_mask"] = np.zeros(grid.n_cells, dtype=int)
    grid["cell_mask"][inside_surface["cell_ids"]] = 1  # Cells inside the surface
    grid["cell_mask"][outside_surface["cell_ids"]] = 2  # Cells outside the surface

    # Use the implicit distance to create a mask for the points in the mesh
    inside_point_ids = np.argwhere(grid["implicit_distance"] >= 0)
    outside_point_ids = np.argwhere(grid["implicit_distance"] < 0)
    grid["point_mask"] = np.zeros(grid.n_points, dtype=int)
    grid["point_mask"][inside_point_ids] = 1  # Points inside the surface
    grid["point_mask"][outside_point_ids] = 2  # Points outside the surface

    return grid


stl = pv.STLReader("openFoamCase/constant/geometry/combined.stl").read()
grid = pv.ImageData()
grid.origin = (0, 0, 0)
# Cell sizes
grid.spacing = (1, 1, 1)
# Number of cells in each direction
grid.dimensions = (100, 100, 50)

masked = mask_mesh_by_surface(grid, stl)

ids = np.argwhere(masked["point_mask"] == 1).ravel()
pts = grid.points[ids]
compute = lambda a, b: np.sqrt(np.sum((b - a) ** 2, axis=1))
dist = compute(pts, np.repeat([masked.bounds[1::2]], pts.shape[0], axis=0))
# Euclidean distance from each point in the mesh that is inside the surface
masked["cool_math"] = np.zeros(grid.n_points)  # Need to preallocate
masked["cool_math"][ids] = dist

distance_mask = masked["cool_math"]
print(f"shape of distance mask: {distance_mask.shape}")

# p = pv.Plotter()
# p.add_mesh(a, scalars="cool_math")
# p.show()

# convert to binary mask
#
print(f"cell mask shape: {masked['cell_mask'].shape}")

masked["binary_mask"] = np.zeros(masked.n_points, dtype=int)
masked["binary_mask"][distance_mask > 1] = 0
masked["binary_mask"][distance_mask <= 1] = 1

# remove all 0s


binary_mask = masked["binary_mask"]

print(f"Binary mask shape: {binary_mask.shape}, 1s: {np.sum(binary_mask == 1)}, 0s: {np.sum(binary_mask == 0)}")

a = masked.threshold(1.5, scalars="cell_mask", invert=False)
a["binary_mask"] = np.zeros(a.n_points, dtype=int)
a["binary_mask"][a["cool_math"] > 0] = 1
a["binary_mask"][a["cool_math"] <= 0] = 0
print(
    f"Threshold mask shape: {a['binary_mask'].shape}, 1s: {np.sum(a['binary_mask'] == 1)}, 0s: {np.sum(a['binary_mask'] == 0)}")

inside_clip = masked.clip_box([0, 50, 0, 50, 0, 50])

p = pv.Plotter()
# p.add_mesh(a, scalars="binary_mask", opacity=0.5)
# plot masked, only 1s
p.add_mesh(inside_clip, scalars="binary_mask", opacity=0.5, style="points")
# clip view
p.view_isometric()
p.show()

# save as np array
# np.save("binary_mask.npy", a["binary_mask"])
