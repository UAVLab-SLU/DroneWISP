import math
import os
import time
import matplotlib.pyplot as plt
import numpy as np
# import open3d
from shapely.geometry import Point, Polygon
from stl import mesh
from mpl_toolkits import mplot3d
from matplotlib import pyplot
import plotly.express as px


class StlMeshUtils:

    def __init__(self, stl_file_name):
        """
        load stl file and preprocess it into a unique point array, and a binary array
        Unique point array: contains all unique points in the mesh, no duplicate points
        Binary array: contains 0s and 1s indicating if the cell is inside the mesh
        :param stl_file_name: stl file name
        """
        self.mesh = mesh.Mesh.from_file(stl_file_name)

        self.mesh_unique_points = np.around(
            np.unique(self.mesh.vectors.reshape(
                [int(self.mesh.vectors.size / 3), 3]),
                axis=0),
            2)
        print("unique points count: " + str(self.mesh_unique_points.size))

        # extracts unique 3D points from the mesh, no duplicate points, rounded to two decimal places
        # there is loss of precision here, but ok for large meshes
        # drawback: for really small meshes, loss is significant

        # self.polygon = Polygon(self.mesh_unique_points)  # used to determine if a point is inside the mesh
        self.binary_array = self.__unique_points_to_binary_array()
        print("true count: " + str(np.count_nonzero(self.binary_array)))


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

    def plot_stl_vertex(self):
        points = self.mesh_unique_points
        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]
        figure = pyplot.figure()
        axes = figure.add_subplot(projection='3d')

        print(self.mesh.points)
        # use small dots to plot the vertices
        axes.scatter(x, y, z, marker='.', s=1)
        # 1:1:1 aspect ratio
        axes.set_aspect('equal')
        # self.plot_interactive(x, y, z)
        axes.set_xlabel('X')
        axes.set_ylabel('Y')
        axes.set_zlabel('Z')

        # plot in 3 directions
        axes.view_init(45, 0)
        pyplot.show()

        axes.view_init(0, 0)
        pyplot.show()

        axes.view_init(0, 90)
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
        pass

    def plot_interactive(self, x, y, z):
        """
        plot interactive 3d plot
        :return:
        """
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        fig = px.scatter_3d(title="3D Plot")

        # points only, no lines, 1:1:1 aspect ratio
        fig.add_scatter3d(x=x, y=y, z=z, name="path", mode="markers", marker=dict(size=2, color="red"))
        fig.update_layout(scene=dict(aspectmode="manual", aspectratio=dict(x=1, y=1, z=1)))

        file_name = 'plot.html'
        fig.write_html(file_name)
        plt.close()



    def __unique_points_to_binary_array(self, x_len=500, y_len=500, z_len=25):
        """
        :param resolution: resolution of the binary array, number of cells in each dimension
        Convert unique points to numpy array containing 0s and 1s indicating if the cell is inside the mesh
        :return:
        """
        count = 0
        bin_array = np.zeros((x_len*2+1, y_len*2+1, z_len*2+1), dtype=bool)
        for point in self.mesh_unique_points:
            count += 1
            x = point[0]
            y = point[1]
            z = point[2]
            if x < x_len and y < y_len and z < z_len:
                bin_array[int(x), int(y), int(z)] = True

        return bin_array

    def stl_to_point_cloud(self):
        pass

    def slice_binary_array(self, x_min, x_max, y_min, y_max, z_min, z_max):
        """
        Slice the binary array
        :param x_min: x min
        :param x_max: x max
        :param y_min: y min
        :param y_max: y max
        :param z_min: z min
        :param z_max: z max
        :return:
        """
        return self.binary_array[x_min:x_max, y_min:y_max, z_min:z_max]

    def save_binary_array(self, file_name):
        np.save(file_name, self.binary_array)

    def load_binary_array(self, file_name):
        # not going to use this, just here for reference
        self.binary_array = np.load(file_name)

    def printProgressBar(self, iteration, total):
        percent = ("{0:." + str(1) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(100 * iteration // total)
        bar = "█" * filledLength + '-' * (100 - filledLength)
        print(f'\r{""} |{bar}| {percent}% {""}', end="\r")


if __name__ == "__main__":
    # for file in os.listdir("../pinn/training_mesh/buildings"):
    #     if file.endswith(".stl"):
    #         print(file)
    #         stl_mesh_utils = StlMeshUtils("../pinn/training_mesh/buildings/" + file)
    #
    #         stl_mesh_utils.scale_mesh(0.01)
    #         stl_mesh_utils.plot_mesh()
    #         stl_mesh_utils.plot_array()

    stl_mesh_utils = StlMeshUtils("../stl/Chicago_+500x-500.stl")  # chicago dimensions: -2014 2073 -1710 1706 0 441

    stl_mesh_utils.save_binary_array("chicago_binary_array.npy")

    # stl_mesh_utils.save_mesh("small.stl")

    # stl_mesh_utils.scale_mesh(0.1)
    # print(stl_mesh_utils.get_mesh_x_bound())
    # print(stl_mesh_utils.get_mesh_y_bound())
    # print(stl_mesh_utils.get_mesh_z_bound())
