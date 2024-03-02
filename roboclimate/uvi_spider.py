import os
from datetime import timedelta, timezone, datetime, date
import time
from common import CITY_PARAMS, logger, run_city, csv_rows
from util import noon_dt_gen

# constants
WEATHER_RESOURCE = "uvi"


def transform_weather_data_to_csv(weather_data_json: dict, run_params: dict) -> csv_rows:
    return [[weather_data_json['current']['dt'], weather_data_json['current']['uvi']]]


def handler(event, context):
    if event is not None:
        logger.info('running on AWS env')
    else:
        logger.info('running on local env')

    # Please pay attention that historical UV index data available only for 5 days back
    yesterday = date.today() + timedelta(days=-1)
    run_params = {
        'json_to_csv_f': transform_weather_data_to_csv,
        'csv_files_path': os.environ.get('ROBOCLIMATE_CSV_FILES_PATH')
    }
    for city_name, city_params in CITY_PARAMS.items():
        dt = datetime(yesterday.year, yesterday.month, yesterday.day, 12, 0, 0, tzinfo=timezone(timedelta(city_params.tz_offset)))
        weather_resource_url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={city_params.lat}&lon={city_params.lon}&units=metric&dt={dt}&appid={os.environ.get('OPEN_WEATHER_API')}"
        run_city(city_name, WEATHER_RESOURCE, weather_resource_url, run_params)


# when running on AWS env, __name__ = file name specified in AWS runtime's handler
if __name__ == '__main__':
    handler(None, None)
