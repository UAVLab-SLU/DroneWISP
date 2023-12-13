from stl import mesh
from mpl_toolkits import mplot3d
from matplotlib import pyplot

class StlMeshUtils:

    def __init__(self, stl_file_name):
        self.mesh = mesh.Mesh.from_file(stl_file_name)

    def get_mesh_min(self):
        return self.mesh.min_

    def get_mesh_max(self):
        return self.mesh.max_

    def get_mesh_x_bound(self):
        return [self.get_mesh_min()[0], self.get_mesh_max()[0]]

    def get_mesh_y_bound(self):
        return [self.get_mesh_min()[1], self.get_mesh_max()[1]]

    def get_mesh_z_bound(self):
        return [self.get_mesh_min()[2], self.get_mesh_max()[2]]

    def scale_mesh(self, scale):
        self.mesh.vectors *= scale

    def rotate_mesh(self, center, degrees):
        self.mesh.rotate(center, degrees)

    def plot_mesh(self):
        figure = pyplot.figure()
        axes = figure.add_subplot(projection='3d')
        axes.add_collection3d(mplot3d.art3d.Poly3DCollection(self.mesh.vectors))
        scale = self.mesh.points.flatten()
        axes.auto_scale_xyz(scale, scale, scale)
        pyplot.show()

    def save_mesh(self, save_file_name):
        self.mesh.save(save_file_name)




if __name__ == "__main__":
    stl_mesh_utils = StlMeshUtils("../openFoamCase/constant/geometry/combined.stl")
    print(stl_mesh_utils.get_mesh_x_bound())
    print(stl_mesh_utils.get_mesh_y_bound())
    print(stl_mesh_utils.get_mesh_z_bound())

    stl_mesh_utils.rotate_mesh([0, 0, 0], 45)

    stl_mesh_utils.plot_mesh()

    stl_mesh_utils.save_mesh("small.stl")

    # stl_mesh_utils.scale_mesh(0.1)
    # print(stl_mesh_utils.get_mesh_x_bound())
    # print(stl_mesh_utils.get_mesh_y_bound())
    # print(stl_mesh_utils.get_mesh_z_bound())




