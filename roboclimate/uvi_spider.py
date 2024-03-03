"""Module to get the daily maximum of the UV index for a given city

To get the maximum UVI value, we need to consider the time of the day when the sun is at its highest point in the sky (solar noon).
For the purpose of this application, we'll assume that solar noon occurs at 12:00:00 (civil noon). 
This is a simplification as the actual solar noon can vary from day to day.

For time zones with DST, solar noon happens at 13:00:00 during the period of daylight saving time.
To avoid having to deal with DST, the current implementation is not DST-aware and therefore solar noon is always at 12:00:00.

Technical details
-----------------
1. The module can be run locally or on AWS Lambda.
2. The function retrieves the UV index at solar noon for the previous day for every configured location.
3. The data is stored in a CSV file (locally or in EFS if running as a lambda function).

"""
import os
from datetime import timedelta, timezone, datetime, date
from common import CITY_PARAMS, logger, run_city, csv_rows

# constants
WEATHER_RESOURCE = "uvi"


def transform_weather_data_to_csv(weather_data_json: dict, run_params: dict) -> csv_rows:
    return [[weather_data_json['data'][0]['dt'], weather_data_json['data'][0]['uvi']]]


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
        # using 'offset' time zone to avoid dealing with DST
        tz = timezone(timedelta(city_params.tz_offset))
        solar_noon_dt = int(datetime(yesterday.year, yesterday.month, yesterday.day, 12, 0, 0, tzinfo=tz).timestamp())
        weather_resource_url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={city_params.lat}&lon={city_params.lon}&units=metric&dt={solar_noon_dt}&appid={os.environ.get('OPEN_WEATHER_API')}"
        run_city(city_name, WEATHER_RESOURCE, weather_resource_url, run_params)


# when running on AWS env, __name__ = file name specified in AWS runtime's handler
if __name__ == '__main__':
    handler(None, None)
