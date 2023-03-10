'''
module with common elements to "weather_spider" and "forecast_spider"
'''

from common import *

# constants
WEATHER_RESOURCE = "forecast"
CSV_FILES_PATH = "forecast"

def transform_weather_data_to_csv(weather_resource_json, conversion_params):
    current_utc_date = conversion_params['utcnow_date']
    return [[j['main']['temp'], j['main']['pressure'], j['main']['humidity'], j['wind']['speed'], j['wind'].get('deg', ""), j['dt'], str(current_utc_date)] for j in weather_resource_json['list']]


def handler(event, context):
    if event is not None:
        write_f = write_to_s3
        logger.info('running on AWS env')
    else:
        write_f = write_to_filesystem
        logger.info('running on local env')

    for city_name, city_id in CITIES.items():
        run_params = dict(
            utcnow_date=utcnow_date(),
            json_to_csv_f=transform_weather_data_to_csv,
            write_f=write_f,
            csv_files_path=CSV_FILES_PATH
        )

        run_city(city_name, city_id, WEATHER_RESOURCE, run_params)


# when running on AWS env, __name__ = file name specified in AWS runtime's handler
if __name__ == '__main__':
    handler(None, None)
