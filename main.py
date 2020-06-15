
import json
import time
import os
from influxdb import InfluxDBClient
import schedule
import requests

# # .ENV FILE FOR TESTING
# if os.path.exists('.env'):
#     from dotenv import load_dotenv
#     load_dotenv()

# GLOBALS
LIVE_CONN = bool(os.environ.get('LIVE_CONN',''))
API_CLIENT = os.environ.get('API_CLIENT','')
API_SECRET = os.environ.get('API_SECRET','')
INFLUX_HOST = os.environ.get('INFLUX_HOST','')
INFLUX_HOST_PORT = int(os.environ.get('INFLUX_HOST_PORT',''))
INFLUX_DATABASE = os.environ.get('INFLUX_DATABASE','')
LATITUDE = os.environ.get('LATITUDE','')
LONGITUDE = os.environ.get('LONGITUDE','')
RUNMINS =  int(os.environ.get('RUNMINS',1))

INFLUX_CLIENT = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_HOST_PORT, database=INFLUX_DATABASE)
JSON_OUTPUT = 'output.json'

# Get saved json from MET
def get_json(client_id, secret):
    url = 'https://api-metoffice.apiconnect.ibmcloud.com/metoffice/production/v0/forecasts/point/hourly?excludeParameterMetadata=false&includeLocationName=true&latitude={}&longitude={}'.format(LATITUDE, LONGITUDE)
    headers = {
        'x-ibm-client-id': client_id,
        'x-ibm-client-secret': secret,
        'accept': 'application/json'
        }
    resp = requests.get(url, headers=headers)
    payload_data = resp.json()
    print(payload_data)
    with open(JSON_OUTPUT, 'w') as outfile:
        json.dump(payload_data, outfile)


def get_saved_data(*args):
    if LIVE_CONN == True:
        get_json(API_CLIENT, API_SECRET)

    with open(JSON_OUTPUT) as json_file:
        working_data = json.load(json_file)
    return working_data

def write_to_influx(data_payload):
    INFLUX_CLIENT.write_points(data_payload)
    pass    

def sort_json(working_data):
    # Interate over weather payload and pull out data points
    data_points = working_data['features'][0]['properties']['timeSeries']
    for data_point in data_points:
        # Cleans up for influxDB insert
        base_dict = {'measurement' : 'met_weather', 'tags' : {'name': 'met_weather'}}
        time_stamp = data_point['time']
        base_dict.update({'time': time_stamp})
        del data_point['time']
        
        # Make everything float to stop insert errors
        for k,v in data_point.items():
            if type(v) == int:
                data_point.update({k : float(v)})

        base_dict.update({'fields' : data_point})

        # Construct payload and insert
        data_payload = [base_dict]
        print("SUBMIT:" + str(data_payload))
        print('#'*30) 
        write_to_influx(data_payload)


def do_it():
    working_data = get_saved_data()
    sort_json(working_data)

def main():
    ''' Main entry point of the app '''
    do_it()
    schedule.every(RUNMINS).minutes.do(do_it)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    ''' This is executed when run from the command line '''
    main()