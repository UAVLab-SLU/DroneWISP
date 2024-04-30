import os

import requests

from pyfoam_reader import OpenFoamController
from openfoam_csv_reader import FoamCSVReader
import threading


class CFDManager:
    """
    This class is responsible for
    - managing CFD runs by interfacing with openfoam controller class
    - report state
    - change openfoam case
    - setup mesh using binary mask
    """

    def __init__(self):
        self.range_x = None
        self.range_y = None
        self.range_z = None
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None
        self.z_min = None
        self.z_max = None

        self.state = "idle"  # can be "idle", "cfd_running", "ready"
        self.openfoam_case_ready = False
        self.stl_mesh_ready = False
        self.wind_type = "uniform"  # default wind type, can be "uniform", "turbulent", "turbulent_multi_source"
        self.openfoam_controller = OpenFoamController("openFoamCase")
        self.foam_csv_reader = FoamCSVReader("openFoamCase")

    def get_state(self):
        return self.state

    def replace_mesh_with_binary_mask(self, request_json):
        """
        Replace the mesh with the binary mask
        :param request_json: raw json from the request
        structure {'maskData': [{'x': -50, 'y': -50, 'z': 0}, {'x': -50, 'y': -49, 'z': 0}, ...]}
        :return: boolean success or failure
        """

        if self.state == "cfd_running":
            print("CFD simulation is running, cannot replace mesh with binary mask")
            return False

        self.state = "idle"

        # json object to list of tuples
        bm_list = [(vertex['x'], vertex['y'], vertex['z']) for vertex in request_json['maskData']]
        replace_success = self.openfoam_controller.replace_mesh_with_binary_mask(bm_list)
        if replace_success:
            self.stl_mesh_ready = True
            if self.openfoam_case_ready and self.stl_mesh_ready:
                self.run_simulation_and_preprocess_thread()
            return True
        else:
            return False

    def update_openfoam_case(self, request_json):
        """
        Update the openfoam case with the new settings
        :param request_json: raw json from the request
        expected format: {'wind_speed_x': 0, 'wind_speed_y': 0, 'wind_speed_z': 0, 'wind_type': 'uniform',
        'x_length': 50, 'y_length': 50, 'z_length': 20,
        'v1': {'x': -50, 'y': -50, 'z': -5}, 'v2': {'x': 50, 'y': -50, 'z': -5} 'v3': {'x': 50, 'y': 50, 'z': -5},
        'v4': {'x': -50, 'y': 50, 'z': -5}, 'v5': {'x': -50, 'y': -50, 'z': 5}, 'v6': {'x': 50, 'y': -50, 'z': 5},
        'v7': {'x': 50, 'y': 50, 'z': 5}, 'v8': {'x': -50, 'y': 50, 'z': 5}}
        :return: success or failure
        """

        # check if the simulation is already running
        if self.state == "cfd_running":
            print("CFD simulation is already running")
            return False

        # type check
        if (not isinstance(request_json['wind_speed_x'], (int, float)) or
                not isinstance(request_json['wind_speed_y'], (int, float)) or
                not isinstance(request_json['wind_speed_z'], (int, float))):
            # try to convert to float
            try:
                request_json['wind_speed_x'] = float(request_json['wind_speed_x'])
                request_json['wind_speed_y'] = float(request_json['wind_speed_y'])
                request_json['wind_speed_z'] = float(request_json['wind_speed_z'])
            except ValueError:
                return False
        if (not isinstance(request_json['x_length'], int) or
                not isinstance(request_json['y_length'], int) or
                not isinstance(request_json['z_length'], int)):
            # try to convert to int
            try:
                request_json['x_length'] = int(request_json['x_length'])
                request_json['y_length'] = int(request_json['y_length'])
                request_json['z_length'] = int(request_json['z_length'])
            except ValueError:
                return False
        vertices = [request_json['v1'], request_json['v2'], request_json['v3'], request_json['v4'],
                    request_json['v5'], request_json['v6'], request_json['v7'], request_json['v8']]
        list_vertex = []
        for vertex in vertices:
            if (not isinstance(vertex['x'], (int, float)) or
                    not isinstance(vertex['y'], (int, float)) or
                    not isinstance(vertex['z'], (int, float))):
                # try to convert to float
                try:
                    vertex['x'] = float(vertex['x'])
                    vertex['y'] = float(vertex['y'])
                    vertex['z'] = float(vertex['z'])
                except ValueError:
                    return False
            list_vertex.append((vertex['x'], vertex['y'], vertex['z']))

        self.range_x = request_json['x_length'] * 2 + 1
        self.range_y = request_json['y_length'] * 2 + 1
        self.range_z = request_json['z_length']
        self.x_min = min([vertex['x'] for vertex in vertices])
        self.x_max = max([vertex['x'] for vertex in vertices])
        self.y_min = min([vertex['y'] for vertex in vertices])
        self.y_max = max([vertex['y'] for vertex in vertices])
        self.z_min = min([vertex['z'] for vertex in vertices])
        self.z_max = max([vertex['z'] for vertex in vertices])

        self.state = "idle"

        self.openfoam_controller.update_vertices(list_vertex)
        self.openfoam_controller.update_dimension(request_json['x_length'] * 2 + 1, request_json['y_length'] * 2 + 1,
                                                  request_json['z_length'])
        self.openfoam_controller.update_wind(request_json['wind_speed_x'], request_json['wind_speed_y'],
                                             request_json['wind_speed_z'], request_json['wind_type'])

        self.openfoam_case_ready = True
        if self.openfoam_case_ready and self.stl_mesh_ready:

            self.run_simulation_and_preprocess_thread()
        return True

    def run_simulation_and_preprocess_thread(self):
        """
        Run the simulation on separate thread, and prepare the results
        """

        # check if the simulation is already running
        if self.state == "cfd_running":
            print("CFD simulation is already running")
            return

        # check if variables are set
        if (self.range_x is None or self.range_y is None or self.range_z is None or
                self.x_min is None or self.x_max is None or
                self.y_min is None or self.y_max is None or
                self.z_min is None or self.z_max is None):
            print("Variables are not set")
            print(self.range_x, self.range_y, self.range_z, self.x_min, self.x_max, self.y_min, self.y_max, self.z_min,
                  self.z_max)
            return

        if not self.openfoam_case_ready or not self.stl_mesh_ready:
            print("OpenFOAM case or STL mesh is not ready")
            return


        # Define a target function for the thread
        def target_function():
            self.state = "cfd_running"
            print("Running CFD simulation")
            self.openfoam_controller.clean()
            self.openfoam_controller.run()

            if self.openfoam_controller.check_run_valid():
                print("CFD simulation completed")
            else:
                print("Error: invalid run")
                self.openfoam_controller.debug_failed_run()
                self.state = "cfd_fail"
                self.reset_flag()
                # if in docker IN_DOCKER = True,
                if os.getenv("IN_DOCKER", False):
                    requests.post("http://drv_server:5000/cfdFailNotify")
                else:
                    requests.post("http://192.168.1.181:5000/cfdFailNotify")
                self.state = "idle"
                return

            print("Preprocessing CFD results")
            self.openfoam_controller.rwds_save_all_result_and_preprocess(range_x=self.range_x, range_y=self.range_y,
                                                                        range_z=self.range_z, x_min=self.x_min, y_min=self.y_min,
                                                                        z_min=self.z_min, x_max=self.x_max, y_max=self.y_max,
                                                                        z_max=self.z_max)
            self.foam_csv_reader.rwds_load_first_csv(int(self.openfoam_controller.get_time_folders()[0]))

            print("Ready to serve wind data")
            self.state = "ready"
            self.reset_flag()
            # if in docker IN_DOCKER = True,
            if os.getenv("IN_DOCKER", False):
                requests.post("http://drv_server:5000/cfdDoneNotify")
            else:
                requests.post("http://192.168.1.181:5000/cfdDoneNotify") # TODO: hard coded DRV ip

        simulation_thread = threading.Thread(target=target_function)
        simulation_thread.start()

    def reset_flag(self):
        """
        Clean the simulation, on current thread
        """

        self.stl_mesh_ready = False
        self.openfoam_case_ready = False

    def get_wind_vector_from_df(self, cartesian_coordinates):
        """
        Get the wind vector from the preprocessed dataframe
        :param cartesian_coordinates: [x, y, z] coordinates
        :return: wind vector [x, y, z]
        """
        # check if case is prepared
        if self.state != "ready":
            print("Wind data is not ready")
            return None
        vel = self.foam_csv_reader.get_spacial_temporal_velocity_next_time_step(cartesian_coordinates)
        return vel



