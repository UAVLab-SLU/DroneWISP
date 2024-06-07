import math

import matplotlib.pyplot as plt
import pyvista as pv
import numpy as np
#import open3d as o3d
import plotly.express as px
from matplotlib import pyplot
from mpl_toolkits import mplot3d
import trimesh

class StlMeshUtils:

    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.binary_array = None
        self.mesh = None
        self.pv_mesh = None
        self.mesh_point_cloud = None  # point cloud of the mesh, type: open3d.geometry.PointCloud
        self.mesh_point_cloud_array = None  # point cloud of the mesh, type: numpy array
        self.mesh_unique_points = None  # unique points in the mesh, type: numpy array, int32
        self.velocity = None  # velocity data, type: numpy array

        self.mesh_binary_mask_blocks = None  # list of binary mask blocks
        self.velocity_blocks = None  # list of velocity blocks

    # def load_convert_mesh(self, stl_file_name):
    #     """
    #     Load the stl file
    #     :param stl_file_name:
    #     :return:
    #     """
    #     if stl_file_name is None:
    #         print("stl file name is None")
    #         return
    #     try:
    #         self.mesh = o3d.io.read_triangle_mesh(stl_file_name)
    #         self.mesh_point_cloud = self.mesh.sample_points_poisson_disk(62500)
    #         self.mesh_point_cloud_array = np.asarray(self.mesh_point_cloud.points)
    #         # int list of unique points
    #         self.mesh_unique_points = np.int32(
    #             np.unique(self.mesh_point_cloud_array.reshape(
    #                 [int(self.mesh_point_cloud_array.size / 3), 3]), axis=0)
    #         )
    #     except:
    #         print("Error loading mesh")

    def pv_load_convert_mesh(self, stl_file_name):
        """
        Load the stl file using pyvista
        :param stl_file_name:
        :return:
        """
        if stl_file_name is None:
            print("stl file name is None")
            return
        try:
            self.pv_mesh = pv.STLReader(stl_file_name).read()
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
        axes.view_init(45, 45)
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

            # check block location
            print("current block is formed by: (", x_start, y_start, "), (", x_end, y_end, ")")

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

    def pv_partition_binary_mesh_block(self, block_size_x=50, block_size_y=50, block_size_z=25, x_min=-100, x_max=100,
                                       y_min=-100, y_max=100, z_max=100):
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

            # check block location
            print("current block is formed by: (", x_start, y_start, "), (", x_end, y_end, ")")

            binary_mask = self.pv_create_binary_mask(block_size_x, block_size_y, block_size_z, x_start, y_start)
            if len(binary_mask) != block_size_x * block_size_y * block_size_z:
                print("Warning: binary mask size does not match expected size")
                print("expected: ", block_size_x * block_size_y * block_size_z, "actual: ", len(binary_mask))

            # reshape to 3d
            binary_mask = binary_mask.reshape((block_size_x, block_size_y, block_size_z))

            # flip x and z axis, somehow pyvista has different axis order
            binary_mask = np.swapaxes(binary_mask, 0, 2)

            binary_mask = binary_mask.flatten().reshape((block_size_x, block_size_y, block_size_z))

            if self.debug_mode:
                self.plot_binary_array(binary_mask)

            blocks.append(binary_mask)

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

    def pv_create_binary_mask(self, block_size_x, block_size_y, block_size_z, x_start, y_start):
        grid = pv.ImageData()
        grid.origin = (x_start, y_start, 0)
        # Cell sizes
        grid.spacing = (1, 1, 1)
        # Number of cells in each direction
        grid.dimensions = (block_size_x, block_size_y, block_size_z)
        masked = self.mask_mesh_by_surface(grid, self.pv_mesh)
        ids = np.argwhere(masked["point_mask"] == 1).ravel()
        pts = grid.points[ids]
        compute = lambda a, b: np.sqrt(np.sum((b - a) ** 2, axis=1))
        dist = compute(pts, np.repeat([masked.bounds[1::2]], pts.shape[0], axis=0))
        # Euclidean distance from each point in the mesh that is inside the surface
        masked["cool_math"] = np.zeros(grid.n_points)  # Need to preallocate
        masked["cool_math"][ids] = dist
        distance_mask = masked["cool_math"]
        masked["binary_mask"] = np.zeros(masked.n_points, dtype=bool)
        masked["binary_mask"][distance_mask > 1] = 0
        masked["binary_mask"][distance_mask <= 1] = 1
        binary_mask = masked["binary_mask"]

        return binary_mask

    def get_mesh_points(self, x_min, x_max, y_min, y_max):
        """
        Get the mesh points within the given range
        :param x_min:
        :param x_max:
        :param y_min:
        :param y_max:
        :return:
        """
        block_points = []
        for point in self.mesh_unique_points:
            x, y, z = point
            if x_min <= x < x_max and y_min <= y < y_max:
                block_points.append(point)
        return block_points

    @staticmethod
    def adjust_points(block_points, x_start, y_start):
        """
        Adjust the points to start from 0, 0
        :param block_points:
        :param x_start:
        :param y_start:
        :return:
        """
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
        just split the data into exactly the same number of blocks as the mesh
        assumes the velocity data is already preprocessed and contains exactly the same number of points as the mesh
        :return: list of blocks
        """

        # size check
        expected_count = (x_max - x_min) * (y_max - y_min) * (max_z - min_z)
        if len(self.velocity) != expected_count:
            print("Warning: velocity data count does not match expected count")
            print("expected: ", expected_count, "actual: ", len(self.velocity))

        # check even division
        if (x_max - x_min) % block_size_x != 0 or (y_max - y_min) % block_size_y != 0:
            print("partition error: block size does not divide evenly")
            print("trying to divide: ", x_max - x_min, y_max - y_min, "by", block_size_x, block_size_y)
            # just throw an error for now
            raise ValueError("block size does not divide evenly")

        # calculate the number of blocks
        total_blocks = (x_max - x_min) // block_size_x * (y_max - y_min) // block_size_y

        # filter by range
        mask = (self.velocity[:, 0] >= x_min) & (self.velocity[:, 0] < x_max) & \
               (self.velocity[:, 1] >= y_min) & (self.velocity[:, 1] < y_max) & \
               (self.velocity[:, 2] >= min_z) & (self.velocity[:, 2] < max_z)
        self.velocity = self.velocity[mask]

        blocks = []

        # split the data into blocks
        for cur_x in range(x_min, x_max, block_size_x):
            for cur_y in range(y_min, y_max, block_size_y):
                cur_block = self.velocity[
                    (self.velocity[:, 0] >= cur_x) & (self.velocity[:, 0] < cur_x + block_size_x) & \
                    (self.velocity[:, 1] >= cur_y) & (self.velocity[:, 1] < cur_y + block_size_y) & \
                    (self.velocity[:, 2] >= min_z) & (self.velocity[:, 2] < max_z)
                    ]
                print("cur block formed by: (", cur_x, cur_y, "), (", cur_x + block_size_x, cur_y + block_size_y, ")")
                blocks.append(cur_block)

        # remove the x, y, z columns
        for i in range(len(blocks)):
            blocks[i] = blocks[i][:, 3:]

        # check shape
        for block in blocks:
            if block.shape != (block_size_x * block_size_y * (max_z - min_z), 3):
                print("Warning: velocity block shape does not match expected shape")
                print("expected: ", block_size_x * block_size_y * (max_z - min_z), "actual: ", block.shape)

        return blocks

    @staticmethod
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

    @staticmethod
    def clip_and_save_mesh(vertices, stl_file_path, output_stl_file_path):
        """
        Clips a section of the mesh defined by 8 vertices from an STL file and saves it to a new STL file.

        Parameters:
        - vertices: A list of 8 tuples, each representing a vertex (x, y, z) of the bounding box.
        - stl_file_path: Path to the input STL file.
        - output_stl_file_path: Path where the clipped mesh will be saved as an STL file.
        """
        # Load the STL file
        mesh = pv.read(stl_file_path)
        points = np.array(vertices, dtype=np.float64)
        cells = np.array([8, 0, 1, 2, 3, 4, 5, 6, 7], dtype=np.int64)
        cell_types = np.array([pv.CellType.HEXAHEDRON], dtype=np.uint8)
        hexahedron = pv.UnstructuredGrid(cells, cell_types, points)
        bbox = hexahedron.extract_surface()
        clipped_mesh = mesh.clip_surface(bbox)
        clipped_mesh.save(output_stl_file_path)


    @staticmethod
    def binary_mask_to_trimesh(point_list, cube_size=1):
        """
        Convert a binary mask to an STL file by generating a cube for each '1'.
        Then, export the combined mesh as an STL file.
        :param point_list:
        :param cube_size: the size of each cube in the binary mask.
        :return: TriMesh object representing the binary mask.
        """

        def create_cube_at_position(position, cube_size):
            cube_mesh = trimesh.creation.box(extents=(cube_size, cube_size, cube_size))
            cube_mesh.apply_translation(np.array(position) * cube_size)
            return cube_mesh
        cubes = []
        for point in point_list:
            center_offset = (0.5 * cube_size, 0.5 * cube_size, 0.5 * cube_size)
            point = np.array(point) + center_offset
            cube = create_cube_at_position(point, cube_size)
            cubes.append(cube)
        combined_mesh = trimesh.util.concatenate(cubes)
        # Export the combined mesh as an STL file
        # combined_mesh.export(output_filename)
        return combined_mesh

    @staticmethod
    def height_mask_to_tall_cubes(height_mask, cube_size=1):
        """
        Convert a height mask to an STL mesh by generating a tall cube with the height specified in z.
        This method attempts to optimize processing by reducing loop overhead and using vectorized operations.
        :param height_mask: list of tuples (x, y, z) where z is the height of the cube.
        :param cube_size: the size of each cube in the height mask.
        :return: TriMesh object representing the height mask.
        """
        # Extract positions and heights from height_mask
        positions = np.array(height_mask)[:, :2]  # x, y positions
        heights = np.array(height_mask)[:, 2]  # z heights

        # Adjust positions to include z-coordinate for translation
        full_positions = np.hstack([positions * cube_size, np.zeros((positions.shape[0], 1))])

        # Calculate the number of vertices and faces per cube
        num_cubes = len(height_mask)
        vertices_per_cube = 8
        faces_per_cube = 12
        total_vertices = vertices_per_cube * num_cubes
        total_faces = faces_per_cube * num_cubes

        # Initialize arrays for vertices and faces
        vertices = np.zeros((total_vertices, 3))
        faces = np.zeros((total_faces, 3), dtype=int)

        # Template for a unit cube
        unit_cube_vertices = np.array([
            [-0.5, -0.5, -0.5],
            [0.5, -0.5, -0.5],
            [0.5, 0.5, -0.5],
            [-0.5, 0.5, -0.5],
            [-0.5, -0.5, 0.5],
            [0.5, -0.5, 0.5],
            [0.5, 0.5, 0.5],
            [-0.5, 0.5, 0.5]
        ])

        unit_cube_faces = np.array([
            [0, 1, 2], [0, 2, 3],
            [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4],
            [2, 3, 7], [2, 7, 6],
            [0, 3, 7], [0, 7, 4],
            [1, 2, 6], [1, 6, 5]
        ])

        # Fill the vertices and faces arrays
        for i, (pos, h) in enumerate(zip(full_positions, heights)):
            start_vertex_index = i * vertices_per_cube
            start_face_index = i * faces_per_cube

            # Scale and translate unit cube vertices
            scaled_vertices = unit_cube_vertices * [cube_size, cube_size, h]
            translated_vertices = scaled_vertices + pos + [0.5 * cube_size, 0.5 * cube_size, 0.5 * h]

            vertices[start_vertex_index:start_vertex_index + vertices_per_cube] = translated_vertices
            faces[start_face_index:start_face_index + faces_per_cube] = unit_cube_faces + start_vertex_index

        # Create the mesh from vertices and faces
        combined_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        return combined_mesh

    @staticmethod
    def height_mask_to_horizontal_faces(height_mask, cube_size=1):
        """
        Convert a height mask to an STL mesh by generating a horizontal face (rectangle) with the height specified in z.
        This method attempts to optimize processing by reducing loop overhead and using vectorized operations.
        :param height_mask: list of tuples (x, y, z) where z is the height of the face.
        :param cube_size: the size of each base of the face in the height mask.
        :return: TriMesh object representing the height mask.
        """
        # Extract positions and heights from height_mask
        positions = np.array(height_mask)[:, :2]  # x, y positions
        heights = np.array(height_mask)[:, 2]  # z heights

        # Adjust positions to include z-coordinate for translation
        full_positions = positions * cube_size

        # Calculate the number of vertices and faces per face
        num_faces = len(height_mask)
        vertices_per_face = 4
        faces_per_face = 2
        total_vertices = vertices_per_face * num_faces
        total_faces = faces_per_face * num_faces

        # Initialize arrays for vertices and faces
        vertices = []
        faces = []

        # Fill the vertices and faces arrays
        vertex_index = 0
        for pos, h in zip(full_positions, heights):
            # Define the vertices for the current horizontal face
            current_vertices = np.array([
                [pos[0], pos[1], h],
                [pos[0] + cube_size, pos[1], h],
                [pos[0] + cube_size, pos[1] + cube_size, h],
                [pos[0], pos[1] + cube_size, h]
            ])

            # Add the vertices to the list
            vertices.extend(current_vertices)

            # Define the faces (triangles) for the current face
            current_faces = np.array([
                [vertex_index, vertex_index + 1, vertex_index + 2],
                [vertex_index, vertex_index + 2, vertex_index + 3]
            ])

            # Add the faces to the list
            faces.extend(current_faces)

            # Update the vertex index for the next face
            vertex_index += vertices_per_face

        # Convert lists to numpy arrays
        vertices = np.array(vertices)
        faces = np.array(faces)

        # Create the mesh from vertices and faces
        combined_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        return combined_mesh

