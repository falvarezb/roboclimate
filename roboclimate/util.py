from datetime import datetime, date, timedelta, timezone
import csv
import os
import logging
import pandas as pd
from roboclimate.config import weather_resources
from roboclimate import config

logger = logging.getLogger(__name__)

def noon_dt_gen(tdelta: timedelta, seed: date):
    """Returns a generator of datetime objects representing the time 12:00:00 for a sequence of dates in the time zone 
    specified by tdelta.

    To get the maximum UVI value, we need to consider the time of the day when the sun is at its highest point in the sky
    (solar noon).

    For the purpose of this application, we'll assume that solar noon occurs at 12:00:00 (civil noon). This is a simplification
    as the actual solar noon can vary from day to day and from one location to another.

    For time zones with DST, solar noon happens at 13:00:00 during the period of daylight saving time.

    To avoid having to deal with DST, the current implementation is not DST-aware and therefore solar noon is always at 12:00:00.

    Args:
        tdelta (timedelta): value used to identify the time zone
        seed (date): starting date (to be interpreted in the time zone specified by tdelta)

    Yields:
        float: POSIX timestamp of the datetime object
    """
    # Create a timedelta of 1 day
    one_day = timedelta(days=1)
    dt = datetime(seed.year, seed.month, seed.day, 12, 0, 0, tzinfo=timezone(tdelta))
    while True:
        yield dt.timestamp()
        dt += one_day


def current_utc_date_generator():
    current_utc_dt = datetime.utcnow()
    return date(current_utc_dt.year, current_utc_dt.month, current_utc_dt.day)


def one_year_ago(date_time):
    return n_years_ago(date_time, 1)


def n_years_ago(date_time, n):
    try:
        return date_time.replace(year=date_time.year - n)
    except ValueError:
        return None


def remove_29_feb(df):
    df['dt_iso'] = df['dt'].apply(datetime.fromtimestamp)
    return df.drop(df[df['dt_iso'].apply(lambda x: (x.month, x.day)) == (2, 29)].index)


def csv_file_path(csv_folder, filename, city_name, weather_variable=None):
    if weather_variable:
        return f"{csv_folder}/{weather_variable}/{filename}_{city_name}.csv"
    return f"{csv_folder}/{filename}_{city_name}.csv"


def date_and_timestamp(start_datetime, end_datetime_not_included):
    """
    Args:
        start_datetime: datetime(2019,11,30,0,0,0)
        end_datetime: datetime(2019,11,30,9,0,0)

    Returns:
        list: returns [(1575072000, '2019-11-30'), (1575082800, '2019-11-30'), (1575093600, '2019-11-30')] that corresponds to
        ['2019-11-30 00:00:00', '2019-11-30 00:03:00', '2019-11-30 00:06:00']
    """
    step_3hours = 3600 * 3
    return [(x, date.fromtimestamp(x).isoformat()) for x in range(int(start_datetime.timestamp()), int(end_datetime_not_included.timestamp()), step_3hours)]


def read_historical_data(file):
    df = pd.read_csv(file)
    df['parsed_dt'] = df['dt_iso'].apply(lambda x: x[:19])
    df = df.drop_duplicates('parsed_dt')
    return df.set_index(pd.DatetimeIndex(df['parsed_dt']))


def write_rows(csv_file, rows):
    with open(csv_file, 'a', newline='', encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        for row in rows:
            csv_writer.writerow(row)


def init(csv_folder, csv_header, city_names):
    for _, weather_variable in config.weather_variables.items():
        folder = f"{csv_folder}/{weather_variable}"
        if not os.path.exists(folder):
            logger.info("creating folder %s", folder)
            os.makedirs(folder)

    for weather_resource in weather_resources:
        for city_name in city_names:
            csv_file = csv_file_path(csv_folder, weather_resource, city_name)
            if not os.path.exists(csv_file):
                logger.info("creating file %s", csv_file)
                write_rows(csv_file, [csv_header])


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level='INFO')
    init(config.csv_folder, config.csv_header, config.cities.keys())
