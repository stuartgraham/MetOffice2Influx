import os
import time
import requests
import schedule
import pendulum
from icecream import ic
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError
from urllib3 import Retry

# GLOBALS
INFLUX_VERSION = int(os.environ.get("INFLUX_VERSION", 2))
API_KEY = os.environ.get("API_KEY", "")
INFLUX_HOST = os.environ.get("INFLUX_HOST", "")
INFLUX_HOST_PORT = int(os.environ.get("INFLUX_HOST_PORT", ""))
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET", "")``
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN", "")
INFLUX_ORG = os.environ.get("INFLUX_ORG", "-")
LATITUDE = os.environ.get("LATITUDE", "")
LONGITUDE = os.environ.get("LONGITUDE", "")
RUNMINS = int(os.environ.get("RUNMINS", 1))
LOGGING = bool(os.environ.get("LOGGING", False))

# Logging
if not LOGGING:
    ic.disable()


# Grabs weather data from authenticate Met Office API
# https://datahub.metoffice.gov.uk/docs/getting-started
def get_live_weather_data(api_key, latitude, longitude):
    return_data = {}
    
    url = (
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly"
        f"?excludeParameterMetadata=false&includeLocationName=true&latitude={latitude}&longitude={longitude}"
    )
    headers = {
        "apikey": api_key,
        "accept": "application/json",
    }
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        print(f"EXCEPTION: {e}")
        return return_data
    
    return_data = response.json()
    
    return return_data


def write_to_influx(data_payload):
    time.sleep(1)
    print("SUBMIT:" + str(data_payload))
    retries = Retry(connect=5, read=2, redirect=5)
    with InfluxDBClient(f"http://{INFLUX_HOST}:{INFLUX_HOST_PORT}", org=INFLUX_ORG, token=INFLUX_TOKEN, retries=retries) as client:
        try:
            client.write_api(write_options=SYNCHRONOUS).write(INFLUX_BUCKET, INFLUX_ORG, data_payload)
        except InfluxDBError as e:
            if e.response.status == 401:
                raise Exception(f"Insufficient write permissions to {INFLUX_BUCKET}.") from e
            raise
        
    data_points = len(data_payload)
    print(f"SUCCESS: {data_points} data points written to InfluxDB")
    print('#'*30)
    client.close()


# Organises weather data from response and sends to Influx in batch
def organise_weather_data(working_data):
    # Create an array to hold the data points
    data_points_batch = []

    data_points = working_data["features"][0]["properties"]["timeSeries"]
    for data_point in data_points:
        # Clean up for InfluxDB insert
        time_stamp = data_point["time"]
        del data_point["time"]

        # Make everything float to stop insert errors
        for k, v in data_point.items():
            if type(v) == int:
                data_point.update({k: float(v)})

        # Construct a Point object and append to the batch
        point = Point("met_weather").tag("name", "met_weather").time(time_stamp)

        # Add fields to the point
        for k, v in data_point.items():
            point = point.field(k, v)
        
        data_points_batch.append(point)

    # Write the batch to InfluxDB
    write_to_influx(data_points_batch)


def qualify_data(working_data):
    # Check for API throttle error
    if working_data["message"] == "Message throttled out":
        print("PAYLOAD_ERROR: API throttle error")
        print(working_data)
        sleep_time = calculate_sleep_time(working_data["nextAccessTime"])
        print(f"API_BACKOFF: Sleeping for {sleep_time} seconds")
        time.sleep(sleep_time)
        return False
    
    # Check for valid weather data
    if not working_data["features"][0]["properties"]["timeSeries"]:
        print("PAYLOAD_ERROR: No data points found")
        print(working_data)
        return False

    print("PAYLOAD_VALID: Payload is validate")
    return True

def calculate_sleep_time(sleep_datetime):
    # Calculate sleep time
    now = pendulum.now()
    sleep_datetime = pendulum.parse(sleep_datetime)
    diff = sleep_datetime.diff(now).in_seconds()
    # return 0 if negative
    if diff < 0:
        return 0
    else:
        return diff


def do_it():
    working_data = get_live_weather_data(API_KEY, LATITUDE, LONGITUDE)
    continue_processing = qualify_data(working_data)
    if not continue_processing:
        return False
    else:
        organise_weather_data(working_data)


def main():
    do_it()
    schedule.every(RUNMINS).minutes.do(do_it)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
