import os
import numpy as np
import subprocess
import PyFoam
from PyFoam.RunDictionary.SolutionFile import SolutionFile
import math


def calculate_rotation(wind_vector):
    """
    Calculate rotation in degrees clockwise from x-axis to make wind vector parallel to x-axis
    :param wind_vector: tuple of wind vector (x, y, z)
    :return: rotation in degrees
    """
    x, y, z = wind_vector
    rotation = np.arctan2(y, x) * 180 / np.pi
    return round(rotation, 2)


class OpenFoamController:
    """
    OpenFOAM controller, run and clean OpenFOAM case, read cell center and velocity, configure case files
    """

    def __init__(self, case_root):
        """
        :param case_root: OpenFOAM case root
        """
        self.case_root = case_root
        self.mesh_stl = StlMeshUtils(os.path.join(
            self.case_root, "constant", "geometry", "combined.stl"))

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
        content = PyFoam.RunDictionary.ParsedParameterFile.ParsedParameterFile(
            filename)
        # print(content)
        content["internalField"] = "uniform (" + str(velocity) + " 0 0)"
        content.writeFile()

    def set_wind_vector(self, wind_vector):
        """
        Set wind vector in OpenFOAM case
        :param wind_vector: tuple of wind vector (x, y, z)
        :return: None
        """

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
        old_filename = os.path.join(
            self.case_root, "constant", "geometry", "combined.stl")
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

    def change_openfoam_inlet_face(self, wind_direction_string, wind_speed):
        """
        Task1:
        Change the inlet face of the openfoam case to the given wind direction and speed
        If the wind direction is only N, E, S, W, then only one face will be changed, change the corresponding face as inlet
        If the wind direction is NE, SE, SW, NW, then two faces will be changed, change the corresponding faces as inlet
        also there will be two initial velocity vectors, one for each face, see python/openFoamCase/0/include/initialConditions.

        Task2:
        Change the wind speed, the wind speed is the magnitude of the wind vector
        how to change it? python/openFoamCase/0/include/initialConditions file


        Tips: use PyFoam package to parse the files, the files that you are going to change are in
        - python/openFoamCase/0/U.orig
        - python/openFoamCase/0/include/initialConditions
        - python/openFoamCase/system/blockMeshDict

        :param wind_direction_string: The wind direction string, "N", "NE", "E", "SE", "S", "SW", "W", "NW"
        :param wind_speed vector: The wind speed vector (x, y, z)
        :return: None
        """
        # TODO: Seyun's task

    solve = SolutionFile("python/openFoamCase/system", "fvSolution")
    match wind_direction_string:
        case "N":
            solve.replaceBoundary("lowerWall", wind_speed)
        case "NE":
            solve.replaceBoundary("lowerWall", wind_speed)
            solve.replaceBoundary("inlet", wind_speed)
        case "E":
            solve.replaceBoundary("inlet", wind_speed)
        case "SE":
            solve.replaceBoundary("frontAndBack", wind_speed)
            solve.replaceBoundary("inlet", wind_speed)
        case "S":
            solve.replaceBoundary("frontAndBack", wind_speed)
        case "SW":
            solve.replaceBoundary("frontAndBack", wind_speed)
            solve.replaceBoundary("inlet", wind_speed)
        case "W":
            solve.replaceBoundary("outlet", wind_speed)
        case "NW":
            solve.replaceBoundary("lowerWall", wind_speed)
            solve.replaceBoundary("inlet", wind_speed)

    # read 0/include/initialConditions

    # change flowVelocity based on input direction, if N : (0, 10, 0), if E : (10, 0, 0)


if wind_direction_string == "N":
    flowVelocity = [0, 10, 0]
elif wind_direction_string == "NE":
    flowVelocity = [10, 10, 0]
elif wind_direction_string == "E":
    flowVelocity = [10, 0, 0]
elif wind_direction_string == "SE":
    flowVelocity = [10, -10, 0]
elif wind_direction_string == "S":
    flowVelocity = [0, -10, 0]
elif wind_direction_string == "SW":
    flowVelocity = [-10, -10, 0]
elif wind_direction_string == "W":
    flowVelocity = [-10, 0, 0]
elif wind_direction_string == "NW":
    flowVelocity = [-10, 10, 0]
else:
    raise ValueError(
        "Invalid wind direction. Expected one of: N, NE, E, SE, S, SW, W, NW")

    # save the file
read_file.writeFile()

# part2: change inlet face
# read system/blockMeshDict
blockMeshDict = ParsedParameterFile(self.case_root + "/system/blockMeshDict")
vertices = blockMeshDict.content['vertices']
blocks = blockMeshDict.content['blocks']
boundary = blockMeshDict.content['boundary']
print(boundary)

# change inlet face based on input direction
if wind_direction_string == "N":
    inlet_face = boundary['lowerWall']
    inlet_face['faces'] = "(3 7 6 2)"
elif wind_direction_string == "NE":
    inlet_face1 = boundary['lowerWall']
    inlet_face1['faces'] = "(3 7 6 2)"
    inlet_face2 = boundary['inlet']
    inlet_face2['faces'] = "(7 8 4 6)"
elif wind_direction_string == "E":
    inlet_face = boundary['inlet']
    inlet_face['faces'] = "(7 8 4 6)"
elif wind_direction_string == "SE":
    inlet_face1 = boundary['frontAndBack']
    inlet_face1['faces'] = "(7 8 4 6)"
    inlet_face2 = boundary['inlet']
    inlet_face2['faces'] = "(8 5 1 4)"
elif wind_direction_string == "S":
    inlet_face = boundary['frontAndBack']
    inlet_face['faces'] = "(8 5 1 4)"
elif wind_direction_string == "SW":
    inlet_face1 = boundary['frontAndBack']
    inlet_face1['faces'] = "(8 5 1 4)"
    inlet_face2 = boundary['outlet']
    inlet_face2['faces'] = "(5 3 2 1)"
elif wind_direction_string == "W":
    inlet_face = boundary['outlet']
    inlet_face['faces'] = "(5 3 2 1)"
elif wind_direction_string == "NW":
    inlet_face1 = boundary['lowerWall']
    inlet_face1['faces'] = "(5 3 2 1)"
    inlet_face2 = boundary['outlet']
    inlet_face2['faces'] = "(3 7 6 2)"
else:
    raise ValueError(
        "Invalid wind direction. Expected one of: N, NE, E, SE, S, SW, W, NW")

# hint: (3 7 6 2) is a face formed by vertices 3, 7, 6, 2, those are vertice indices in the vertices list in the same file
# hint: you need to find the correct vertices for the inlet face based on the input direction


# move those (a b c d) to the correct definition of inlet face


# save the file
blockMeshDict.writeFile()

## Example : assume I got "W" and 10 as input
# wind_speed = 10
# wind_direction_string = "W"


# U_file = ParsedParameterFile(self.openfoam_case + "/0/U")
# inlet_faces = U_file.content['boundaryField']['inlet']
# wind_vector_str = f"uniform ({self.wind_speeds} 0 0)"
# inlet_faces['value'] = wind_vector_str
# U_file.writeFile()
# self.wind_direction = wind_direction_string
# if wind_direction_string in ["NE", "SE", "SW", "NW"]:
#     # Adjust for diagonal wind direction
#     self.wind_speeds = wind_speed / math.sqrt(2)
#
# # Manipulate OpenFOAM files
# U_file = ParsedParameterFile(self.openfoam_case + "/0/U")
# inlet_faces = U_file.content['boundaryField']['inlet']
# inlet_faces['value'].setUniform(self.wind_speed)
# wind_vector_str = f"uniform ({self.wind_speed} 0 0)"
# inlet_faces['value'] = wind_vector_str
# U_file.writeFile()


if __name__ == "__main__":
    case_root = "openFoamCase"
    foam = OpenFoamController(case_root)
    # foam.clean()
    # # foam.set_wind_velocity(9)
    # # foam.run()
    # print(foam.calculate_rotation((10, 5, 0)))
    # print(foam.calculate_velocity((10, 5, 0)))
    foam.change_openfoam_inlet_face("N", 10)
