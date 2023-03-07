from typing import Mapping
from threading import Thread
from datetime import timezone, datetime, date
import os
import logging
from json.decoder import JSONDecodeError
import requests
from requests.exceptions import ConnectionError
from tenacity import retry, retry_if_exception_type, wait_fixed, stop_after_attempt
import datetime as dt
from collections import namedtuple
import boto3

s3 = boto3.client('s3')

# type alias
csv_row = "list[str]"
csv_rows = "list[csv_row]"
City = namedtuple('City', 'id name firstMeasurement')

# constants
CITIES = {"london": City(2643743, 'london', dt.datetime(2019, 11, 28, 3, 0, 0, tzinfo=dt.timezone.utc)),
          "madrid": City(3117735, 'madrid', dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          "saopaulo": City(3448439, 'saopaulo', dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          "sydney": City(2147714, 'sydney', dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          "newyork": City(5128581, 'newyork', dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          "moscow": City(524901, 'moscow', dt.datetime(2021, 1, 27, 3, 0, 0, tzinfo=dt.timezone.utc)),
          "tokyo": City(1850147, 'tokyo', dt.datetime(2021, 1, 27, 3, 0, 0, tzinfo=dt.timezone.utc)),
          "nairobi": City(184745, 'nairobi', dt.datetime(2021, 1, 27, 3, 0, 0, tzinfo=dt.timezone.utc)),
          "asuncion": City(3439389, 'asuncion', dt.datetime(2021, 1, 27, 3, 0, 0, tzinfo=dt.timezone.utc)),
          "lagos": City(2332459, 'lagos', dt.datetime(2021, 1, 27, 3, 0, 0, tzinfo=dt.timezone.utc))}

WEATHER_RESOURCE = "weather"
S3_BUCKET_NAME = "roboclimate"
S3_OBJECT_PREFIX = "weather"
CSV_HEADER = ['temp', 'pressure', 'humidity', 'wind_speed', 'wind_deg', 'dt', 'today']
TOLERANCE = {'positive_tolerance': 1200, 'negative_tolerance': 60}  # tolerance in seconds


logger = logging.getLogger(__name__)


def generate_current_utc_date() -> date:
    """
    Return date object corresponding to the current UTC datetime
    """
    current_utc_dt = datetime.utcnow()
    return date(current_utc_dt.year, current_utc_dt.month, current_utc_dt.day)


def epoch_time(date: date):
    """
    Calculate the POSIX timestamp at the times: 0, 3, 6, 9, 12, 15, 18 and 21 of the date passed as parameter

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


def normalise_datetime(dt, current_utc_date, tolerance):
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
    except ConnectionError:
        logger.error(f"ConnectionError while reading {url}", exc_info=True)
    except Exception as ex:
        logger.error(f"Error {ex} while reading {url}", exc_info=True)


def transform_data(weather_data: requests.Response, generate_current_utc_date, tolerance: "dict[str, int]") -> csv_rows:
    try:
        weather_data_json = weather_data.json()
        return transform_weather_data_to_csv(weather_data_json, generate_current_utc_date(), tolerance)
    except JSONDecodeError:
        logger.error(f"JSONDecodeError while parsing '{weather_data.text}'", exc_info=True)


def write_f(file_name, data):
    s3.put_object(Body=data, Bucket=S3_BUCKET_NAME, Key=file_name)


def write_data(city_name: str, weather_data_csv: csv_rows, write_f, s3_object_prefix):
    csv_file_name = f"{s3_object_prefix}/{WEATHER_RESOURCE}_{city_name}.csv"
    weather_data_csv_with_header = [CSV_HEADER]
    weather_data_csv_with_header.extend(weather_data_csv)
    csv_data_serialized = '\n'.join([','.join(map(str, row)) for row in weather_data_csv_with_header])
    write_f(csv_file_name, csv_data_serialized)


def run_thread(city_name, city_id, injected_params):
    try:
        weather_data = fetch_data(city_id)
        weather_data_csv = transform_data(weather_data, injected_params.generate_current_utc_date, injected_params.tolerance)
        write_data(city_name, weather_data_csv, injected_params.write_f, injected_params.s3_object_prefix)
    except Exception as ex:
        logger.error(f"Error {ex} while processing {city_name}", exc_info=True)


def main():
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level='INFO')
    for city_name, city_id in CITIES.items():
        injected_params = dict(
            generate_current_utc_date=generate_current_utc_date,
            write_f=write_f,
            tolerance=TOLERANCE,
            s3_object_prefix=S3_OBJECT_PREFIX
        )
        # the GIL is always released when doing I/O
        # (https://docs.python.org/3/glossary.html#term-global-interpreter-lock)
        Thread(target=run_thread, name=city_name, args=(city_name, city_id, injected_params)).start()


if __name__ == '__main__':
    main()
