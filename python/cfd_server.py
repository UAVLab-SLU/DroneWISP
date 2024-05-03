import json
import os
import struct

import requests
from flask import Flask, request
import threading
import socket
import logging
from flask_cors import CORS
from cfd_manager import CFDManager

app = Flask(__name__)
log = logging.getLogger('werkzeug')
#log.setLevel(logging.ERROR)
CORS(app)
# hardcoded for now, use environment variables in production
UE_ADDRESS = "192.168.1.181"
UE_PORT = 8008
DRV_ADDRESS = "192.168.1.181"
DRV_PORT = 5000
MY_INBOUND_UDP_PORT = 3001

cfd_manager = CFDManager()
if os.getenv("IN_DOCKER", False):
    ascii_art = """
 ______        ______  ____    ____   ___   ____ _  _______ ____  
|  _ \ \      / /  _ \/ ___|  |  _ \ / _ \ / ___| |/ / ____|  _ \ 
| |_) \ \ /\ / /| | | \___ \  | | | | | | | |   | ' /|  _| | |_) |
|  _ < \ V  V / | |_| |___) | | |_| | |_| | |___| . \| |___|  _ < 
|_| \_\ \_/\_/  |____/|____/  |____/ \___/ \____|_|\_\_____|_| \_\ 
"""
else:
    ascii_art = """
______        ______  ____  
|  _ \ \      / /  _ \/ ___| 
| |_) \ \ /\ / /| | | \___ \ 
|  _ < \ V  V / | |_| |___) |
|_| \_\ \_/\_/  |____/|____/ 
"""
print(ascii_art)


@app.route('/')
def hello():
    return 'Hello, WSL CFD Server!'


@app.route('/wind', methods=['GET'])
def wind():
    """
    Read the wind data from the U file
    :returns: wind data
    """
    # get target location from request
    request_json = request.get_json()
    # Structure check
    if not all(key in request_json for key in ["x", "y", "z"]):
        print("Missing keys in request")
        return json.dumps({"x": 0, "y": 0, "z": 0})

    # check if coordinates are float or int
    if not all(isinstance(i, (int, float)) for i in [request_json["x"], request_json["y"], request_json["z"]]):
        print("Coordinates are not int or float")
        return json.dumps({"x": 0, "y": 0, "z": 0})

    cartesian_coordinates = [request_json["x"], request_json["y"], request_json["z"]]

    #print("cartesian_coordinates:", cartesian_coordinates)

    wind_vector = cfd_manager.get_wind_vector_from_df(cartesian_coordinates)
    if wind_vector is None:
        print("Wind does not exist")
        return json.dumps({"x": 0, "y": 0, "z": 0})

    if not isinstance(wind_vector[0], (int, float)) or not isinstance(wind_vector[1], (int, float)) or not isinstance(
            wind_vector[2], (int, float)):
        print("Coordinates are not int or float")
        return json.dumps({"x": 0, "y": 0, "z": 0})

    return json.dumps({"x": wind_vector[0], "y": wind_vector[1], "z": wind_vector[2]})


@app.route('/openfoam', methods=['POST'])
def configure_openfoam_case():
    """
    Configure the OpenFOAM case, request is json containing all the necessary data
    :returns: success message, ready to run the simulation, does not start the simulation, wait for the binary mask
    """
    # get boundary vertices from request
    request_json = request.get_json()
    print("request_json:", request_json)
    if cfd_manager.update_openfoam_case(request_json):
        return json.dumps({"status": "success"})
    else:
        return json.dumps({"status": "error"})


@app.route('/cfd', methods=['GET'])
def cfd_status():
    """
    Check the status of the CFD simulation
    :returns: status of the CFD simulation [running, completed, idle]
    """
    state = cfd_manager.get_state()
    return json.dumps({"state": state})


@app.route('/bm', methods=['POST'])
def binary_mask():
    """
    Receive the binary mask from the UE side
    :returns: success message
    """
    # get binary mask from request
    request_json = request.get_json()
    if cfd_manager.replace_mesh_with_binary_mask(request_json):
        return json.dumps({"status": "success"})
    else:
        print("Error replacing mesh with binary mask")
        return json.dumps({"status": "error"})


if __name__ == '__main__':
    # Start the UDP server in a new thread
    # quick check on drv server rest api, see if we can access it
    try:
        if os.environ.get("IN_DOCKER", False):
            response = requests.get(f"http://drv_server:5000/state", timeout=1)
        else:
            response = requests.get(f"http://192.168.1.181:5000/state", timeout=1)
        if response.status_code == 200:
            print("Connected to DRV server")
        else:
            print("Error connecting to DRV server")
    except requests.exceptions.RequestException as e:
        print("Error connecting to DRV server:", e)

    app.run(host='0.0.0.0', port=5001)
