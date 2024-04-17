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
        self.state = "idle"
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

        # json object to list of tuples
        bm_list = [(vertex['x'], vertex['y'], vertex['z']) for vertex in request_json['maskData']]
        replace_success = self.openfoam_controller.replace_mesh_with_binary_mask(bm_list)
        if replace_success:
            self.stl_mesh_ready = True
            if self.openfoam_case_ready and self.stl_mesh_ready:
                self.run_simulation()
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

        self.openfoam_controller.update_vertices(list_vertex)
        self.openfoam_controller.update_dimension(request_json['x_length'] * 2 + 1, request_json['y_length'] * 2 + 1,
                                                  request_json['z_length'])
        self.openfoam_controller.update_wind(request_json['wind_speed_x'], request_json['wind_speed_y'],
                                             request_json['wind_speed_z'], request_json['wind_type'])

        self.openfoam_case_ready = True
        if self.openfoam_case_ready and self.stl_mesh_ready:
            self.run_simulation()
        return True

    def run_simulation(self):
        """
        Run the simulation on separate thread, and prepare the results
        """

        # Define a target function for the thread
        def target_function():
            self.state = "cfd_running"
            self.openfoam_controller.run()
            self.state = "ready"  # Set self.state to "ready" after the thread completes

        simulation_thread = threading.Thread(target=target_function)
        simulation_thread.start()

    def clean_simulation(self):
        """
        Clean the simulation, on current thread
        """

        self.stl_mesh_ready = False
        self.openfoam_case_ready = False
        self.openfoam_controller.clean()

    def get_wind_at_cartesian(self, cartesian_coordinates):
        pass
