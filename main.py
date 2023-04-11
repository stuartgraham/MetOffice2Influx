import json
import os
import time

import requests
import schedule
from icecream import ic

# GLOBALS
INFLUX_VERSION = int(os.environ.get("INFLUX_VERSION", 2))
LIVE_CONN = bool(os.environ.get("LIVE_CONN", ""))
API_CLIENT = os.environ.get("API_CLIENT", "")
API_SECRET = os.environ.get("API_SECRET", "")
INFLUX_HOST = os.environ.get("INFLUX_HOST", "")
INFLUX_HOST_PORT = int(os.environ.get("INFLUX_HOST_PORT", ""))
INFLUX_DATABASE = os.environ.get("INFLUX_DATABASE","")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN", "")
INFLUX_ORG = os.environ.get("INFLUX_ORG", "")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET", "")
LATITUDE = os.environ.get("LATITUDE", "")
LONGITUDE = os.environ.get("LONGITUDE", "")
RUNMINS = int(os.environ.get("RUNMINS", 1))
LOGGING = bool(os.environ.get("LOGGING", False))

if not LOGGING:
    ic.disable()

if INFLUX_VERSION == 1:
    from influxdb import InfluxDBClient
    INFLUX_CLIENT = InfluxDBClient(
        host=INFLUX_HOST, port=INFLUX_HOST_PORT, database=INFLUX_DATABASE
        )

elif INFLUX_VERSION == 2: 
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUX_CLIENT = InfluxDBClient(
        url=f"http://{INFLUX_HOST}:{INFLUX_HOST_PORT}", org=INFLUX_ORG, token=INFLUX_TOKEN
        )
    INFLUX_WRITE_API = INFLUX_CLIENT.write_api(write_options=SYNCHRONOUS)

JSON_OUTPUT = "output.json"


# Grabs weather data from authenticate Met Office API
# https://metoffice.apiconnect.ibmcloud.com/metoffice/production/
def get_live_weather_data(client_id, secret):
    url = (
        "https://api-metoffice.apiconnect.ibmcloud.com/v0/forecasts/point/hourly"
        f"?excludeParameterMetadata=false&includeLocationName=true&latitude={LATITUDE}&longitude={LONGITUDE}"
    )
    headers = {
        "X-IBM-Client-Id": client_id,
        "X-IBM-Client-Secret": secret,
        "accept": "application/json",
    }
    response = requests.get(url, headers=headers)
    payload_data = response.json()
    with open(JSON_OUTPUT, "w") as outfile:
        json.dump(payload_data, outfile)


# Verifies if we are using LIVE_CONN to spare API bombardment, or if no local json exists
# Opens weather data from local file 
def load_weather_data():
    if LIVE_CONN or not os.path.exists(JSON_OUTPUT):
        get_live_weather_data(API_CLIENT, API_SECRET)

    with open(JSON_OUTPUT) as json_file:
        working_data = json.load(json_file)
    return working_data


# Determines client type and formats write correctly
def write_to_influx(data_payload):
    ic(data_payload)
    if INFLUX_VERSION == 1:
        response = INFLUX_CLIENT.write_points([data_payload]) 
        success = response
    elif INFLUX_VERSION == 2:
        response = INFLUX_WRITE_API.write(INFLUX_BUCKET, INFLUX_ORG, data_payload)
        success = response is None  # In InfluxDB 2.x, a successful write returns None

    if not success:
        if LOGGING:
            ic("Error writing to InfluxDB:", response)


# Organises weather data from response and sends to Influx
def organise_weather_data(working_data):
    # Iterate over weather payload and pull out data points
    data_points = working_data["features"][0]["properties"]["timeSeries"]
    for data_point in data_points:
        # Clean up for InfluxDB insert
        time_stamp = data_point["time"]
        del data_point["time"]

        # Make everything float to stop insert errors (original logic)
        for k, v in data_point.items():
            if type(v) == int:
                data_point.update({k: float(v)})

        # Construct payload and insert
        data_payload = {
            "measurement": "met_weather",
            "tags": {"name": "met_weather"},
            "time": time_stamp,
            "fields": data_point,
        }
        write_to_influx(data_payload)


def do_it():
    working_data = load_weather_data()
    organise_weather_data(working_data)


def main():
    do_it()
    schedule.every(RUNMINS).minutes.do(do_it)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
