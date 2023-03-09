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

WEATHER_RESOURCE = "weather"
CSV_FILES_PATH = "weather"
CSV_HEADER = "temp,pressure,humidity,wind_speed,wind_deg,dt,today"
TOLERANCE = {'positive_tolerance': 1200, 'negative_tolerance': 60}  # tolerance in seconds

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


def epoch_time(date: date) -> 'dict[str,int]':
    """
    Calculate the POSIX timestamp at the hours: 0, 3, 6, 9, 12, 15, 18 and 21 of the date passed as parameter

    According to https://docs.python.org/3.6/library/datetime.html

    'There is no method to obtain the POSIX timestamp directly from a naive datetime instance representing UTC time.
    If your application uses this convention and your system timezone is not set to UTC,
    you can obtain the POSIX timestamp by supplying tzinfo=timezone.utc'

    Parameters
    ----------
    date : date

        date to use as reference to calculate the POSIX timestamp. As POSIX timestamp is always in UTC, 'date' will be
        converted in a datetime in UTC timezone

    Returns
    -------
    dict

        dict containing 8 pairs where the keys are the hours "0", "3", "6", "9", "12", "15", "18", "21" and the values are
        the corresponding POSIX timestamp on the given date

    """

    three_hours_in_seconds = 60 * 60 * 3
    initial_timestamp = datetime(date.year, date.month, date.day, tzinfo=timezone.utc).timestamp()
    keys = [str(j) for j in range(0, 24, 3)]
    values = [initial_timestamp + three_hours_in_seconds * j for j in range(0, 8)]
    return dict(zip(keys, values))


def normalise_datetime(dt: int, current_utc_date: date, tolerance: 'dict[str,int]'):
    """
    Open Weather's "five day forecast" endpoint always returns data for 8 specific timestamps: 0, 3, 6, 9, 12, 15, 18 and 21.

    On the other hand the "current weather" endpoint does not always return the "current timestamp":
        - most of the times the API returns stale data (up to 10 min)
        - the returned data contains numerous temporal gaps

    Therefore, even if we call the "current weather" endpoint at the above intervals, there is no guarantee that the returned
    timestamps will match the expected values.

    However, to be able to match forecast and real measurements, the "current weather" timestamps need to be recorded as one of the
    8 possible values for a given day. And that's what the normalisation carried out by this function is about

    Parameters
    ----------
    dt : int

        POSIX timestamp (only the int part) returned by the "current weather" endpoint

    current_utc_date : date

        current UTC date and time

    tolerance: int

        interval of time (in seconds) in which 2 timestamps are considered the same

    Returns
    -------
    int

        POSIX timestamp corresponding to the matching interval of the current date. If matching failed, original dt is returned

    """
    lower_bound = dt - tolerance['negative_tolerance']
    upper_bound = dt + tolerance['positive_tolerance']
    normalised_dts = epoch_time(current_utc_date)

    for hour in iter(normalised_dts):
        if lower_bound <= normalised_dts[hour] < upper_bound:
            return normalised_dts[hour]
    logger.warning(f"it was not possible to normalise this timestamp {dt} to any of the values in {normalised_dts}")
    return dt


def transform_weather_data_to_csv(weather_data_json, current_utc_datetime, tolerance) -> csv_rows:
    return [[weather_data_json['main']['temp'], weather_data_json['main']['pressure'], weather_data_json['main']['humidity'], weather_data_json['wind']['speed'], weather_data_json['wind'].get('deg', ""), normalise_datetime(weather_data_json['dt'], current_utc_datetime, tolerance), str(current_utc_datetime)[:10]]]


@retry(retry=retry_if_exception_type(ConnectionError), stop=stop_after_attempt(2), wait=wait_fixed(5), reraise=True)
def read_remote_resource(url):
    return requests.get(url)


def compose_url(city_id: int):
    return f"http://api.openweathermap.org/data/2.5/{WEATHER_RESOURCE}?id={city_id}&units=metric&appid={os.environ.get('OPEN_WEATHER_API')}"


########################################


def fetch_data(city_id) -> requests.Response:
    try:
        url = compose_url(city_id)
        return read_remote_resource(url)
    except Exception as ex:
        logger.error(f"Error '{ex}' while reading '{url}'", exc_info=False)
        raise ex


def transform_data(weather_data: requests.Response, utcnow_date_f, tolerance: "dict[str, int]") -> csv_rows:
    try:
        weather_data_json = weather_data.json()
        return transform_weather_data_to_csv(weather_data_json, utcnow_date_f(), tolerance)
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
    s3_bucket_name = os.environ.get('S3_BUCKET_NAME')
    try:
        existing_data = s3.get_object(Bucket=s3_bucket_name, Key=file_name)['Body'].read().decode('UTF-8')
    except botocore.exceptions.ClientError:
        # add header when file is first created
        data = f"{CSV_HEADER}\n{data}"
    else:
        # append data
        data = f"{existing_data}{data}"
    logger.info(f'writing object {file_name} in bucket {s3_bucket_name}')
    s3.put_object(Body=data, Bucket=s3_bucket_name, Key=file_name)


def write_data(city_name: str, weather_data_csv: csv_rows, write_f, csv_files_path):
    csv_file_name = f"{csv_files_path}/{WEATHER_RESOURCE}_{city_name}.csv"
    csv_data_serialized = ('\n'.join([','.join(map(str, row)) for row in weather_data_csv]))+'\n'
    write_f(csv_file_name, csv_data_serialized)


def run_city(city_name: str, city_id: int, injected_params: dict):
    try:
        weather_data = fetch_data(city_id)
        weather_data_csv = transform_data(weather_data, injected_params['utcnow_date_f'], injected_params['tolerance'])
        write_data(city_name, weather_data_csv, injected_params['write_f'], injected_params['csv_files_path'])
    except Exception as ex:
        logger.error(f"Error '{ex}' while processing '{city_name}'", exc_info=True)


def weather_handler(event, context):
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
            tolerance=TOLERANCE,
            csv_files_path=CSV_FILES_PATH
        )

        run_city(city_name, city_id, injected_params)


# when running on AWS env, __name__ = file name specified in AWS runtime's handler
if __name__ == '__main__':
    weather_handler(None, None)
