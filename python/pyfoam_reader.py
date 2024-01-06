import os
import numpy as np
import subprocess
import PyFoam
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
        self.mesh_stl = StlMeshUtils(os.path.join(self.case_root, "constant", "geometry", "combined.stl"))

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

    def __read_cell_center(self, time):
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

    def __read_velocity(self, time):
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

    def read_cell_and_velocity(self, time):
        """
        Read cell and velocity from OpenFOAM case
        :param time: time folder
        :return: two numpy array of cell and velocity
        """
        cell = self.__read_cell_center(time)
        velocity = self.__read_velocity(time)

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
        csv format: x, y, z, u, v, w
        :param time: time folder
        :param save_path: save path
        :return: None
        """
        cell, velocity = self.read_cell_and_velocity(time)
        if cell is None or velocity is None:
            return
        cell_and_velocity = np.concatenate((cell, velocity), axis=1)
        np.savetxt(save_path, cell_and_velocity, delimiter=",")

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
        #print(content)
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


if __name__ == "__main__":
    case_root = "openFoamCase"
    foam = OpenFoamController(case_root)
    foam.clean()
    #foam.set_wind_velocity(9)
    # foam.run()
    print(foam.calculate_rotation((10, 5, 0)))
    print(foam.calculate_velocity((10, 5, 0)))
