import numpy as np
import pyvista as pv

surface = pv.STLReader("openFoamCase/constant/geometry/combined.stl").read()
n = 50
# Create a rectilinear grid 50x50x50
xx = np.linspace(-100, 100, n)
yy = np.linspace(-100, 100, n)
zz = np.linspace(0, 200, n)


dataset = pv.RectilinearGrid(xx, yy, zz)
# p = pv.Plotter()
#
# p.add_mesh(surface, color="w", label="Surface", opacity=0.5)
# # make the surface slightly transparent
# p.add_mesh(dataset, color="gold", show_edges=True, opacity=0.75, label="To Clip")
# p.add_legend()
# p.show()

dataset.compute_implicit_distance(surface, inplace=True)

dataset["my_array"] = np.zeros(dataset.n_points)
dataset["my_array"][dataset["implicit_distance"] >= 0] = 1
dataset["my_array"][dataset["implicit_distance"] < 0] = 0
# Plot the result, only showing the cells with a value of 1
dataset.plot(scalars="my_array", show_edges=True, cmap="viridis", show_scalar_bar=True,opacity=0.5)

