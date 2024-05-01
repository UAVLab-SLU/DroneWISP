import time
from python.cfd_manager import CFDManager

cfd_manager = CFDManager()
assert cfd_manager.get_state() == "idle"

# replace mesh, but here we just make it ready
cfd_manager.stl_mesh_ready = True

# update openfoam case
request_json = {'wind_speed_x': -10,
                'wind_speed_y': -5,
                'wind_speed_z': 0,
                'wind_type': 'uniform',
                'x_length': 50,
                'y_length': 50,
                'z_length': 25,
                'v1': {'x': -50, 'y': -50, 'z': -5},
                'v2': {'x': 50, 'y': -50, 'z': -5},
                'v3': {'x': 50, 'y': 50, 'z': -5},
                'v4': {'x': -50, 'y': 50, 'z': -5},
                'v5': {'x': -50, 'y': -50, 'z': 20},
                'v6': {'x': 50, 'y': -50, 'z': 20},
                'v7': {'x': 50, 'y': 50, 'z': 20},
                'v8': {'x': -50, 'y': 50, 'z': 20}}
cfd_manager.update_openfoam_case(request_json)

time_start = time.time()

# at this point, RWDS should be running
assert cfd_manager.get_state() == "cfd_running"

# wait for the simulation to finish
while cfd_manager.get_state() == "cfd_running":
    pass

assert cfd_manager.get_state() == "ready"
print("Time taken for simulation: ", time.time() - time_start)

# get wind
time_start = time.time()
print(cfd_manager.get_wind_vector_from_df([0, 0, 0]))
print("Time taken for wind query: ", time.time() - time_start)
time_start = time.time()
print(cfd_manager.get_wind_vector_from_df([10, 2, 10]))
print("Time taken for wind query: ", time.time() - time_start)
time_start = time.time()
print(cfd_manager.get_wind_vector_from_df([1.01, 0.2, 10.0]))
print("Time taken for wind query: ", time.time() - time_start)


