import math

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import plotly.express as px
from matplotlib import pyplot
from mpl_toolkits import mplot3d


class StlMeshUtils:

    def __init__(self):
        self.binary_array = None
        self.mesh = None
        self.mesh_point_cloud = None  # point cloud of the mesh, type: open3d.geometry.PointCloud
        self.mesh_point_cloud_array = None  # point cloud of the mesh, type: numpy array
        self.mesh_unique_points = None  # unique points in the mesh, type: numpy array, int32
        self.velocity = None  # velocity data, type: numpy array

        self.mesh_binary_mask_blocks = None  # list of binary mask blocks
        self.velocity_blocks = None  # list of velocity blocks

    def load_convert_mesh(self, stl_file_name):
        """
        Load the stl file
        :param stl_file_name:
        :return:
        """
        if stl_file_name is None:
            print("stl file name is None")
            return
        try:
            self.mesh = o3d.io.read_triangle_mesh(stl_file_name)
            self.mesh_point_cloud = self.mesh.sample_points_poisson_disk(62500)
            self.mesh_point_cloud_array = np.asarray(self.mesh_point_cloud.points)
            # int list of unique points
            self.mesh_unique_points = np.int32(
                np.unique(self.mesh_point_cloud_array.reshape(
                    [int(self.mesh_point_cloud_array.size / 3), 3]), axis=0)
            )
        except:
            print("Error loading mesh")

    def load_velocity(self, velocity_file_name):
        """
        Load the velocity file,
        csv file format: x, y, z, u, v, w
        first row is the header, so it is skipped
        :param velocity_file_name:
        :return:
        """
        if velocity_file_name is None:
            print("velocity file name is None")
            return
        try:
            # csv file
            if velocity_file_name.endswith(".csv"):
                self.velocity = np.genfromtxt(velocity_file_name, delimiter=',')[1:]
        except:
            print("Error loading velocity file")

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
        # top-down view
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
        pyplot.close()

    def plot_binary_array(self, array=None):
        """
        plot the binary array, only 1s are plotted
        :return:
        """
        if array is None:
            array = self.binary_array

        figure = pyplot.figure()
        axes = figure.add_subplot(projection='3d')
        # axes.voxels(self.binary_array, edgecolor='k')
        x = []
        y = []
        z = []
        for i in range(array.shape[0]):
            for j in range(array.shape[1]):
                for k in range(array.shape[2]):
                    if array[i][j][k]:
                        x.append(i)
                        y.append(j)
                        z.append(k)

        axes.scatter(x, y, z, marker='.', s=1)
        axes.view_init(45, 0)
        axes.set_xlabel('X')
        axes.set_ylabel('Y')
        axes.set_zlabel('Z')

        pyplot.show()

    def plot_unique_points(self):
        points = self.mesh_unique_points
        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]
        figure = pyplot.figure()
        axes = figure.add_subplot(projection='3d')
        # use small dots to plot the vertices
        axes.scatter(x, y, z, marker='.', s=1)
        # 1:1:1 aspect ratio
        axes.set_aspect('equal')
        # self.plot_interactive(x, y, z)
        axes.set_xlabel('X')
        axes.set_ylabel('Y')
        axes.set_zlabel('Z')

        axes.view_init(45, 0)
        pyplot.show()

    def save_mesh(self, save_file_name):
        self.mesh.save(save_file_name)

    def __is_cell_inside_mesh(self, x, y, z):
        """
        Check if the cell is inside the mesh
        :param x: x index
        :param y: y index
        :param z: z index
        :return: True if the cell is inside the mesh, False otherwise
        """
        pass

    @staticmethod
    def plot_interactive(x, y, z):
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

    def __mesh_to_binary_array(self, x_len=500, y_len=500, z_len=25):
        """
        use polygon to determine if a cell is inside the mesh
        :param x_len:
        :param y_len:
        :param z_len:
        :return:
        """

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

    def save_binary_array(self, file_name, array=None):
        np.save(file_name, array)

    def load_binary_array(self, file_name):
        # not going to use this, just here for reference
        self.binary_array = np.load(file_name)

    def partition_mesh_block(self, block_size_x=50, block_size_y=50, x_min=-500, x_max=500, y_min=-500, y_max=500):
        """
        Partition the mesh into blocks, order: x from min to max, then y from min to max
        :return: list of blocks
        """

        # check even division
        if (x_max - x_min) % block_size_x != 0 or (y_max - y_min) % block_size_y != 0:
            print("partition error: block size does not divide evenly")
            print("trying to divide: ", x_max - x_min, y_max - y_min, "by", block_size_x, block_size_y)

        blocks = []
        x_start, y_start = x_min, y_min
        while x_start < x_max and y_start < y_max:
            x_end = min(x_start + block_size_x, x_max)
            y_end = min(y_start + block_size_y, y_max)

            block_points = self.get_mesh_points(x_start, x_end, y_start, y_end)
            adjusted_block_points = self.adjust_points(block_points, x_start, y_start)
            blocks.append(adjusted_block_points)

            x_start += block_size_x
            if x_start >= x_max:
                x_start = x_min
                y_start += block_size_y

        # check block count
        expected_count = ((x_max - x_min) // block_size_x) * ((y_max - y_min) // block_size_y)
        if len(blocks) != expected_count:
            print("Warning: block count does not match expected count")
            print("expected: ", expected_count, "actual: ", len(blocks))

        return blocks

    def get_mesh_points(self, x_min, x_max, y_min, y_max):
        block_points = []
        for point in self.mesh_unique_points:
            x, y, z = point
            if x_min <= x < x_max and y_min <= y < y_max:
                block_points.append(point)
        return block_points

    @staticmethod
    def adjust_points(block_points, x_start, y_start):
        adjusted_block_points = []
        for x, y, z in block_points:
            adjusted_point = [x - x_start, y - y_start, z]
            adjusted_block_points.append(adjusted_point)
        return adjusted_block_points

    @staticmethod
    def to_binary_mask(block):
        binary_mask = np.zeros((50, 50, 25), dtype=int)
        for point in block:
            x, y, z = point
            if 0 <= x < 50 and 0 <= y < 50 and 0 <= z < 25:
                binary_mask[x][y][z] = 1
        return binary_mask

    def partition_velocity_block(self, block_size_x=50, block_size_y=50, x_min=-500, x_max=500, y_min=-500, y_max=500,
                                 min_z=0, max_z=25):
        """
        Partition the velocity data into blocks
        :return: list of blocks
        """
        # calculate the number of blocks
        total_blocks = (x_max - x_min) // block_size_x * (y_max - y_min) // block_size_y


        # filter the velocity data
        mask = (self.velocity[:, 0] >= x_min) & (self.velocity[:, 0] < x_max) & \
               (self.velocity[:, 1] >= y_min) & (self.velocity[:, 1] < y_max) & \
               (self.velocity[:, 2] >= min_z) & (self.velocity[:, 2] < max_z)

        self.velocity = self.velocity[mask]

        # check even division
        if (x_max - x_min) % block_size_x != 0 or (y_max - y_min) % block_size_y != 0:
            print("partition error: block size does not divide evenly")
            print("trying to divide: ", x_max - x_min, y_max - y_min, "by", block_size_x, block_size_y)

        # split the velocity data into exactly the same number of blocks as the mesh
        blocks = np.array_split(self.velocity, total_blocks)

        return blocks


if __name__ == "__main__":
    stl_file = "../stl/Chicago_+500x-500.stl"
    vl_file = "../openFoamCase/10ms_2.csv"

    stl_mesh_utils = StlMeshUtils()  # chicago dimensions: -2014 2073 -1710 1706 0 441
    stl_mesh_utils.load_convert_mesh(stl_file)
    stl_mesh_utils.load_velocity(vl_file)

    blocks = stl_mesh_utils.partition_mesh_block(50, 50, -100, 100, -100, 100)
    print("block count: ", len(blocks))

    #print(blocks[0])
    #
    for i, block in enumerate(blocks):
        binary_mask = stl_mesh_utils.to_binary_mask(block)
        stl_mesh_utils.save_binary_array("binary_mask_" + str(i) + ".npy", binary_mask)


    vel_blocks = stl_mesh_utils.partition_velocity_block(50, 50, -100, 100, -100, 100)
    print("vel block count: ", len(vel_blocks))

    for i, block in enumerate(vel_blocks):
        np.save("velocity_" + str(i) + ".npy", block)
    # stl_mesh_utils.plot_mesh()
    # stl_mesh_utils.plot_stl_vertex()




    # stl_mesh_utils.save_mesh("small.stl")

    # stl_mesh_utils.scale_mesh(0.1)
    # print(stl_mesh_utils.get_mesh_x_bound())
    # print(stl_mesh_utils.get_mesh_y_bound())
    # print(stl_mesh_utils.get_mesh_z_bound())
