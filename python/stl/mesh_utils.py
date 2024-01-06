import math
import os

import numpy as np
from shapely.geometry import Point, Polygon
from stl import mesh
from mpl_toolkits import mplot3d
from matplotlib import pyplot


class StlMeshUtils:

    def __init__(self, stl_file_name):
        self.mesh = mesh.Mesh.from_file(stl_file_name)
        self.binary_array = self.__stl_to_array()

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

    def rotate_mesh(self, degrees):
        rad = degrees * math.pi / 180
        self.mesh.rotate(axis=[0, 0, 1], theta=rad, point=[0, 0, 0])

    def plot_mesh(self):
        figure = pyplot.figure()
        axes = figure.add_subplot(projection='3d')
        axes.add_collection3d(mplot3d.art3d.Poly3DCollection(self.mesh.vectors))
        scale = self.mesh.points.flatten()
        axes.auto_scale_xyz(scale, scale, scale)
        # top down view
        axes.view_init(45, 0)

        axes.set_xlabel('X')
        axes.set_ylabel('Y')
        axes.set_zlabel('Z')

        pyplot.show()

    def plot_array(self):
        figure = pyplot.figure()
        axes = figure.add_subplot(projection='3d')
        axes.voxels(self.binary_array, edgecolor='k')

        axes.view_init(45, 0)
        axes.set_xlabel('X')
        axes.set_ylabel('Y')
        axes.set_zlabel('Z')

        pyplot.show()

    def save_mesh(self, save_file_name):
        self.mesh.save(save_file_name)

    def add_mesh(self, stl_file_name, origin):
        mesh_to_add = mesh.Mesh.from_file(stl_file_name)
        self.mesh = mesh.Mesh(np.concatenate([self.mesh.data, mesh_to_add.data]))

    def __is_cell_inside_mesh(self, x, y, z):
        """
        Check if the cell is inside the mesh
        :param x: x index
        :param y: y index
        :param z: z index
        :return: True if the cell is inside the mesh, False otherwise
        """



    def __stl_to_array(self):
        """
        Convert stl mesh to numpy array containing 0s and 1s indicating if the cell is inside the mesh
        :return:
        """

        resolution = 60
        min_coords = np.min(self.mesh.v0, axis=0)
        max_coords = np.max(self.mesh.v0, axis=0)
        # Normalize coordinates to fit within the resolution
        normalized_coords = (self.mesh.v0 - min_coords) / (max_coords - min_coords) * resolution

        # Create an empty 3D array
        voxel_grid = np.zeros((resolution+1, resolution+1, resolution+1), dtype=int)

        ins = 0
        # Fill the voxel grid based on the mesh
        for x in range(resolution+1):
            for y in range(resolution+1):
                for z in range(resolution+1):
                    point = Point(x, y, z)
                    polygon = Polygon(normalized_coords)
                    if polygon.contains(point):
                        ins += 1
                        voxel_grid[x, y, z] = 1
        print("ins:", ins, "total:", (resolution+1)**3)

        return voxel_grid



if __name__ == "__main__":

    # for file in os.listdir("../pinn/training_mesh/buildings"):
    #     if file.endswith(".stl"):
    #         print(file)
    #         stl_mesh_utils = StlMeshUtils("../pinn/training_mesh/buildings/" + file)
    #
    #         stl_mesh_utils.scale_mesh(0.01)
    #         stl_mesh_utils.plot_mesh()
    #         stl_mesh_utils.plot_array()

    stl_mesh_utils = StlMeshUtils("../stl/small.stl")
    print(stl_mesh_utils.get_mesh_x_bound())
    print(stl_mesh_utils.get_mesh_y_bound())
    print(stl_mesh_utils.get_mesh_z_bound())

    #stl_mesh_utils.scale_mesh(0.01)

    stl_mesh_utils.plot_mesh()
    stl_mesh_utils.plot_array()

    # stl_mesh_utils.save_mesh("small.stl")

    # stl_mesh_utils.scale_mesh(0.1)
    # print(stl_mesh_utils.get_mesh_x_bound())
    # print(stl_mesh_utils.get_mesh_y_bound())
    # print(stl_mesh_utils.get_mesh_z_bound())
