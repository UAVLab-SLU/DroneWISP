import os
import numpy as np
import subprocess
import pandas as pd
from PyFoam.RunDictionary.ParsedBlockMeshDict import ParsedBlockMeshDict
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
from stl.mesh_utils import StlMeshUtils


class OpenFoamController:
    """
    OpenFOAM controller, run and clean OpenFOAM case, read cell center and velocity, configure case files
    """

    def __init__(self, case_root):
        """
        :param case_root: OpenFOAM case root
        """
        self.case_root = case_root
        self.foam_stl_path = os.path.join(self.case_root, "constant", "geometry", "combined.stl")
        self.empty_openfoam_case_root = "openFoamCaseEmpty"
        self.mesh_utils = StlMeshUtils()

    # async
    def run(self):
        """
        Run "Allrun" in OpenFOAM case
        :return:
        """
        print("Running OpenFOAM case: ", self.case_root)
        if os.environ.get("IN_DOCKER", False):
            proc = subprocess.Popen(["./AllrunDocker"],
                                    cwd=self.case_root)
        else:
            proc = subprocess.Popen(["bash ./Allrun"],
                                    shell=True,
                                    cwd=self.case_root)

        proc.wait()

    def clean(self):
        """
        Clean OpenFOAM case
        :return:
        """
        print("Running OpenFOAM case: ", self.case_root)
        if os.environ.get("IN_DOCKER", False):
            proc = subprocess.Popen(["./AllcleanDocker"],
                                    cwd=self.case_root)
        else:
            proc = subprocess.Popen(["bash ./Allclean"],
                                    shell=True,
                                    cwd=self.case_root)

        proc.wait()

    def check_run_valid(self):
        """
        Checks for "FOAM FATAL ERROR" in any log file and verifies the existence of the "1" folder.
        Log files are identified by the prefix "log.".

        :return: bool indicating whether the run is valid (True) or not (False)
        """
        # First, check if any time > 0 folder exists to quickly fail if necessary
        time_folders = [f for f in os.listdir(self.case_root) if
                        f.isdigit() and os.path.isdir(os.path.join(self.case_root, f))]
        if not any(int(folder) > 0 for folder in time_folders):
            print("Error: No time folder > 0 exists.")
            return False

        # Check log files for "FOAM FATAL ERROR"
        log_files = [f for f in os.listdir(self.case_root) if f.startswith("log.")]
        for log_file in log_files:
            with open(os.path.join(self.case_root, log_file), "r") as f:
                if any("FOAM FATAL ERROR" in line for line in f):
                    print(f"Error: FOAM FATAL ERROR in {log_file}")
                    return False

        return True

    def debug_failed_run(self):
        """
        called when check_run_valid returns False
        check each log file for errors
        :return:
        """
        log_files = [f for f in os.listdir(self.case_root) if f.startswith("log.")]
        for log_file in log_files:
            with open(os.path.join(self.case_root, log_file), "r") as f:
                if any("FOAM FATAL ERROR" in line for line in f):
                    print(f"Error: FOAM FATAL ERROR in {log_file}")
                    # print next 5 lines
                    for i in range(5):
                        print(f.readline())

    def __read_c(self, time):
        """
        Read cell center from OpenFOAM case
        :param time: time folder
        :return: numpy array of cell center
        """
        case_time = os.path.join(self.case_root, str(time))
        filename = os.path.join(case_time, "C")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        content = ParsedParameterFile(filename).content
        internal_field = content["internalField"]
        array = np.array(internal_field)
        return array

    def __read_u(self, time):
        """
        Read velocity from OpenFOAM case
        :param time: time folder
        :return: numpy array of velocity
        """
        case_time = os.path.join(self.case_root, str(time))
        filename = os.path.join(case_time, "U")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        content = ParsedParameterFile(filename).content
        internal_field = content["internalField"]
        array = np.array(internal_field)
        return array

    def read_u_orig(self):
        """
        Read velocity from OpenFOAM case
        """
        filename = os.path.join(self.case_root, "0", "U.orig")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        return ParsedParameterFile(filename)

    def read_empty_u_orig(self):
        """
        Read U.orig file from empty OpenFOAM case, for wind direction generalization.
        """
        filename = os.path.join(self.empty_openfoam_case_root, "0", "U.orig")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        return ParsedParameterFile(filename)

    def read_nut_orig(self):
        """
        Read nut from OpenFOAM case
        """
        filename = os.path.join(self.case_root, "0", "nut")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        return ParsedParameterFile(filename)

    def read_empty_nut_orig(self):
        """
        Read nut from empty OpenFOAM case, for wind direction generalization.
        """
        filename = os.path.join(self.empty_openfoam_case_root, "0", "nut")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        return ParsedParameterFile(filename)

    def read_omega_orig(self):
        """
        Read omega from OpenFOAM case
        """
        filename = os.path.join(self.case_root, "0", "omega")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        return ParsedParameterFile(filename)

    def read_empty_omega_orig(self):
        """
        Read omega from empty OpenFOAM case, for wind direction generalization.
        """
        filename = os.path.join(self.empty_openfoam_case_root, "0", "omega")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        return ParsedParameterFile(filename)

    def read_block_mesh_dict(self):
        """
        Read block mesh dictionary from OpenFOAM case.
        """
        filename = os.path.join(self.case_root, "system", "blockMeshDict")
        if not os.path.exists(filename):
            raise ValueError("File do not exist:", filename)
        return ParsedBlockMeshDict(filename)

    @staticmethod
    def vertices_to_string(vertices):
        """
        Convert a list of vertices to a list of strings ready to be written to blockMeshDict.
        :param vertices: List of vertices as tuples.
        :return: List of vertices as strings.
        """
        return [f"({v[0]} {v[1]} {v[2]})" for v in vertices]

    def update_vertices(self, new_vertices):
        """
        Update vertices in the blockMeshDict.
        :param new_vertices: List of new vertex coordinates as strings.
        """
        if not isinstance(new_vertices, list):
            raise ValueError("new_vertices must be a list.")
        if len(new_vertices) != 8:
            raise ValueError("There must be exactly 8 vertices.")

        # convert to string if not already
        if not all(isinstance(v, str) for v in new_vertices):
            new_vertices = self.vertices_to_string(new_vertices)

        print("updating vertices to", new_vertices)
        block_mesh_dict = self.read_block_mesh_dict()
        if block_mesh_dict is not None:
            block_mesh_dict["vertices"] = new_vertices
            block_mesh_dict.writeFile()
            print("Updated blockMeshDict vertices.")
        else:
            print("Failed to read blockMeshDict.")

    def read_cell_and_velocity(self, time=None):
        """
        Read cell and velocity from OpenFOAM case
        :param time: time folder
        :return: two numpy array of cell and velocity
        """

        if time is None:
            # load latest time folder
            time_folders = self.get_time_folders()
            time = time_folders[-1]

        cell = self.__read_c(time)
        velocity = self.__read_u(time)

        if cell is None or velocity is None:
            if cell is None:
                print("Error: cell is None")
            if velocity is None:
                print("Error: velocity is None")
            return None, None
        else:
            return cell, velocity

    def get_time_folders(self):
        time_folders = [f for f in os.listdir(self.case_root) if os.path.isdir(os.path.join(self.case_root, f))]
        # filter out non-numeric folders
        time_folders = [f for f in time_folders if f.replace('.', '', 1).isdigit()]
        # filter out 0 folder
        time_folders = [f for f in time_folders if f != "0"]
        time_folders.sort(key=float)
        return time_folders

    def save_cell_and_velocity(self, time, save_path):
        """
        Save cell and velocity to csv file
        header : x, y, z, u, v, w
        :param time: time folder
        :param save_path: save path
        :return: None
        """
        cell, velocity = self.read_cell_and_velocity(time)
        if cell is None or velocity is None:
            return
        cell_and_velocity = np.concatenate((cell, velocity), axis=1)

        # add header
        header = "x, y, z, u, v, w"
        np.savetxt(save_path, cell_and_velocity, delimiter=",", header=header)

    def pinn_save_all_result_and_preprocess(self, range_x=None, range_y=None, range_z=None, x_min=None, x_max=None,
                                            y_min=None, y_max=None, z_min=None, z_max=None):
        """
        save the all result to csv file,
        optional param range_x, range_y, range_z to preprocess the data
        optional param x_min, x_max, y_min, y_max, z_min, z_max to preprocess the data
        if they are none, dont preprocess the data
        preprocess procedure(PINN specific):
        - convert all x y z to integer precision, cast to nearest integer using manhattan distance
        - remove duplicate data row, duplicate data is defined as same x y z after conversion, keep the first one
        - fill the missing data with 0 on x y z, missing data is defined as missing x y z after conversion and
        within the range defined by x_min, x_max, y_min, y_max, z_min, z_max
        - do a quick size check, should have range_x * range_y * range_z data points
        - sort the data by x y z, this sequence information is used to reconstruct the mesh
        - for all filled data, fill the u v w p k nut omega with null value to distinguish from real data
        - add binary mask col "bm', if there is value in u v w p k nut omega(not filled), set the mask to 0, otherwise 1
        - save the result to csv file

        :param range_x: int, number of value in x direction
        :param range_y: int, number of value in y direction
        :param range_z: int, number of value in z direction
        :param x_min: int, minimum value in x direction
        :param x_max: int, maximum value in x direction
        :param y_min: int, minimum value in y direction
        :param y_max: int, maximum value in y direction
        :param z_min: int, minimum value in z direction
        :param z_max: int, maximum value in z direction
        :return: None
        header: x, y, z, u, v, w, p, k, nut, omega
        :return:
        """
        # get all time folders
        time_folders = self.get_time_folders()

        print("Time folders: ", time_folders)
        for time in time_folders:
            cell = self.__read_c(time)
            if cell is None:
                print("Error: reading cell data failed")
                continue

            x, y, z = cell[:, 0], cell[:, 1], cell[:, 2]
            velocity = self.__read_u(time)
            if velocity is None:
                print("Error: reading velocity data failed")
                continue
            u, v, w = velocity[:, 0], velocity[:, 1], velocity[:, 2]

            k = self.__read_k(time)
            nut = self.__read_nut(time)
            omega = self.__read_omega(time)
            p = self.__read_p(time)
            if any(arr is None for arr in [k, nut, omega, p]):
                print("Error: reading additional data failed")
                continue

            # Combine all results and convert to DataFrame
            data = np.column_stack((x, y, z, u, v, w, p, k, nut, omega))
            df = pd.DataFrame(data, columns=["x", "y", "z", "u", "v", "w", "p", "k", "nut", "omega"])

            # Convert x, y, z to integer precision
            df[["x", "y", "z"]] = df[["x", "y", "z"]].round().astype(int)

            # Remove duplicates based on x, y, z
            df.drop_duplicates(subset=["x", "y", "z"], keep="first", inplace=True)

            # Sort data
            df.sort_values(by=["x", "y", "z"], inplace=True)

            # Fill missing data
            if all(v is not None for v in [range_x, range_y, range_z, x_min, x_max, y_min, y_max, z_min, z_max]):
                x_coords = np.linspace(x_min, x_max, range_x, dtype=int)
                y_coords = np.linspace(y_min, y_max, range_y, dtype=int)
                z_coords = np.linspace(z_min, z_max, range_z, dtype=int)

                mesh = pd.DataFrame(np.array(np.meshgrid(x_coords, y_coords, z_coords, indexing='ij')).T.reshape(-1, 3),
                                    columns=["x", "y", "z"])
                df = pd.merge(mesh, df, on=["x", "y", "z"], how="outer")
                df = pd.merge(mesh, df, on=["x", "y", "z"], how="left")

            # Check size
            if range_x is not None and range_y is not None and range_z is not None:
                if len(df) != range_x * range_y * range_z:
                    print(f"Error: Data size is not correct. Expected {range_x * range_y * range_z}, got {len(df)}")

            # Add binary mask
            df['bm'] = np.where(df[['u', 'v', 'w', 'p', 'k', 'nut', 'omega']].isnull().all(axis=1), 1, 0)

            # Save to CSV, adjust path as needed
            sub_dir_name = str(x_min) + "_" + str(x_max) + "_" + str(y_min) + "_" + str(y_max) + "_" + str(
                z_min) + "_" + str(z_max)
            # create sub dir if not exist
            data_dir = "../5k_training_dataset"
            if not os.path.exists(os.path.join(data_dir, sub_dir_name)):
                os.makedirs(os.path.join(data_dir, sub_dir_name))
            save_path = os.path.join(data_dir, sub_dir_name, f"result_preprocessed_{time}.csv")
            df.to_csv(save_path, index=False)
            print(f"Saved preprocessed data to {save_path}")

    def replace_mesh_with_file(self, stl_file_name):
        """
        Replace mesh in OpenFOAM case
        :param stl_file_name: stl file name
        :return: None
        """
        old_filename = os.path.join(self.case_root, "constant", "geometry", "combined.stl")
        # make a temp copy at current folder
        temp_filename = os.path.join(os.getcwd(), "combined.stl")
        os.system("cp " + old_filename + " " + temp_filename)

        # replace mesh
        try:
            os.system("cp " + stl_file_name + " " + old_filename)
        except:
            print("Error: replace mesh failed")
            os.system("cp " + temp_filename + " " + old_filename)
            return

        # clean temp file
        os.system("rm " + temp_filename)

    def replace_mesh_with_binary_mask(self, binary_mask):
        """
        Replace mesh in OpenFOAM case with binary mask
        :param list of tuple binary_mask: [(x, y, z), ...]
        :return:
        """
        # convert json array to a list of tuples

        trimesh_obj = self.mesh_utils.binary_mask_to_trimesh(binary_mask)
        try:
            trimesh_obj.export(self.foam_stl_path, 'stl_ascii')
            return True
        except Exception as e:
            print("Error: replace mesh with binary mask failed")
            print(e)
            return False

    def __read_k(self, time):
        """
        Read k from OpenFOAM case
        :param time:
        :return:
        """

        case_time = os.path.join(self.case_root, str(time))
        filename = os.path.join(case_time, "k")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        content = ParsedParameterFile(filename).content
        internal_field = content["internalField"]
        array = np.array(internal_field)
        return array

    def __read_nut(self, time):
        """
        Read nut from OpenFOAM case
        :param time:
        :return:
        """

        case_time = os.path.join(self.case_root, str(time))
        filename = os.path.join(case_time, "nut")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        content = ParsedParameterFile(filename).content
        internal_field = content["internalField"]
        array = np.array(internal_field)
        return array

    def __read_omega(self, time):
        """
        Read omega from OpenFOAM case
        :param time:
        :return:
        """

        case_time = os.path.join(self.case_root, str(time))
        filename = os.path.join(case_time, "omega")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        content = ParsedParameterFile(filename).content
        internal_field = content["internalField"]
        array = np.array(internal_field)
        return array

    def __read_p(self, time):
        """
        Read p from OpenFOAM case
        :param time:
        :return:
        """
        case_time = os.path.join(self.case_root, str(time))
        filename = os.path.join(case_time, "p")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        content = ParsedParameterFile(filename).content
        internal_field = content["internalField"]
        array = np.array(internal_field)
        return array

    def read_snappy_hex_mesh_dict(self):
        """
        Read snappyHexMeshDict from OpenFOAM case
        :return:
        """
        filename = os.path.join(self.case_root, "system", "snappyHexMeshDict")
        if not os.path.exists(filename):
            raise ValueError("File do not exist:", filename)

        return ParsedParameterFile(filename)

    @staticmethod
    def calculate_shm_inside_point(vertices):
        """
        Calculate inside point for snappyHexMeshDict from vertices.
        The center of the box on the x, y plane with a magic offset is calculated,
        and the z-coordinate is determined by the lowest point of the box plus the magic offset.
        The inside point is returned in the format "(-30 -30 0)".

        :param vertices: List of vertices forming a box [v1, v2, v3, v4, v5, v6, v7, v8], v_i = (x, y, z)
        :return: String, inside point as a string in the format "(x y z)"
        """
        magic_offset = (3.0001, 3.0001, 0.43)

        # Sum up all x and y coordinates
        sum_x = sum(vertex[0] for vertex in vertices)
        sum_y = sum(vertex[1] for vertex in vertices)
        # Find the minimum z coordinate
        min_z = min(vertex[2] for vertex in vertices)

        # Calculate average x and y
        avg_x = sum_x / len(vertices)
        avg_y = sum_y / len(vertices)

        # Apply magic offset to each axis
        inside_x = avg_x + magic_offset[0]
        inside_y = avg_y + magic_offset[1]
        inside_z = min_z + magic_offset[2]  # Original bottom z plus the magic offset

        # Return the inside point as a string formatted as "(x y z)"
        return f"({inside_x:.4f} {inside_y:.4f} {inside_z:.4f})"

    def update_shm_inside_point(self, new_inside_point):
        """
        Update inside point in snappyHexMeshDict.
        :param new_inside_point: List of new inside point coordinates as strings.
        """
        snappy_hex_mesh_dict = self.read_snappy_hex_mesh_dict()
        if snappy_hex_mesh_dict is not None:
            snappy_hex_mesh_dict["castellatedMeshControls"]["insidePoint"] = new_inside_point
            snappy_hex_mesh_dict.writeFile()
        else:
            raise ValueError("Failed to read snappyHexMeshDict.")

    def update_dimension(self, x_size, y_size, z_size):
        """
        Update dimension in blockMeshDict.
        :param x_size:
        :param y_size:
        :param z_size:
        :return:
        """
        print("Updating dimension to", x_size, y_size, z_size)
        block_mesh_dict = self.read_block_mesh_dict()
        if block_mesh_dict is not None:

            # go slightly larger than the size
            x_size_larger = x_size + x_size // 10 if x_size // 10 > 0 else x_size + 1
            y_size_larger = y_size + y_size // 10 if y_size // 10 > 0 else y_size + 1
            z_size_larger = z_size + z_size // 10 if z_size // 10 > 0 else z_size + 1

            block_mesh_dict["blocks"][2] = [x_size_larger, y_size_larger, z_size_larger]
            block_mesh_dict.writeFile()
            print("Updated blockMeshDict dimension.")
        else:
            raise ValueError("Failed to read blockMeshDict.")

    def update_wind(self, x, y, z, wind_type="uniform", turb_percent=0):
        """
        Update the wind in OpenFOAM case by changing boundary face values.
        subsequent update will overwrite the previous update
        :param x: number, wind speed in x direction
        :param y: number, wind speed in y direction
        :param z: number, wind speed in z direction
        :param wind_type: str, type of wind, "uniform" or "turbulent"
        :param turb_percent: number, percentage of turbulence
        """

        if z != 0:
            raise ValueError("z direction wind is not supported yet.")

        if x == 0 and y == 0 and z == 0:
            raise ValueError("Wind speed is zero.")

        print("Updating wind to", x, y, z)

        self.update_block_mesh_dict_bounds_from_wind_vector(x, y, z)
        self.update_u_orig_from_wind_vector(x, y, z)
        self.update_p_from_wind_vector(x, y, z)
        self.update_k_from_wind_vector(x, y, z)
        self.update_nut_from_wind_vector(x, y, z)
        self.update_omega_from_wind_vector(x, y, z)
        print("Updated u, p, k, nut, omega, blockMeshDict.")

    def update_u_orig_from_wind_vector(self, x, y, z):
        """
        Update U.orig file based on wind vector components.
        """
        if z != 0:
            raise ValueError("Error: z direction wind is not supported yet.")

        u_orig = self.read_empty_u_orig()
        zero_count = [x, y, z].count(0)

        if zero_count == 3:
            raise ValueError("Wind speed is zero.")
        if zero_count > 2:
            raise ValueError("three direction wind is not supported yet.")

        def set_boundary_fixed(boundary_name, vector):
            u_orig.content["boundaryField"][boundary_name]["type"] = "fixedValue"
            u_orig.content["boundaryField"][boundary_name]["value"] = f"uniform ({vector[0]} {vector[1]} 0)"

        def set_boundary_inlet_outlet(boundary_name, vector):
            u_orig.content["boundaryField"][boundary_name]["type"] = "inletOutlet"
            u_orig.content["boundaryField"][boundary_name]["value"] = f"uniform ({vector[0]} {vector[1]} 0)"
            u_orig.content["boundaryField"][boundary_name]["inletValue"] = f"uniform ({vector[0]} {vector[1]} 0)"

        if zero_count == 2:
            if x != 0:
                vector = (x, 0)
                if x > 0:
                    set_boundary_fixed("inlet", vector)
                    set_boundary_inlet_outlet("outlet", vector)
                else:
                    set_boundary_inlet_outlet("inlet", vector)
                    set_boundary_fixed("outlet", vector)

                set_boundary_fixed("front", vector)
                set_boundary_fixed("back", vector)

            if y != 0:
                vector = (0, y)
                if y > 0:
                    set_boundary_fixed("back", vector)
                    set_boundary_inlet_outlet("front", vector)
                else:
                    set_boundary_inlet_outlet("back", vector)
                    set_boundary_fixed("front", vector)

                set_boundary_fixed("inlet", vector)
                set_boundary_fixed("outlet", vector)

        elif zero_count == 1:
            vector = (x, y)
            set_boundary_fixed("inlet", vector)
            set_boundary_fixed("back", vector)
            set_boundary_inlet_outlet("front", vector)
            set_boundary_inlet_outlet("outlet", vector)

        # Set fixed values for walls and combined group
        set_boundary_fixed("lowerWall", (x, y))
        set_boundary_fixed("upperWall", (x, y))
        u_orig.content["boundaryField"]["combinedGroup"]["type"] = "noSlip"

        u_orig_run = self.read_u_orig()
        u_orig_run.writeFile(u_orig.content)

    def update_block_mesh_dict_bounds_from_wind_vector(self, x, y, z):
        """
        Change blockMeshDict boundaries based on wind vector components.
        Only change the boundaries fields.
        """
        block_mesh_dict = self.read_block_mesh_dict()
        zero_count = [x, y, z].count(0)

        if z != 0:
            raise ValueError("Error: z direction wind is not supported yet.")
        if zero_count == 3:
            raise ValueError("Wind speed is zero.")
        if zero_count < 1 or zero_count > 2:
            raise ValueError("Unsupported wind configuration.")

        # Simplify the boundary settings based on the wind vector component count
        def set_boundary(index, name, boundary_type, faces):
            block_mesh_dict.content["boundary"][index] = name
            block_mesh_dict.content["boundary"][index + 1] = dict(type=boundary_type, faces=faces)

        if zero_count == 2:  # One direction wind
            if x != 0:
                # Wind along the x-axis
                set_boundary(0, "inlet", "patch", [[0, 4, 7, 3]])
                set_boundary(2, "outlet", "patch", [[2, 6, 5, 1]])
                set_boundary(4, "front", "wall", [[1, 5, 4, 0]])
                set_boundary(6, "back", "wall", [[3, 7, 6, 2]])
            elif y != 0:
                # Wind along the y-axis
                set_boundary(0, "inlet", "wall", [[0, 4, 7, 3]])
                set_boundary(2, "outlet", "wall", [[2, 6, 5, 1]])
                set_boundary(4, "front", "patch", [[1, 5, 4, 0]])
                set_boundary(6, "back", "patch", [[3, 7, 6, 2]])

        elif zero_count == 1:  # Two direction wind, one component is 0
            set_boundary(0, "inlet", "patch", [[0, 4, 7, 3]])
            set_boundary(2, "outlet", "patch", [[2, 6, 5, 1]])
            set_boundary(4, "front", "patch", [[1, 5, 4, 0]])
            set_boundary(6, "back", "patch", [[3, 7, 6, 2]])

        # Common boundary settings for all supported configurations
        set_boundary(8, "upperWall", "wall", [[4, 5, 6, 7]])
        set_boundary(10, "lowerWall", "wall", [[0, 3, 2, 1]])

        block_mesh_dict.writeFile()

    def update_p_from_wind_vector(self, x, y, z):
        """
        Update p file based on wind vector components.
        """
        p = self.read_empty_p_orig()

        def set_boundary_conditions(axis_value, positive_boundary, negative_boundary):
            if axis_value > 0:
                p.content["boundaryField"][positive_boundary]["type"] = "fixedValue"
                p.content["boundaryField"][positive_boundary]["value"] = "uniform 0"
                p.content["boundaryField"][negative_boundary]["type"] = "zeroGradient"
            elif axis_value < 0:
                p.content["boundaryField"][negative_boundary]["type"] = "fixedValue"
                p.content["boundaryField"][negative_boundary]["value"] = "uniform 0"
                p.content["boundaryField"][positive_boundary]["type"] = "zeroGradient"
            else:
                p.content["boundaryField"][positive_boundary]["type"] = "zeroGradient"
                p.content["boundaryField"][negative_boundary]["type"] = "zeroGradient"

        # Set boundary conditions based on x and y wind components
        set_boundary_conditions(x, "outlet", "inlet")
        set_boundary_conditions(y, "front", "back")

        # Common boundary settings for walls and combined groups
        common_boundaries = ["lowerWall", "upperWall", "combinedGroup"]
        for boundary in common_boundaries:
            p.content["boundaryField"][boundary]["type"] = "zeroGradient"

        p_run = self.read_p_orig()
        p_run.writeFile(p.content)

    def update_k_from_wind_vector(self, x, y, z):
        """
        Update k file based on wind vector components.
        """
        if z != 0:
            raise ValueError("Error: z direction wind is not supported yet.")

        k_orig = self.read_empty_k_orig()
        zero_count = [x, y, z].count(0)

        if zero_count > 2:
            raise ValueError("Error: three direction wind is not supported yet.")

        def set_boundary(boundary_name, type_value, internal_field=True):
            k_orig.content["boundaryField"][boundary_name]["type"] = type_value
            k_orig.content["boundaryField"][boundary_name]["value"] = "$internalField"
            if type_value == "inletOutlet":
                k_orig.content["boundaryField"][boundary_name]["inletValue"] = "$internalField"

        def configure_boundaries_for_direction(positive, negative, vector_pos):
            vector = {"x": 0, "y": 0}
            vector.update(vector_pos)
            positive_type = "fixedValue" if vector['x'] > 0 or vector['y'] > 0 else "inletOutlet"
            negative_type = "inletOutlet" if vector['x'] > 0 or vector['y'] > 0 else "fixedValue"

            set_boundary(positive, positive_type)
            set_boundary(negative, negative_type)

        if zero_count == 2:
            if x != 0:
                configure_boundaries_for_direction("inlet", "outlet", {"x": x})
                # Set front and back with kqRWallFunction
                set_boundary("front", "kqRWallFunction")
                set_boundary("back", "kqRWallFunction")
            if y != 0:
                configure_boundaries_for_direction("back", "front", {"y": y})
                # Set inlet and outlet with kqRWallFunction
                set_boundary("inlet", "kqRWallFunction")
                set_boundary("outlet", "kqRWallFunction")

        elif zero_count == 1:
            # Two direction wind, simplify by using positive/negative logic for both x and y
            configure_boundaries_for_direction("inlet", "outlet", {"x": x})
            configure_boundaries_for_direction("back", "front", {"y": y})

        # Common settings for walls and combined groups
        wall_boundaries = ["lowerWall", "upperWall", "combinedGroup"]
        for boundary in wall_boundaries:
            set_boundary(boundary, "kqRWallFunction")

        k_orig_run = self.read_k_orig()
        k_orig_run.writeFile(k_orig.content)

    def update_nut_from_wind_vector(self, x, y, z):
        """
        Update nut file based on wind vector components.
        """
        nut = self.read_empty_nut_orig()

        if z != 0:
            raise ValueError("Error: z direction wind is not supported yet.")

        zero_count = [x, y, z].count(0)
        if zero_count > 2:
            raise ValueError("Error: three direction wind is not supported yet.")

        def set_uniform_value(boundary_name, type_value="uniform 0"):
            nut.content["boundaryField"][boundary_name]["value"] = type_value

        def set_type(boundary_name, type_value):
            nut.content["boundaryField"][boundary_name]["type"] = type_value

        # Set uniform values for all fields
        boundaries = ["inlet", "outlet", "front", "back", "lowerWall", "upperWall", "combinedGroup"]
        for boundary in boundaries:
            set_uniform_value(boundary)

        # Default type settings for walls and combined groups
        for boundary in ["lowerWall", "upperWall", "combinedGroup"]:
            set_type(boundary, "nutkWallFunction")

        # Type settings based on wind direction
        if zero_count == 2:
            if x != 0:
                set_type("inlet", "calculated")
                set_type("outlet", "calculated")
                set_type("front", "nutkWallFunction")
                set_type("back", "nutkWallFunction")
            if y != 0:
                set_type("front", "calculated")
                set_type("back", "calculated")
                set_type("inlet", "nutkWallFunction")
                set_type("outlet", "nutkWallFunction")

        elif zero_count == 1:
            # Two direction wind
            calculated_boundaries = ["inlet", "outlet", "front", "back"]
            for boundary in calculated_boundaries:
                set_type(boundary, "calculated")

        nut_run = self.read_nut_orig()
        nut_run.writeFile(nut.content)

    def update_omega_from_wind_vector(self, x, y, z):
        """
        Update U.orig file based on wind vector components.
        """
        if z != 0:
            raise ValueError("Error: z direction wind is not supported yet.")

        omega_orig = self.read_empty_omega_orig()
        zero_count = [x, y, z].count(0)

        if zero_count > 2:
            raise ValueError("Error: three direction wind is not supported yet.")

        def set_boundary(boundary_name, type_value, is_inlet=False):
            omega_orig.content["boundaryField"][boundary_name]["type"] = type_value
            omega_orig.content["boundaryField"][boundary_name]["value"] = "$internalField"
            if is_inlet:
                omega_orig.content["boundaryField"][boundary_name]["inletValue"] = "$internalField"

        if zero_count == 2:
            if x != 0:
                direction = "positive" if x > 0 else "negative"
                primary, secondary = ("inlet", "outlet") if direction == "positive" else ("outlet", "inlet")
                set_boundary(primary, "fixedValue")
                set_boundary(secondary, "inletOutlet", is_inlet=True)
                set_boundary("front", "omegaWallFunction")
                set_boundary("back", "omegaWallFunction")
            if y != 0:
                direction = "positive" if y > 0 else "negative"
                primary, secondary = ("front", "back") if direction == "positive" else ("back", "front")
                set_boundary(primary, "fixedValue")
                set_boundary(secondary, "inletOutlet", is_inlet=True)
                set_boundary("inlet", "omegaWallFunction")
                set_boundary("outlet", "omegaWallFunction")

        elif zero_count == 1:
            # Two direction wind, simplify by setting all boundaries involved to either fixedValue or inletOutlet
            directions = {"inlet": x, "outlet": x, "front": y, "back": y}
            for boundary, direction in directions.items():
                if direction > 0:
                    set_boundary(boundary, "fixedValue")
                elif direction < 0:
                    set_boundary(boundary, "inletOutlet", is_inlet=True)

        # Common settings for walls and combined groups
        set_boundary("lowerWall", "omegaWallFunction")
        set_boundary("upperWall", "omegaWallFunction")
        omega_orig.content["boundaryField"]["combinedGroup"]["type"] = "slip"
        omega_orig.content["boundaryField"]["combinedGroup"]["value"] = "$internalField"

        omega_orig_run = self.read_omega_orig()
        omega_orig_run.writeFile(omega_orig.content)

    def read_p_orig(self):
        filename = os.path.join(self.case_root, "0", "p")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        return ParsedParameterFile(filename)

    def read_empty_p_orig(self):
        filename = os.path.join(self.empty_openfoam_case_root, "0", "p")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        return ParsedParameterFile(filename)

    def read_k_orig(self):
        filename = os.path.join(self.case_root, "0", "k")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        return ParsedParameterFile(filename)

    def read_empty_k_orig(self):
        filename = os.path.join(self.empty_openfoam_case_root, "0", "k")
        if not os.path.exists(filename):
            raise ValueError("File do not exist: ", filename)
        return ParsedParameterFile(filename)

    def rwds_save_all_result_and_preprocess(self, range_x=None, range_y=None, range_z=None, x_min=None, x_max=None,
                                            y_min=None, y_max=None, z_min=None, z_max=None):
        """
        save the all result to csv file,
        - convert all x y z to integer precision, cast to nearest integer using manhattan distance
        - remove duplicate data row, duplicate data is defined as same x y z after conversion, keep the first one
        - fill the missing data with 0 on x y z, missing data is defined as missing x y z after conversion
         within the range defined by x_min, x_max, y_min, y_max, z_min, z_max
        - save the result to csv file header: x, y, z, u, v, w
        :param range_x: int, number of value in x direction
        :param range_y: int, number of value in y direction
        :param range_z: int, number of value in z direction
        :param x_min: int, minimum value in x direction
        :param x_max: int, maximum value in x direction
        :param y_min: int, minimum value in y direction
        :param y_max: int, maximum value in y direction
        :param z_min: int, minimum value in z direction
        :param z_max: int, maximum value in z direction
        """
        # get all time folders
        time_folders = self.get_time_folders()

        print("Time folders: ", time_folders)
        for time in time_folders:
            cell = self.__read_c(time)
            if cell is None:
                print("Error: reading cell data failed")
                continue

            x, y, z = cell[:, 0], cell[:, 1], cell[:, 2]
            velocity = self.__read_u(time)
            if velocity is None:
                print("Error: reading velocity data failed")
                continue
            u, v, w = velocity[:, 0], velocity[:, 1], velocity[:, 2]

            # Combine all results and convert to DataFrame
            data = np.column_stack((x, y, z, u, v, w))
            df = pd.DataFrame(data, columns=["x", "y", "z", "u", "v", "w"])

            # Convert x, y, z to integer precision
            df[["x", "y", "z"]] = df[["x", "y", "z"]].round().astype(int)

            # Remove duplicates based on x, y, z
            df.drop_duplicates(subset=["x", "y", "z"], keep="first", inplace=True)

            # Sort data
            df.sort_values(by=["x", "y", "z"], inplace=True)

            # Fill missing data
            if all(v is not None for v in [range_x, range_y, range_z, x_min, x_max, y_min, y_max, z_min, z_max]):
                x_coords = np.linspace(x_min, x_max, range_x, dtype=int)
                y_coords = np.linspace(y_min, y_max, range_y, dtype=int)
                z_coords = np.linspace(z_min, z_max, range_z, dtype=int)

                mesh = pd.DataFrame(np.array(np.meshgrid(x_coords, y_coords, z_coords, indexing='ij')).T.reshape(-1, 3),
                                    columns=["x", "y", "z"])
                df = pd.merge(mesh, df, on=["x", "y", "z"], how="outer")
                df = pd.merge(mesh, df, on=["x", "y", "z"], how="left")

            # Check size
            if range_x is not None and range_y is not None and range_z is not None:
                if len(df) != range_x * range_y * range_z:
                    print(f"Error: Data size is not correct. Expected {range_x * range_y * range_z}, got {len(df)}")

            save_path = os.path.join(self.case_root, f"rwds_{time}.csv")
            df.to_csv(save_path, index=False)
            print(f"Saved preprocessed data to {save_path}")


if __name__ == "__main__":
    case_root = "openFoamCase"
    foam = OpenFoamController(case_root)
    foam.clean()
    foam.update_wind(10, 0, 0)
    # foam.run()
    # print(foam.check_run_valid())

    # for x in [10, -10, 0]:
    #     for y in [10, -10, 0]:
    #         foam.clean()
    #         foam.update_wind(x, y, 0)
    #         print("testing: x=", x, " y=", y, " z=", 0)
    #         foam.run()
    #         if not foam.check_run_valid():
    #             print("Fail")
    #         else:
    #             print("Pass")

    # This part can automate things
    # value_vertices = [(-100, -100, 0),
    #                   (100, -100, 0),
    #                   (100, 100, 0),
    #                   (-100, 100, 0),
    #                   (-100, -100, 25),
    #                   (100, -100, 25),
    #                   (100, 100, 25),
    #                   (-100, 100, 25)]
    # print("box vertices: ", value_vertices)
    # vertices_string = foam.vertices_to_string(value_vertices)
    # foam.update_vertices(vertices_string)
    # inside_point = foam.calculate_shm_inside_point(value_vertices)
    # print("inside_point: ", inside_point)
    # foam.update_shm_inside_point(inside_point)
    # foam.clean()
    # foam.run()
    # if not foam.check_run_valid():
    #     foam.debug_failed_run()
    ##########################

    ## Works
    ## read cell and velocity
    # t = 10
    # foam.save_cell_and_velocity(t, "cell_and_velocity_" + str(t) + ".csv")

    # foam.pinn_save_all_result_and_preprocess(range_x=50, range_y=50, range_z=25, x_min=-25, x_max=25, y_min=-25,
    #                                          y_max=25, z_min=0, z_max=25)

    # works
    # foam.update_shm_inside_point("(-30 -30 0)")

    # foam.set_wind_velocity(9)

    # print(foam.calculate_rotation((10, 5, 0)))
    # print(foam.calculate_velocity((10, 5, 0)))
