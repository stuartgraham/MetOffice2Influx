## Met Office to Influx 
Downloads hourly weather data from Met Office DataHub API (https://metoffice.apiconnect.ibmcloud.com/metoffice/production/) based on longitude and latitude and inserts to InfluxDB.
Supports v1.8 and v2.

### Requirements
```sh
pip install -p requirements.txt
```

### Execution 
```sh
python3 .\main.py
```

### Docker Compose - Influx v1.8 Support
```sh 
metoffice2influx:
  image: ghcr.io/stuartgraham/metoffice2influx:latest
  restart: always
  container_name: metoffice2influx
  environment:
    - INFLUX_VERSION=1
    - LIVE_CONN=True
    - API_CLIENT=SoMe-GuId
    - API_SECRET=SoMe-PaSsWoRd
    - INFLUX_HOST=influx.test.local
    - INFLUX_HOST_PORT=8086
    - INFLUX_DATABASE=weatherstats
    - LATITUDE=58.642334
    - LONGITUDE=-3.070539
    - RUNMINS=60
    - LOGGING=False
```

### Docker Compose - Influx v2 Support
```sh 
metoffice2influx:
  image: ghcr.io/stuartgraham/metoffice2influx:latest
  restart: always
  container_name: metoffice2influx
  environment:
    - INFLUX_VERSION=2
    - LIVE_CONN=True
    - API_CLIENT=SoMe-GuId
    - API_SECRET=SoMe-PaSsWoRd
    - INFLUX_HOST=influx.test.local
    - INFLUX_HOST_PORT=8086
    - INFLUX_TOKEN=SoMe-token
    - INFLUX_ORG=InfluxOrg
    - INFLUX_BUCKET=WeatherBucket
    - LATITUDE=58.642334
    - LONGITUDE=-3.070539
    - RUNMINS=60
    - LOGGING=False
```
