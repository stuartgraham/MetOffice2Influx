
import os
import sys
import time
import requests
import schedule
import pendulum
from icecream import ic
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError
from urllib3 import Retry

# GLOBALS
CRON_MODE = bool(os.environ.get("CRON_MODE", False))
API_KEY = os.environ.get("API_KEY", False)
INFLUX_HOST = os.environ.get("INFLUX_HOST", "")
INFLUX_HOST_PORT = int(os.environ.get("INFLUX_HOST_PORT", 8086))
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET", "")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN", "")
INFLUX_ORG = os.environ.get("INFLUX_ORG", "-")
LATITUDE = os.environ.get("LATITUDE", "")
LONGITUDE = os.environ.get("LONGITUDE", "")
RUNMINS = int(os.environ.get("RUNMINS", 1))

# Configure Icecream
def time_format():
    return f"{pendulum.now("Europe/London").to_datetime_string()} |> "
ic.configureOutput(prefix=time_format)


# Grabs weather data from authenticate Met Office API
# https://datahub.metoffice.gov.uk/docs/getting-started
def get_live_weather_data(api_key, latitude, longitude):
    url = (
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly"
        f"?excludeParameterMetadata=false&includeLocationName=true&latitude={latitude}&longitude={longitude}"
    )
    headers = {
        "apikey": api_key,
        "accept": "application/json",
    }

    with requests.get(url, headers=headers) as response:
        response_code = response.status_code
        ic(response_code)
        if response.status_code == 200:
            ic("API_HTTP_SUCCESS: Connected to Met Office API successfully")
        else:
            ic("API_HTTP_ERROR: Unable to connect to API")

    ic(response.json())
    return response.json()


# Writes data to InfluxDB
def write_to_influx(data_payload):
    time.sleep(1)
    ic("SUBMIT:" + str(data_payload))
    retries = Retry(connect=5, read=2, redirect=5)
    with InfluxDBClient(f"http://{INFLUX_HOST}:{INFLUX_HOST_PORT}", org=INFLUX_ORG, token=INFLUX_TOKEN, retries=retries) as client:
        try:
            client.write_api(write_options=SYNCHRONOUS).write(INFLUX_BUCKET, INFLUX_ORG, data_payload)
        except InfluxDBError as e:
            if e.response.status == 401:
                raise Exception(f"Insufficient write permissions to {INFLUX_BUCKET}.") from e
            raise
        
    data_points = len(data_payload)
    ic(f"SUCCESS: {data_points} data points written to InfluxDB")
    ic("#"*30)
    client.close()


# Organises weather data from response and sends to Influx in batch
def organise_weather_data(working_data, testing=False):
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
    if not testing:
        write_to_influx(data_points_batch)

    return data_points_batch


# Check the payload for errors
def qualify_data(working_data, testing=False):
    # Check for API throttle error
    if working_data.get("message") == "Message throttled out":
        ic("PAYLOAD_ERROR: API throttle error")
        ic(working_data)
        sleep_time = calculate_sleep_time(working_data["nextAccessTime"])
        ic(f"API_BACKOFF: Sleeping for {sleep_time} seconds")
        if not testing:
            time.sleep(sleep_time)
        return False
    
    # Check for valid weather data
    if working_data.get("features", [{}])[0].get("properties", {}).get("timeSeries") is None:
        ic("PAYLOAD_ERROR: No data points found")
        ic(working_data)
        return False
    else:
        ic("PAYLOAD_VALID: Payload is validate")
        return True


# Calculate the time to sleep
def calculate_sleep_time(sleep_datetime):
    try:
        # Define the format of the input string
        date_format = "%Y-%b-%d %H:%M:%S%z %Z"
        date_obj = datetime.strptime(sleep_datetime, date_format)
        sleep_datetime = pendulum.instance(date_obj)

    except Exception as e:
        ic(f"TIME_PARSE_ERROR: Could parse retry time. Exception: {e}")
        return 300
    
    now = pendulum.now("Europe/London")
    diff = sleep_datetime.diff(now).in_seconds()

    # return 0 if negative
    if diff < 0:
        ic("TIME_DELTA: Less than zero")
        return 0
    else:
        ic(f"TIME_DELTA: set to {diff}")
        return diff


# Main function to run
def do_it():
    working_data = get_live_weather_data(API_KEY, LATITUDE, LONGITUDE)
    continue_processing = qualify_data(working_data)
    if not continue_processing:
        return False
    else:
        organise_weather_data(working_data)


def main():
    # Cron mode runs once and signals an exit code
    if CRON_MODE:
        try:
            print("STARTJOB: Starting job...")
            do_it()
            print("COMPLTEDJOB: Job completed successfully")
            sys.exit(0)
        except Exception as e:
            print(f"EXCEPTION: Job failed with exception: {e}")
            sys.exit(1)

    # Else operate as long running
    else:
        do_it()
        schedule.every(RUNMINS).minutes.do(do_it)

        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    main()
