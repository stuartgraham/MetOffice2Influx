# Weather Data Ingestion

This repository contains a Python script for retrieving weather data from the Met Office API and storing it into an InfluxDB database. The script can run in two modes: real-time ingestion mode and cron mode for continuous updating.

## Table of Contents
- [Weather Data Ingestion](#weather-data-ingestion)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Environment Variables](#environment-variables)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Functions](#functions)
  - [Dependencies](#dependencies)
  - [License](#license)

## Features

- **Real-time Data Ingestion:**
  - Fetches live weather data at specified intervals.
  - Validates and processes the data before storing it in InfluxDB.

- **Cron Mode:**
  - Allows the script to run continuously, fetching weather data every specified number of minutes.
  - Throttles API requests based on Met Office guidelines.

## Environment Variables

Ensure the following environment variables are set before running the script:

- `CRON_MODE` (default: `False`): If set to `True`, the script runs in cron mode.
- `API_KEY`: The API key for the Met Office API.
- `INFLUX_HOST`: The hostname of the InfluxDB.
- `INFLUX_HOST_PORT` (default: `8086`): The port of the InfluxDB.
- `INFLUX_BUCKET`: The bucket name in InfluxDB.
- `INFLUX_TOKEN`: The authentication token for InfluxDB.
- `INFLUX_ORG` (default: `"-"`): The organization name in InfluxDB.
- `LATITUDE`: The latitude for the weather data location.
- `LONGITUDE`: The longitude for the weather data location.
- `RUNMINS` (default: `1`): The interval in minutes for fetching live data.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/your-repo-name.git
    cd your-repo-name
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up environment variables in your preferred way (e.g., using a `.env` file or exporting in the shell).

## Usage

Run the script using Python:

```sh
python script_name.py
```

Depending on the environment variables set, the script will either fetch real-time weather data or run in cron mode for continuous updates.

## Functions

- **time_format():** Configures the output format for Icecream logging.
- **get_live_weather_data(api_key, latitude, longitude):** Fetches live weather data from the Met Office API.
- **write_to_influx(data_payload):** Writes data to an InfluxDB instance.
- **organise_weather_data(working_data, testing=False):** Organizes weather data and sends it to InfluxDB in batches.
- **qualify_data(working_data, testing=False):** Validates the payload for errors.
- **calculate_sleep_time(sleep_datetime):** Calculates the sleep time until the next API access window.
- **do_it():** Main function that orchestrates fetching, qualifying, and organizing weather data.
- **main():** Main entry point of the script, handles scheduling and mode selection.

## Dependencies

- `requests`
- `schedule`
- `pendulum`
- `icecream`
- `datetime`
- `influxdb_client`
- `urllib3`

Refer to `requirements.txt` for the exact versions.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

Feel free to customize this `README.md` further according to your needs. Happy coding! 🖥️🚀

---

Feel free to use this content as needed in your `README.md` file.