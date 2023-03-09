'''
module with common elements to "weather_spider" and "forecast_spider"
'''

from datetime import timezone, datetime, date
import os
import logging
import requests
from requests.exceptions import ConnectionError
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

WEATHER_RESOURCE = "forecast"
S3_BUCKET_NAME = "roboclimate"
S3_OBJECT_PREFIX = "forecast"
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


def utcnow_date() -> date:
    """
    Return date object corresponding to the current UTC datetime
    """
    current_utc_dt = datetime.utcnow()
    return date(current_utc_dt.year, current_utc_dt.month, current_utc_dt.day)


@retry(retry=retry_if_exception_type(ConnectionError), stop=stop_after_attempt(2), wait=wait_fixed(5), reraise=True)
def read_remote_resource(url):
    return requests.get(url)


def compose_url(city_id: int, weather_resource: str):
    return f"http://api.openweathermap.org/data/2.5/{weather_resource}?id={city_id}&units=metric&appid={os.environ.get('OPEN_WEATHER_API')}"


########################################


def fetch_data(city_id) -> requests.Response:
    try:
        url = compose_url(city_id)
        return read_remote_resource(url)
    except Exception as ex:
        logger.error(f"Error '{ex}' while reading '{url}'", exc_info=False)
        raise ex


def transform_data(weather_data: requests.Response, utcnow_date_f, json_to_csv) -> csv_rows:
    try:
        weather_data_json = weather_data.json()
        return json_to_csv(weather_data_json, utcnow_date_f())
    except Exception as ex:
        logger.error(f"Error '{ex}' while parsing '{weather_data.text}'", exc_info=True)
        raise ex


def write_to_filesystem(file_name: str, data: str):
    logger.info(f'writing file {file_name}')
    if os.path.exists(file_name):
        # append data
        with open(f"{file_name}", 'a', encoding='UTF-8') as f:
            f.write(data)
    else:
        # add header when file is first created
        with open(f"{file_name}", 'w', encoding='UTF-8') as f:
            f.write(f"{CSV_HEADER}\n{data}")


def write_to_s3(file_name: str, data: str):
    try:
        existing_data = s3.get_object(Bucket=S3_BUCKET_NAME, Key=file_name)['Body'].read().decode('UTF-8')
    except botocore.exceptions.ClientError:
        # add header when file is first created
        data = f"{CSV_HEADER}\n{data}"
    else:
        # append data
        data = f"{existing_data}{data}"
    logger.info(f'writing object {file_name} in bucket {S3_BUCKET_NAME}')
    s3.put_object(Body=data, Bucket=S3_BUCKET_NAME, Key=file_name)


def write_data(city_name: str, weather_data_csv: csv_rows, write_f, s3_object_prefix):
    csv_file_name = f"{s3_object_prefix}/{WEATHER_RESOURCE}_{city_name}.csv"
    csv_data_serialized = ('\n'.join([','.join(map(str, row)) for row in weather_data_csv]))+'\n'
    write_f(csv_file_name, csv_data_serialized)


def run_city(city_name: str, city_id: int, injected_params: dict):
    try:
        weather_data = fetch_data(city_id)
        weather_data_csv = transform_data(weather_data, injected_params['utcnow_date_f'])
        write_data(city_name, weather_data_csv, injected_params['write_f'], injected_params['s3_object_prefix'])
    except Exception as ex:
        logger.error(f"Error '{ex}' while processing '{city_name}'", exc_info=True)


def handler(event, context):
    if event is not None:
        write_f = write_to_s3
        logger.info('running on AWS env')
    else:
        write_f = write_to_filesystem
        logger.info('running on local env')

    for city_name, city_id in CITIES.items():
        injected_params = dict(
            utcnow_date_f=utcnow_date,
            write_f=write_f,            
            s3_object_prefix=S3_OBJECT_PREFIX
        )

        run_city(city_name, city_id, injected_params)


# when running on AWS env, __name__ = file name specified in AWS runtime's handler
if __name__ == '__main__':
    handler(None, None)
