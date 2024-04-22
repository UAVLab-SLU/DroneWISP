import json
import struct

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


@app.route('/wind', methods=['POST'])
def wind():
    """
    Read the wind data from the U file
    :returns: wind data
    """
    # get target location from request
    request_json = request.get_json()
    print("request_json:", request_json)

    # dummy coordinates
    cartesian_coordinates = {
        "x": 1,
        "y": 2,
        "z": 3
    }

    # TODO: read wind data from preprocessed df
    dummy_wind_data = json.dumps({"wind": [1, 2, 3]})
    #return dummy_wind_data

    wind_vector = cfd_manager.get_wind_vector_from_df([
        cartesian_coordinates["x"], cartesian_coordinates["y"], cartesian_coordinates["z"]])

    return json.dumps({"wind": wind_vector, "cartesian_coordinates": cartesian_coordinates})


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
    # TODO: return the current openfoam case status
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
    app.run(host='0.0.0.0', port=5001)
