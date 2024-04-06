import os
import numpy as np
import subprocess
import PyFoam
import pandas as pd
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
        self.stl_path = os.path.join(self.case_root, "constant", "geometry", "combined.stl")

    # async

    def run(self):
        """
        Run "Allrun" in OpenFOAM case
        :return:
        """
        print("Running OpenFOAM case: ", self.case_root)
        proc = subprocess.Popen(["bash ./Allrun"],
                                shell=True,
                                cwd=self.case_root,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        proc.wait()

    def clean(self):
        """
        Clean OpenFOAM case
        :return:
        """
        print("Cleaning OpenFOAM case: ", self.case_root)
        proc = subprocess.Popen(["bash ./Allclean"],
                                shell=True,
                                cwd=self.case_root,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        proc.wait()

    def check_run_valid(self):
        """
        Checks for "FOAM FATAL ERROR" in any log file and verifies the existence of the "1" folder.
        Log files are identified by the prefix "log.".

        :return: bool indicating whether the run is valid (True) or not (False)
        """
        # First, check if "1" folder exists to quickly fail if necessary
        if not os.path.exists(os.path.join(self.case_root, "1")):
            print("Error: '1' folder does not exist, did not run successfully")
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
            print("File do not exist: ", filename)
            return None
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
            print("File do not exist: ", filename)
            return None
        content = ParsedParameterFile(filename).content
        internal_field = content["internalField"]
        array = np.array(internal_field)
        return array

    def read_block_mesh_dict(self):
        """
        Read block mesh dictionary from OpenFOAM case.
        """
        filename = os.path.join(self.case_root, "system", "blockMeshDict")
        if not os.path.exists(filename):
            print("File do not exist:", filename)
            return None

        return ParsedParameterFile(filename)

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
        block_mesh_dict = self.read_block_mesh_dict()
        if block_mesh_dict is not None:
            block_mesh_dict["vertices"] = new_vertices
            block_mesh_dict.writeFile()
        else:
            print("Failed to read blockMeshDict.")

    def read_cell_and_velocity(self, time):
        """
        Read cell and velocity from OpenFOAM case
        :param time: time folder
        :return: two numpy array of cell and velocity
        """
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

    def pinn_save_all_result_and_preprocess(self, range_x=None, range_y=None, range_z=None, x_min=None, x_max=None, y_min=None, y_max=None, z_min=None, z_max=None):
        """
        save the all result to csv file,
        optional param range_x, range_y, range_z to preprocess the data
        optional param x_min, x_max, y_min, y_max, z_min, z_max to preprocess the data
        if they are none, dont preprocess the data
        preprocess procedure(PINN specific):
        - convert all x y z to integer precision, cast to nearest integer using manhattan distance
        - remove duplicate data row, duplicate data is defined as same x y z after conversion, keep the first one
        - fill the missing data with 0 on x y z, missing data is defined as missing x y z after conversion and within the range defined by x_min, x_max, y_min, y_max, z_min, z_max
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
        time_folders = [f for f in os.listdir(self.case_root) if os.path.isdir(os.path.join(self.case_root, f))]
        # filter out non-numeric folders
        time_folders = [f for f in time_folders if f.replace('.', '', 1).isdigit()]
        # filter out 0 folder
        time_folders = [f for f in time_folders if f != "0"]

        # Sort folders numerically by converting to float
        time_folders.sort(key=float)

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

            # Quick size check
            if not len(df) == range_x * range_y * range_z:
                print(f"Size mismatch for time {time}, expected {range_x * range_y * range_z}, got {len(df)}")
                continue

            # Sort data
            df.sort_values(by=["x", "y", "z"], inplace=True)

            # Fill missing data and
            # TODO: This is a complex procedure requiring generation of a complete grid and then merging it with existing data
            # generate a grid with dimensions range_x, range_y, range_z

            # Add binary mask
            df['bm'] = np.where(df[['u', 'v', 'w', 'p', 'k', 'nut', 'omega']].isnull().all(axis=1), 0, 1)

            # Save to CSV, adjust path as needed
            save_path = os.path.join(self.case_root, f"result_preprocessed_{time}.csv")
            df.to_csv(save_path, index=False)
            print(f"Saved preprocessed data to {save_path}")

            # save to csv


    def __set_wind_velocity(self, velocity):
        """
        Set wind velocity in OpenFOAM case
        :param velocity: wind velocity value, float or int
        :return: None
        """

        # check type
        if not isinstance(velocity, float) and not isinstance(velocity, int):
            print("Wind velocity must be float or int")
            return
        filename = os.path.join(self.case_root, "0", "U.orig")

        # TODO: this does not work
        content = PyFoam.RunDictionary.ParsedParameterFile.ParsedParameterFile(filename)
        # print(content)
        content["internalField"] = "uniform (" + str(velocity) + " 0 0)"
        content.writeFile()

    def set_wind_vector(self, wind_vector):
        """
        Set wind vector in OpenFOAM case
        :param wind_vector: tuple of wind vector (x, y, z)
        :return: None
        """

    def calculate_rotation(self, wind_vector):
        """
        Calculate rotation in degrees clockwise from x-axis to make wind vector parallel to x-axis
        :param wind_vector: tuple of wind vector (x, y, z)
        :return: rotation in degrees
        """
        x, y, z = wind_vector
        rotation = np.arctan2(y, x) * 180 / np.pi
        return round(rotation, 2)

    @staticmethod
    def calculate_velocity(wind_vector):
        """
        Calculate velocity in x-axis
        :param wind_vector: tuple of wind vector (x, y, z)
        :return: combined velocity
        """
        return round(np.linalg.norm(wind_vector), 2)

    def replace_mesh(self, stl_file_name):
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

    def __read_k(self, time):
        """
        Read k from OpenFOAM case
        :param time:
        :return:
        """

        case_time = os.path.join(self.case_root, str(time))
        filename = os.path.join(case_time, "k")
        if not os.path.exists(filename):
            print("File do not exist: ", filename)
            return None
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
            print("File do not exist: ", filename)
            return None
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
            print("File do not exist: ", filename)
            return None
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
            print("File do not exist: ", filename)
            return None
        content = ParsedParameterFile(filename).content
        internal_field = content["internalField"]
        array = np.array(internal_field)
        return array

    def __read_snappy_hex_mesh_dict(self):
        """
        Read snappyHexMeshDict from OpenFOAM case
        :return:
        """
        filename = os.path.join(self.case_root, "system", "snappyHexMeshDict")
        if not os.path.exists(filename):
            print("File do not exist:", filename)
            return None

        return ParsedParameterFile(filename)

    def calculate_shm_inside_point(self, vertices):
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
        snappy_hex_mesh_dict = self.__read_snappy_hex_mesh_dict()
        if snappy_hex_mesh_dict is not None:
            snappy_hex_mesh_dict["castellatedMeshControls"]["insidePoint"] = new_inside_point
            snappy_hex_mesh_dict.writeFile()
        else:
            print("Failed to read snappyHexMeshDict.")


if __name__ == "__main__":
    case_root = "openFoamCase"
    foam = OpenFoamController(case_root)
    ####################### This part can automate things
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

    foam.pinn_save_all_result_and_preprocess()

    # works
    # foam.update_shm_inside_point("(-30 -30 0)")

    # foam.set_wind_velocity(9)

    # print(foam.calculate_rotation((10, 5, 0)))
    # print(foam.calculate_velocity((10, 5, 0)))
