# only good for terrain, not for buildings

import numpy as np
import pyvista as pv

mesh = pv.STLReader("openFoamCase/constant/geometry/combined.stl").read()
# create mesh, 200x200x200
blocks = pv.RectilinearGrid()
blocks.x = np.linspace(-100, 100, 50)
blocks.y = np.linspace(-100, 100, 50)
blocks.z = np.linspace(0, 200, 50)

# convert topo to mesh
mesh = mesh.sample(blocks)

# extract topography
extracted = blocks.clip_surface(mesh, invert=False, compute_distance=True)

# plot
p = pv.Plotter()
p.add_mesh(mesh, color="orange")
p.add_mesh(extracted, scalars="implicit_distance")
p.show()

# extract buildings
