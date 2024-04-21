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

    wind_vector = cfd_manager.get_wind_vector_from_df(cartesian_coordinates)

    return json.dumps({"wind": wind_vector, "cartesian_coordinates": cartesian_coordinates})



@app.route('/lla', methods=['POST'])
def lla():
    """
    Propagate the LLA data to the UE side UDP port
    :return:
    """
    # get LLA data from request
    request_json = request.get_json()
    # expected format:
    data = {
        "latitude": 41.885777,
        "longitude": -87.624166,
        "scan_x_min": -50,  # all in meters
        "scan_x_max": 50,
        "scan_y_min": -50,
        "scan_y_max": 50,
        "scan_z_min": -5,
        "scan_z_max": 20,
        "scan_step": 1,
        "from_port": MY_INBOUND_UDP_PORT  # DRV will not send this, add it on our side
    }

    # verify the request format
    if not all(key in request_json for key in data.keys()):
        return json.dumps({"status": "error", "message": "invalid request format"})
    else:
        data = request_json

    print("request_json:", request_json)
    json_data = json.dumps(data)
    # send the LLA data to the UE side UDP port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json_data.encode(), (UE_ADDRESS, UE_PORT))

    return json.dumps({"status": "success"})


@app.route('/openfoam', methods=['POST'])
def configure_openfoam_case():
    """
    Configure the OpenFOAM case, request is json containing all the necessary data
    :returns: success message, ready to run the simulation, does not start the simulation, wait for the binary mask
    """
    # get boundary vertices from request
    request_json = request.get_json()
    print("request_json:", request_json)
    # TODO: update the openfoam case with the wind data
    cfd_manager.update_openfoam_case(request_json)


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
