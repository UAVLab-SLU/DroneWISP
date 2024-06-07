import requests
import time

post_url = 'http://localhost:5001/wind'
get_url = 'http://localhost:5001/'
def measure_delay_post():
    start_time = time.time()

    # Create the JSON data to send in the POST request
    data = {'x': 1, 'y': 2, 'z': 3}

    # Send the POST request with JSON data
    response = requests.post(post_url, json=data)

    end_time = time.time()
    delay = end_time - start_time
    return delay

def measure_delay_get():
    start_time = time.time()

    # Send the GET request
    response = requests.get(get_url)

    end_time = time.time()
    delay = end_time - start_time
    return delay

if __name__ == '__main__':
    delay = measure_delay_post()
    print(f"POST Delay: {delay} seconds")
    delay = measure_delay_get()
    print(f"GET Delay: {delay} seconds")
