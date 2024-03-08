from datetime import datetime, date
from collections import namedtuple
import os
import logging
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.wait import wait_fixed
from tenacity.stop import stop_after_attempt

# type alias
csv_row = "list[str]"
csv_rows = "list[csv_row]"

# constants
CITIES = {"london": 2643743,
          "madrid": 3117735,
          "saopaulo": 3448439,
          "sydney": 2147714,
          "newyork": 5128581,
          "moscow": 524901,
          "tokyo": 1850147,
          "nairobi": 184745,
          "asuncion": 3439389,
          "lagos": 2332459}

# openweathermap provides an endpoint to get a city's geo coordinates
# https://api.openweathermap.org/geo/1.0/direct?q=London,GB&limit=5&appid=YOUR_API_KEY
CityParams = namedtuple('CityParams', 'city_name lat lon tz_offset')
CITY_PARAMS = {'london': CityParams('london', 51.5073219, -0.1276474, 0),
               'madrid': CityParams('madrid', 40.4167047, -3.7035825, 1),
               'saopaulo': CityParams('saopaulo', -23.5506507, -46.6333824, -3),
               'sydney': CityParams('sydney', -33.8698439, 151.2082848, 10),
               'newyork': CityParams('newyork', 40.7127281, -74.0060152, -5),
               'moscow': CityParams('moscow', 55.7504461, 37.6174943, 3),
               'tokyo': CityParams('tokyo', 35.6828387, 139.7594549, 9),
               'nairobi': CityParams('nairobi', -1.2832533, 36.8172449, 3),
               'asuncion': CityParams('asuncion', -25.2800459, -57.6343814, -4),
               'lagos': CityParams('lagos', 6.4550575, 3.3941795, 1)}

# global variables
logger = logging.getLogger()
if len(logger.handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logger.setLevel(logging.INFO)
else:
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level='INFO', filename='weather.log')


# common functions

def utcnow_date() -> date:
    """
    Return date object corresponding to the current UTC datetime
    """
    current_utc_dt = datetime.utcnow()
    return date(current_utc_dt.year, current_utc_dt.month, current_utc_dt.day)


@retry(retry=retry_if_exception_type((RequestsConnectionError, Timeout)), stop=stop_after_attempt(2), wait=wait_fixed(5), reraise=True)
def read_remote_resource(url):
    return requests.get(url, timeout=10)


def fetch_data(weather_resource_url: str) -> requests.Response:
    try:
        return read_remote_resource(weather_resource_url)
    except Exception as ex:
        logger.error("Error '%s' while reading '%s'", ex, weather_resource_url, exc_info=False)
        raise ex


def write_to_filesystem(file_name: str, data: str, csv_header: str):
    logger.info('writing file %s', file_name)
    if os.path.exists(file_name):
        # append data
        with open(f"{file_name}", 'a', encoding='UTF-8') as f:
            f.write(data)
    else:
        # add header when file is first created
        with open(f"{file_name}", 'w', encoding='UTF-8') as f:
            f.write(f"{csv_header}\n{data}")


def write_data(city_name: str, weather_resource: str, weather_data_csv: csv_rows, csv_files_path, csv_header):
    csv_file_name = f"{csv_files_path}/{weather_resource}_{city_name}.csv"
    csv_data_serialized = ('\n'.join([','.join(map(str, row)) for row in weather_data_csv])) + '\n'
    write_to_filesystem(csv_file_name, csv_data_serialized, csv_header)


def transform_data(weather_data: requests.Response, run_params: dict) -> csv_rows:
    try:
        weather_data_json = weather_data.json()
        return run_params['json_to_csv_f'](weather_data_json, run_params)
    except Exception as ex:
        logger.error("Error '%s' while parsing '%s'", ex, weather_data.text, exc_info=True)
        raise ex


def run_city(city_name: str, run_params: dict):
    try:
        weather_data = fetch_data(run_params['weather_resource_url'])
        weather_data_csv = transform_data(weather_data, run_params)
        write_data(city_name, run_params['weather_resource'], weather_data_csv, run_params['csv_files_path'], run_params['csv_header'])
    except Exception as ex:
        logger.error("Error '%s' while processing '%s'", ex, city_name, exc_info=True)
