from pyfoam_reader import OpenFoamController


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
        self.openfoam_controller = OpenFoamController("openFoamCase")

    def get_state(self):
        return self.state

    def get_wind_vector_from_df(self, cartesian_coordinates):
        pass

    def replace_mesh_with_binary_mask(self, request_json):
        """
        Replace the mesh with the binary mask
        :param request_json: raw json from the request
        structure {'maskData': [{'x': -50, 'y': -50, 'z': 0}, {'x': -50, 'y': -49, 'z': 0}, ...]}
        :return: boolean success or failure
        """

        # json object to list of tuples
        bm_list = [(vertex['x'], vertex['y'], vertex['z']) for vertex in request_json['maskData']]
        return self.openfoam_controller.replace_mesh_with_binary_mask(bm_list)


    def update_openfoam_case(self, request_json):
        """
        Update the openfoam case with the new settings
        :param request_json: raw json from the request
        :return: success or failure
        """
        pass
