# Communicate with DRV and WISP server, and gather data for PINN
import random
import time
import requests

from pyfoam_reader import OpenFoamController

DRV_IP = "192.168.1.181:5000"
WISP_IP = "127.0.0.1:5001"

my_fav = {"latitude":41.885799407958984,"longitude":-87.624099731445312}
openfoam_controller = OpenFoamController("openFoamCase")

min_x = -25
max_x = 25
min_y = -25
max_y = 25
min_z = 0
max_z = 10

def scan_terrain(gps_coord):
    # get request to DRV server
    requests.post(f"http://{DRV_IP}/cesiumCoordinate", json=gps_coord)

    requests.get(f"http://{DRV_IP}/scan")

    # wait for the scan to complete
    while True:
        time.sleep(0.3)
        response = requests.get(f"http://{DRV_IP}/state")
        if response.json()["state"] != "scan":
            break
    print("Scan completed")

def run_cfd(wind_x, wind_y,
            x_length=25, y_length=25, z_length=10,
            x_min=-25, x_max=25,
            y_min=-25, y_max=25,
            z_min=-5, z_max=20,
            dt=1, end_time=51, write_interval=50):
    # send configuration to WISP server



    json_request = dict(wind_speed_x=-wind_x, wind_speed_y=wind_y, wind_speed_z=0, wind_type='uniform',
                        x_length=x_length, y_length=y_length, z_length=z_length,
                        dt=dt, end_time=end_time, write_interval=write_interval,
                        v1={'x': x_min, 'y': y_min, 'z': z_min},
                        v2={'x': x_max, 'y': y_min, 'z': z_min},
                        v3={'x': x_max, 'y': y_max, 'z': z_min},
                        v4={'x': x_min, 'y': y_max, 'z': z_min},
                        v5={'x': x_min, 'y': y_min, 'z': z_max},
                        v6={'x': x_max, 'y': y_min, 'z': z_max},
                        v7={'x': x_max, 'y': y_max, 'z': z_max},
                        v8={'x': x_min, 'y': y_max, 'z': z_max})

    requests.post(f"http://{WISP_IP}/openfoam", json=json_request)

    # wait for the CFD simulation to complete
    print("Waiting for CFD simulation to complete")
    while True:
        time.sleep(0.3)
        response = requests.get(f"http://{WISP_IP}/cfd")
        #print(response.json())
        if response.json()["state"] == "ready":
            print("CFD simulation completed")
            return True
        elif response.json()["state"] == "cfd_fail":
            print("Error in CFD simulation")
            return False



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

    report_csv = open("report_conti.csv", "w")
    report_csv.write("time_length, time\n")

    size_range= dict(x_length=25, y_length=25, z_length=10)

    time_len_range = [1,10,50,100,200]


    success_count = 0
    for t in time_len_range:
        print(f"Running CFD simulation for {size_range['x_length']}x{size_range['y_length']}x{size_range['z_length']}")
        wind_x, wind_y = generate_random_wind()
        gps_loc = my_fav

        start_time = time.time()
        scan_terrain(gps_loc)
        if run_cfd(wind_x, wind_y, size_range["x_length"], size_range["y_length"], size_range["z_length"],
                   dt=1, end_time=t, write_interval=1):
            success_count += 1
            # append to report
            time_len = t
            report_csv.write(f"{t}, {time.time()-start_time}\n")
        else:
            print("Error in CFD simulation")


    report_csv.close()
    print("All done")
