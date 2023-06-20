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



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)