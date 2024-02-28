from datetime import datetime, date
import os
import logging
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout
from tenacity import retry, retry_if_exception_type, wait_fixed, stop_after_attempt
import boto3
import botocore

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

# https://api.openweathermap.org/geo/1.0/direct?q=London,GB&limit=5&appid=YOUR_API_KEY
CITY_COORDINATES = {"london": (51.5073219, -0.1276474),
                        "madrid": (40.4167047, -3.7035825),
                        "saopaulo": (-23.5506507, -46.6333824),
                        "sydney": (-33.8698439, 151.2082848),
                        "newyork": (40.7127281, -74.0060152),
                        "moscow": (55.7504461, 37.6174943),
                        "tokyo": (35.6828387, 139.7594549),
                        "nairobi": (-1.2832533, 36.8172449),
                        "asuncion": (-25.2800459, -57.6343814),
                        "lagos": (6.4550575, 3.3941795)}

CSV_HEADER = "temp,pressure,humidity,wind_speed,wind_deg,dt,today"

# global variables
s3 = boto3.client('s3')
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


def write_to_filesystem(file_name: str, data: str):
    logger.info('writing file %s', file_name)
    if os.path.exists(file_name):
        # append data
        with open(f"{file_name}", 'a', encoding='UTF-8') as f:
            f.write(data)
    else:
        # add header when file is first created
        with open(f"{file_name}", 'w', encoding='UTF-8') as f:
            f.write(f"{CSV_HEADER}\n{data}")


def write_to_s3(file_name: str, data: str):
    s3_bucket_name = os.environ.get('S3_BUCKET_NAME')
    try:
        existing_data = s3.get_object(Bucket=s3_bucket_name, Key=file_name)['Body'].read().decode('UTF-8')
    except botocore.exceptions.ClientError:
        # add header when file is first created
        data = f"{CSV_HEADER}\n{data}"
    else:
        # append data
        data = f"{existing_data}{data}"
    logger.info('writing object %s in bucket %s', file_name, s3_bucket_name)
    s3.put_object(Body=data, Bucket=s3_bucket_name, Key=file_name)


def write_data(city_name: str, weather_resource: str, weather_data_csv: csv_rows, csv_files_path):
    csv_file_name = f"{csv_files_path}/{weather_resource}_{city_name}.csv"
    csv_data_serialized = ('\n'.join([','.join(map(str, row)) for row in weather_data_csv])) + '\n'
    write_to_filesystem(csv_file_name, csv_data_serialized)


def transform_data(weather_data: requests.Response, run_params: dict) -> csv_rows:
    try:
        weather_data_json = weather_data.json()
        return run_params['json_to_csv_f'](weather_data_json, run_params)
    except Exception as ex:
        logger.error("Error '%s' while parsing '%s'", ex, weather_data.text, exc_info=True)
        raise ex


def run_city(city_name: str, weather_resource: str, weather_resource_url: str, run_params: dict):
    try:
        weather_data = fetch_data(weather_resource_url)
        weather_data_csv = transform_data(weather_data, run_params)
        write_data(city_name, weather_resource, weather_data_csv, run_params['csv_files_path'])
    except Exception as ex:
        logger.error("Error '%s' while processing '%s'", ex, city_name, exc_info=True)
