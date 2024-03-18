import numpy as np
import pyvista as pv


def mask_mesh_by_surface(mesh, surface):
    grid = mesh.copy()
    # Split the mesh by the fault
    grid["pids"] = np.arange(grid.n_points)
    grid["cids"] = np.arange(grid.n_cells)
    a = grid.clip_surface(surface, invert=False, compute_distance=True)
    b = grid.clip_surface(surface, invert=True, compute_distance=True)
    # Inject the mask
    grid["cell_mask"] = np.zeros(grid.n_cells, dtype=int)
    grid["cell_mask"][a["cids"]] = 1
    grid["cell_mask"][b["cids"]] = 2
    # Use implicit distance to get point mask
    lpids = np.argwhere(grid["implicit_distance"] >= 0)
    gpids = np.argwhere(grid["implicit_distance"] < 0)
    grid["point_mask"] = np.zeros(grid.n_points, dtype=int)
    grid["point_mask"][lpids] = 1
    grid["point_mask"][gpids] = 2
    return grid


fault = pv.STLReader("openFoamCase/constant/geometry/combined.stl").read()
grid = pv.ImageData()
grid.origin = (0, 0, 0)
# Cell sizes
grid.spacing = (1, 1, 1)
# Number of cells in each direction
grid.dimensions = (100, 100, 100)

masked = mask_mesh_by_surface(grid, fault)

ids = np.argwhere(masked["point_mask"] == 1).ravel()
pts = grid.points[ids]
len(pts)
compute = lambda a, b: np.sqrt(np.sum((b - a) ** 2, axis=1))
dist = compute(pts, np.repeat([masked.bounds[1::2]], pts.shape[0], axis=0))
masked["cool_math"] = np.zeros(grid.n_points)  # Need to preallocate
masked["cool_math"][ids] = dist

a = masked.threshold(1.5, scalars="cell_mask", invert=False)

# p = pv.Plotter()
# p.add_mesh(a, scalars="cool_math")
# p.show()

# convert to binary mask
a["binary_mask"] = np.zeros(a.n_points, dtype=int)
a["binary_mask"][a["cool_math"] > 0] = 1
a["binary_mask"][a["cool_math"] <= 0] = 0

binary_mask = a["binary_mask"]
print(f"Binary mask shape: {binary_mask.shape}, 1s: {np.sum(binary_mask)}, 0s: {np.sum(binary_mask == 0)}")

# save as np array
#np.save("binary_mask.npy", a["binary_mask"])
