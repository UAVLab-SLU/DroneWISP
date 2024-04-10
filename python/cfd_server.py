import json

from flask import Flask, request

app = Flask(__name__)

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

    #TODO: read the wind data from the U file
    dummy_wind_data = json.dumps({"wind": [1, 2, 3]})
    return dummy_wind_data


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



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)