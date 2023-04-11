import json
import os
import time

import requests
import schedule
from icecream import ic
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

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
    INFLUX_CLIENT = InfluxDBClient(
        host=INFLUX_HOST, port=INFLUX_HOST_PORT, database=INFLUX_DATABASE
        )

elif INFLUX_VERSION == 2: 
    INFLUX_CLIENT = InfluxDBClient(
        url=f"http://{INFLUX_HOST}:{INFLUX_HOST_PORT}", org=INFLUX_ORG, token=INFLUX_TOKEN
        )
    INFLUX_WRITE_API = INFLUX_CLIENT.write_api(write_options=SYNCHRONOUS)

JSON_OUTPUT = "output.json"


# Get saved json from MET
def get_json(client_id, secret):
    url = (
        "https://api-metoffice.apiconnect.ibmcloud.com/v0/forecasts/point/hourly"
        f"?excludeParameterMetadata=false&includeLocationName=true&latitude={LATITUDE}&longitude={LONGITUDE}"
    )
    headers = {
        "X-IBM-Client-Id": client_id,
        "X-IBM-Client-Secret": secret,
        "accept": "application/json",
    }
    resp = requests.get(url, headers=headers)
    payload_data = resp.json()
    with open(JSON_OUTPUT, "w") as outfile:
        json.dump(payload_data, outfile)


def get_saved_data(*args):
    if LIVE_CONN == True:
        get_json(API_CLIENT, API_SECRET)

    with open(JSON_OUTPUT) as json_file:
        working_data = json.load(json_file)
    return working_data


def write_to_influx(data_payload):
    ic(data_payload)
    if INFLUX_VERSION == 1:
        INFLUX_CLIENT.write_points(data_payload) 
    elif INFLUX_VERSION == 2:
        INFLUX_WRITE_API.write(INFLUX_BUCKET, INFLUX_ORG, data_payload)


def sort_json(working_data):
    # Interate over weather payload and pull out data points
    data_points = working_data["features"][0]["properties"]["timeSeries"]
    for data_point in data_points:
        # Cleans up for influxDB insert
        base_dict = {"measurement": "met_weather", "tags": {"name": "met_weather"}}
        time_stamp = data_point["time"]
        base_dict.update({"time": time_stamp})
        del data_point["time"]

        # Make everything float to stop insert errors
        for k, v in data_point.items():
            if type(v) == int:
                data_point.update({k: float(v)})

        base_dict.update({"fields": data_point})

        # Construct payload and insert
        write_to_influx(base_dict)


def do_it():
    working_data = get_saved_data()
    sort_json(working_data)


def main():
    """Main entry point of the app"""
    do_it()
    schedule.every(RUNMINS).minutes.do(do_it)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    """This is executed when run from the command line"""
    main()
