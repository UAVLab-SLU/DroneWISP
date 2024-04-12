import json

from flask import Flask, request
import threading
import socket
import logging
from flask_cors import CORS
from python.cfd_manager import CFDManager

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
CORS(app)
# hardcoded for now, use environment variables in production
UE_ADDRESS = "192.168.1.181"
UE_PORT = 8008
DRV_ADDRESS = "192.168.1.181"
DRV_PORT = 5000
MY_INBOUND_UDP_PORT = 3001

manager = CFDManager()
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

    # TODO: read the wind data from the U file
    dummy_wind_data = json.dumps({"wind": [1, 2, 3]})
    return dummy_wind_data


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

    print("request_json:", request_json)
    json_data = json.dumps(data)
    # send the LLA data to the UE side UDP port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json_data.encode(), (UE_ADDRESS, UE_PORT))


@app.route('/openfoam', methods=['POST'])
def configure_openfoam_case():
    """
    Configure the OpenFOAM case
    input: wind speed, wind direction, wind type
    :returns: success message, ready to run the simulation, does not start the simulation, wait for the binary mask
    """
    # get boundary vertices from request
    request_json = request.get_json()
    print("request_json:", request_json)
    # TODO: update the openfoam case with the wind data


@app.route('/mesh', methods=['POST'])
def setup_mesh_using_binary_mask():
    """
    Setup the mesh using the binary mask
    :returns: success message, ready to run the simulation
    """
    # get binary mask from request
    request_json = request.get_json()
    print("request_json:", request_json)
    # TODO: setup the mesh using the binary mask


@app.route('/cfd', methods=['GET'])
def cfd_status():
    """
    Check the status of the CFD simulation
    :returns: status of the CFD simulation [running, completed, idle]
    """
    # TODO: return the current openfoam case status
    state = manager.get_state()
    return json.dumps({"state": state})


def udp_server():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    server_address = ('', 3001)
    sock.bind(server_address)
    print("UDP server listening on port 3001")

    while True:
        data, address = sock.recvfrom(4096)
        # TODO: geometry Binary mask from UE
        # 1. check current state of CFD simulation
        # 2. if idle, then convert the binary mask to stl and save to the openfoam case

        print("Hello")


if __name__ == '__main__':
    # Start the UDP server in a new thread
    udp_thread = threading.Thread(target=udp_server)
    udp_thread.start()
    app.run(host='0.0.0.0', port=5001)
