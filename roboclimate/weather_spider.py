from datetime import timezone, datetime, date
from common import logger, write_to_s3, write_to_filesystem, utcnow_date, run_city, csv_rows, CITIES

# constants
WEATHER_RESOURCE = "weather"
CSV_FILES_PATH = "weather"
TOLERANCE = {'positive_tolerance': 1200, 'negative_tolerance': 60}  # tolerance in seconds


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
    logger.warning("it was not possible to normalise this timestamp %s to any of the values in %s", dt, normalised_dts)
    return dt


def transform_weather_data_to_csv(weather_data_json: dict, conversion_params: dict) -> csv_rows:
    current_utc_date = conversion_params['utcnow_date']
    tolerance = conversion_params['tolerance']
    return [[weather_data_json['main']['temp'], weather_data_json['main']['pressure'], weather_data_json['main']['humidity'], weather_data_json['wind']['speed'], weather_data_json['wind'].get('deg', ""), normalise_datetime(weather_data_json['dt'], current_utc_date, tolerance), str(current_utc_date)]]


def weather_handler(event, context):
    if event is not None:
        write_f = write_to_s3
        logger.info('running on AWS env')
    else:
        write_f = write_to_filesystem
        logger.info('running on local env')

    for city_name, city_id in CITIES.items():
        run_params = {
            'utcnow_date': utcnow_date(),
            'tolerance': TOLERANCE,
            'json_to_csv_f': transform_weather_data_to_csv,
            'write_f': write_f,
            'csv_files_path': CSV_FILES_PATH
        }

        run_city(city_name, city_id, WEATHER_RESOURCE, run_params)


# when running on AWS env, __name__ = file name specified in AWS runtime's handler
if __name__ == '__main__':
    weather_handler(None, None)
