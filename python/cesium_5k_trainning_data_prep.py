# Communicate with DRV and WISP server, and gather data for PINN
import os.path
import random
import time
import hashlib

import requests
import vtk

from pyfoam_reader import OpenFoamController

DRV_IP = "192.168.1.181:5000"
WISP_IP = "127.0.0.1:5001"

my_fav = {"latitude":41.885799407958984,"longitude":-87.624099731445312}
openfoam_controller = OpenFoamController("openFoamCase")
lat_max = 41.886817
lat_min = 41.878162
long_max = -87.624490
long_min = -87.636632

min_x = -25
max_x = 25
min_y = -25
max_y = 25
min_z = 0
max_z = 10

sample_points = 2

# generate random GPS coordinates uniformly distributed in the area
def generate_random_gps():
    lat = random.uniform(lat_min, lat_max)
    long = random.uniform(long_min, long_max)
    print(f"GPS offset: ({lat-lat_min}, {long-long_min})") # offset from the bottom left corner of the area)
    return {"latitude": lat, "longitude": long}

def scan_terrain(gps_coord):
    # get request to DRV server
    requests.post(f"http://{DRV_IP}/cesiumCoordinate", json=gps_coord)

    requests.get(f"http://{DRV_IP}/scan")

    # wait for the scan to complete
    while True:
        time.sleep(3)
        response = requests.get(f"http://{DRV_IP}/state")
        if response.json()["state"] != "scan":
            break
    print("Scan completed")

def run_cfd(wind_x, wind_y):
    # send configuration to WISP server



    json_request = dict(wind_speed_x=-wind_x, wind_speed_y=wind_y, wind_speed_z=0, wind_type='uniform',
                        x_length=50, y_length=50, z_length=10,
                        v1={'x': -25, 'y': -25, 'z': 0},
                        v2={'x': 25, 'y': -25, 'z': 0},
                        v3={'x': 25, 'y': 25, 'z': 0},
                        v4={'x': -25, 'y': 25, 'z': 0},
                        v5={'x': -25, 'y': -25, 'z': 10},
                        v6={'x': 25, 'y': -25, 'z': 10},
                        v7={'x': 25, 'y': 25, 'z': 10},
                        v8={'x': -25, 'y': 25, 'z': 10})

    requests.post(f"http://{WISP_IP}/openfoam", json=json_request)

    # wait for the CFD simulation to complete
    print("Waiting for CFD simulation to complete")
    while True:
        time.sleep(3)
        response = requests.get(f"http://{WISP_IP}/cfd")
        if response.json()["state"] == "ready":
            print("CFD simulation completed")
            return True
        elif response.json()["state"] == "cfd_fail" or response.json()["state"] == "idle":
            print("Error in CFD simulation")
            return False


def calculate_file_hash(filepath):
    hash_obj = hashlib.sha256()
    with open(filepath, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def convert_stl_to_vtk(stl_file_path, output_dir, vtk_file_name):
    stl_reader = vtk.vtkSTLReader()
    stl_reader.SetFileName(stl_file_path)
    stl_reader.Update()
    # Convert to polydata
    polydata = vtk.vtkPolyData()
    polydata.ShallowCopy(stl_reader.GetOutput())

    vtk_writer = vtk.vtkDataSetWriter()
    vtk_writer.SetInputData(polydata)
    vtk_writer.SetFileName(os.path.join(output_dir, vtk_file_name))
    vtk_writer.Write()



def gather_data(wind_x, wind_y):
    mesh_file = os.path.join("openFoamCase", "constant", "geometry", "combined.stl")
    mesh_hash = calculate_file_hash(mesh_file)
    dir_name = os.path.join("pinn", "cesium5kTrain", f"{mesh_hash}_{wind_x}_{wind_y}")


    # check if the data already exists
    if os.path.exists(dir_name):
        print("Data already exists")
    else:
        os.makedirs(dir_name, exist_ok=True)

        # convert the mesh to VTK format
        convert_stl_to_vtk(mesh_file, dir_name, "combined.vtk")

    print("Gathering data")
    openfoam_controller.pinn_save_all_result_and_preprocess(range_x=50 , range_y=50, range_z=10,
                                                             x_min=-25, y_min=-25, z_min=0,
                                                             x_max=25, y_max=25, z_max=10,
                                                             data_dir=dir_name)


def generate_random_wind(mag_min=10, mag_max=20):
    # Helper function to get a random wind speed in the specified ranges
    def get_wind_speed():
        if random.choice([True, False]):
            return random.randint(-mag_max, -mag_min)
        else:
            return random.randint(mag_min, mag_max)
    wind_x = get_wind_speed()
    wind_y = get_wind_speed()

    print(f"Wind speed: ({wind_x}, {wind_y})")
    return wind_x, wind_y


if __name__ == '__main__':

    for i in range(sample_points):
        print("Set ", i)
        wind_x, wind_y = generate_random_wind()
        gps_loc = generate_random_gps()
        scan_terrain(gps_loc)
        run_cfd(wind_x, wind_y)
        gather_data(wind_x, wind_y)
