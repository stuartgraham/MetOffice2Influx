## Met Office to Influx 
Downloads weather data from Met Office DataHub API (https://metoffice.apiconnect.ibmcloud.com/metoffice/production/) and inserts to InfluxDB

### Requirements
```sh
pip install -p requirements.txt
```

### Execution 
```sh
python3 .\main.py
```

### Docker Compose
```sh 
weatherscraper:
  image: ghcr.io/stuartgraham/metoffice2influx:latest
  restart: always
  container_name: metoffice2influx
  environment:
    - LIVE_CONN=True
    - API_CLIENT=SoMe-GuId
    - API_SECRET=SoMe-PaSsWoRd
    - INFLUX_HOST=influx.test.local
    - INFLUX_HOST_PORT=8086
    - INFLUX_DATABASE=weatherstats
    - LATITUDE=58.642334
    - LONGITUDE=-3.070539
    - RUNMINS=60
```
