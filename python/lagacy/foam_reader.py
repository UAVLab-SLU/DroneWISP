# Purpose: Utility Class to read OpenFOAM data that is later used for server-client communication architecture
# currently only the abstraction, no implementation
import Ofpp

class FoamReader:
    root_path = os.path

    mesh_path = None
    data_path = None
    boundary_path = None

    start_time = None
    end_time = None
    time_step = None

    def __init__(self):
        pass

    def read(self, path):
        """
        Read OpenFOAM data from path
        :param path: root path of OpenFOAM run case
        :return: "mesh", "data", "boundary"
        """
        pass

    def read_mesh(self, path):
        pass

    def read_data(self, path):
        pass

    def read_boundary(self, path):
        pass
