import json
from datetime import timezone, datetime, date
import os
import logging
import requests
from apscheduler.schedulers.blocking import BlockingScheduler


def fetch_weather_data_as_json(url):
    result = requests.get(url).text
    return json.loads(result)


def transform_weather_data_to_csv(weather_resource_json, current_dt, weather_resource_info, tolerance):
    return [[j['main']['temp'], j['main']['pressure'], j['main']['humidity'], j['wind']['speed'], j['wind'].get('deg', ""), weather_resource_info['normaliser'](j['dt'], current_dt, tolerance), str(current_dt)[:10]] for j in weather_resource_info['rows_generator'](weather_resource_json)]


def write_rows(csv_file, rows):
    import csv
    with open(csv_file, 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        for row in rows:
            csv_writer.writerow(row)


def collect_weather_data(weather_resource_info, current_dt, city, tolerance):
    """
    Reads weather data from Open Weather's endpoints and store it in a CSV file

    Parameters
    ----------
    weather_resource_info : dict
        info about the weather resource to be fetched
    current_dt : datetime
        current UTC date and time
    city: int
        city id to get weather data for

    Returns
    -------
    None
        this function only produces side-effects

    """

    try:
        weather_resource_json = fetch_weather_data_as_json(weather_resource_info['url'](city))
        rows = transform_weather_data_to_csv(weather_resource_json, current_dt(), weather_resource_info, tolerance)
        write_rows(weather_resource_info['csv_file'], rows)
    except Exception:
        logging.error(f"Error while reading {weather_resource_info['url'](city)}", exc_info=True)


def url(weather_resource):
    return lambda city: f"http://api.openweathermap.org/data/2.5/{weather_resource}?id={city}&appid={os.environ.get('OPEN_WEATHER_API')}&units=metric"


def epoch_time(date):
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

        dict containing 8 pairs (time, POSIX timestamp) corresponding to the date passed as parameter
        the keys of the 8 pairs are: "0", "3", "6", "9", "12", "15", "18", "21"

    """

    three_hours_in_seconds = 60 * 60 * 3
    initial_timestamp = datetime(date.year, date.month, date.day, tzinfo=timezone.utc).timestamp()
    keys = [str(j) for j in range(0, 24, 3)]
    values = [initial_timestamp + three_hours_in_seconds*j for j in range(0, 8)]
    return dict(zip(keys, values))


def normalise_dt(dt, current_utc_date, tolerance):
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
    lower_bound = dt
    upper_bound = dt + tolerance
    normalised_dts = epoch_time(current_utc_date)

    for hour in iter(normalised_dts):
        if lower_bound < normalised_dts[hour] < upper_bound:
            return normalised_dts[hour]
    logging.warning(f"it was not possible to normalise this timestamp {dt} to any of the values in {normalised_dts}")
    return dt


def main():

    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level='INFO')
    cities = {"london": 2643743}
    csv_folder = "csv_files"
    csv_header = ['temp', 'pressure', 'humidity', 'wind_speed', 'wind_deg', 'dt', 'today']
    tolerance = 1200

    weather_resource_config = {
        "current_weather": {
            "url": url("weather"),
            "csv_file": f"{csv_folder}/weather.csv",
            "rows_generator": lambda row: [row],
            "normaliser": normalise_dt
        },
        "five_day_weather_forecast": {
            "url": url("forecast"),
            "csv_file": f"{csv_folder}/forecast.csv",
            "rows_generator": lambda row: row['list'],
            "normaliser": lambda dt, current_dt, tolerance: dt
        }
    }

    def current_utc_date():
        current_utc_dt = datetime.utcnow()
        return date(current_utc_dt.year, current_utc_dt.month, current_utc_dt.day)

    def init():
        if not os.path.exists(csv_folder):
            logging.info(f"creating folder {csv_folder}")
            os.makedirs(csv_folder)

        for key in iter(weather_resource_config):
            csv_file = weather_resource_config[key]["csv_file"]
            if not os.path.exists(csv_file):
                logging.info(f"creating file {csv_file}")
                write_rows(csv_file, [csv_header])

    init()
    collect_weather_data(weather_resource_config['current_weather'], current_utc_date, cities['london'], tolerance)
    collect_weather_data(weather_resource_config['five_day_weather_forecast'], current_utc_date, cities['london'], tolerance)

    # scheduler = BlockingScheduler()
    # scheduler.add_job(collect_weather_data, 'cron', [weather_resource_config['current_weather'], current_utc_date, cities['london'], tolerance], hour='*/3')
    # scheduler.add_job(collect_weather_data, 'cron', [weather_resource_config['five_day_weather_forecast'], current_utc_date, cities['london'], tolerance], hour=22)
    # scheduler.start()


if __name__ == '__main__':
    main()
