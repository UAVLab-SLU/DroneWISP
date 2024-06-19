import os
import time

import requests

from open_foam_controller import OpenFoamController
from openfoam_csv_reader import FoamCSVReader
from openfoam_kd_tree_reader import FoamKDTreeReader
import threading


class CFDManager:
    """
    This class is responsible for
    - managing CFD runs by interfacing with openfoam controller class
    - report state
    - change openfoam case
    - setup mesh using binary mask
    """

    def __init__(self, preprocess_mode="int_precision"):
        self.preprocess_mode = preprocess_mode  # can be "int_precision", "kd_tree"
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
        self.openfoam_controller = OpenFoamController("openFoamCase", preprocess_mode)
        if preprocess_mode == "kd_tree":
            print("Using KDTree")
            self.foam_kd_tree_reader = FoamKDTreeReader("openFoamCase")
        else:
            self.foam_csv_reader = FoamCSVReader("openFoamCase")
        self.DEBUG_USE_SAME_DATA = False # for debugging, use the same data for subsequent requests


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

        if self.DEBUG_USE_SAME_DATA:
            self.stl_mesh_ready = True
            self.state = "ready"
            return True

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
        'dt': 1, 'end_time': 51, 'write_interval': 50,
        'v1': {'x': -50, 'y': -50, 'z': -5}, 'v2': {'x': 50, 'y': -50, 'z': -5} 'v3': {'x': 50, 'y': 50, 'z': -5},
        'v4': {'x': -50, 'y': 50, 'z': -5}, 'v5': {'x': -50, 'y': -50, 'z': 5}, 'v6': {'x': 50, 'y': -50, 'z': 5},
        'v7': {'x': 50, 'y': 50, 'z': 5}, 'v8': {'x': -50, 'y': 50, 'z': 5}}
        :return: success or failure
        """

        # check if the simulation is already running
        if self.state == "cfd_running":
            print("CFD simulation is already running")
            return False

        if self.DEBUG_USE_SAME_DATA:
            self.openfoam_case_ready = True
            self.state = "ready"
            # simulate a delay
            import time
            time.sleep(3)
            self.notify_ready()
            return True

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

        if 'wind_type' in request_json:
            self.wind_type = request_json['wind_type']
            if self.wind_type not in ["uniform", "turbulent", "turbulent_multi_source"]:
                return False

            if self.wind_type != "uniform":
                # check if the turbulent wind is set correctly
                if 'turb_percent' not in request_json:
                    # use default value
                    request_json['turb_percent'] = 10
                if not isinstance(request_json['turb_percent'], (int, float)):
                    try:
                        request_json['turb_percent'] = float(request_json['turb_percent'])
                    except ValueError:
                        request_json['turb_percent'] = 10
                if request_json['turb_percent'] <= 0:
                    # equivalent to uniform wind
                    self.wind_type = "uniform"
                    request_json['wind_type'] = "uniform"
                    request_json['turb_percent'] = 0

                # update end time if not set
                if 'end_time' not in request_json:
                    request_json['end_time'] = 26
                if not isinstance(request_json['end_time'], (int, float)):
                    try:
                        request_json['end_time'] = float(request_json['end_time'])
                    except ValueError:
                        request_json['end_time'] = 26

                if 'dt' not in request_json:
                    request_json['dt'] = 1
                if not isinstance(request_json['dt'], (int, float)):
                    try:
                        request_json['dt'] = float(request_json['dt'])
                    except ValueError:
                        request_json['dt'] = 1

                request_json['write_interval'] = 1

            else:
                request_json['turb_percent'] = 0
                request_json['wind_type'] = "uniform"
                request_json['dt'] = 1
                request_json['end_time'] = 51
                request_json['write_interval'] = 50


        self.state = "idle"

        self.openfoam_controller.update_vertices(list_vertex)
        self.openfoam_controller.update_shm_inside_point(self.openfoam_controller.calculate_shm_inside_point(list_vertex))
        self.openfoam_controller.update_dimension(request_json['x_length'] * 2 + 1, request_json['y_length'] * 2 + 1,
                                                  request_json['z_length'])
        self.openfoam_controller.update_end_time(request_json['end_time'])
        self.openfoam_controller.update_write_interval(request_json['write_interval'])
        self.openfoam_controller.update_dt(request_json['dt'])
        self.openfoam_controller.update_wind(request_json['wind_speed_x'], request_json['wind_speed_y'],
                                             request_json['wind_speed_z'], request_json['wind_type'], request_json['turb_percent'])

        if 'dt' in request_json:
            # convert to float if not
            if not isinstance(request_json['dt'], (int, float)):
                try:
                    request_json['dt'] = float(request_json['dt'])
                except ValueError:
                    return False
            self.openfoam_controller.update_dt(request_json['dt'])
        if 'end_time' in request_json:
            if not isinstance(request_json['end_time'], (int, float)):
                try:
                    request_json['end_time'] = float(request_json['end_time'])
                except ValueError:
                    return False
            self.openfoam_controller.update_end_time(request_json['end_time'])
        if 'write_interval' in request_json:
            if not isinstance(request_json['write_interval'], int):
                try:
                    request_json['write_interval'] = int(request_json['write_interval'])
                except ValueError:
                    return False
            self.openfoam_controller.update_write_interval(request_json['write_interval'])

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

        if self.DEBUG_USE_SAME_DATA:
            self.state = "ready"
            return

        # reset kd tree reader
        if self.preprocess_mode == "kd_tree":
            self.foam_kd_tree_reader.clear_time_list()

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
            start_time = time.time()
            self.openfoam_controller.clean()
            self.openfoam_controller.run()

            if self.openfoam_controller.check_run_valid():
                print(f"CFD simulation completed, time taken: {time.time() - start_time:.2f} seconds")
            else:
                print("Error: invalid run")
                self.openfoam_controller.debug_failed_run()
                self.state = "cfd_fail"
                self.reset_flag()
                self.notify_fail()
                self.state = "idle"
                return

            print("Preprocessing CFD results")

            start_time = time.time()
            self.openfoam_controller.wisp_save_all_result_and_preprocess(range_x=self.range_x, range_y=self.range_y,
                                                                         range_z=self.range_z, x_min=self.x_min, y_min=self.y_min,
                                                                         z_min=self.z_min, x_max=self.x_max, y_max=self.y_max,
                                                                         z_max=self.z_max)
            if self.preprocess_mode == "kd_tree":
                pass
            else:
                self.foam_csv_reader.wisp_load_first_df(int(self.openfoam_controller.get_time_folders()[0]))

            print(f"Preprocessing CFD results completed, time taken: {time.time() - start_time:.2f} seconds")
            print("Ready to serve wind data")
            self.state = "ready"
            self.reset_flag()
            # if in docker IN_DOCKER = True,
            self.notify_ready()



        simulation_thread = threading.Thread(target=target_function)
        simulation_thread.start()

    @staticmethod
    def notify_fail():
        # if in docker IN_DOCKER = True,
        if os.getenv("IN_DOCKER", False):
            requests.post("http://drv_server:5000/cfdFailNotify")
        else:
            requests.post(f"http://{os.getenv('HOST_IP')}:5000/cfdFailNotify")

    @staticmethod
    def notify_ready():
        if os.getenv("IN_DOCKER", False):
            requests.post("http://drv_server:5000/cfdDoneNotify")
        else:
            requests.post(f"http://{os.getenv('HOST_IP')}:5000/cfdDoneNotify")

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
        :return: wind vector [x, y, z] or None if data is not ready
        """
        if not self.DEBUG_USE_SAME_DATA and self.state != "ready":
            print("Wind data is not ready")
            return None

        if self.preprocess_mode == "kd_tree":
            return self.foam_kd_tree_reader.get_spacial_temporal_velocity_next_time_step(cartesian_coordinates)
        else:
            return self.foam_csv_reader.get_spacial_temporal_velocity_next_time_step(cartesian_coordinates)


if __name__ == "__main__":
    cfd_manager = CFDManager()
    cfd_manager.openfoam_controller.wisp_save_all_result_and_preprocess()