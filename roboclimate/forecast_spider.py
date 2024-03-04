import os
from common import logger, run_city, utcnow_date, CITIES

# constants
WEATHER_RESOURCE = "forecast"


def transform_weather_data_to_csv(weather_resource_json, run_params):
    current_utc_date = run_params['utcnow_date']
    return [[j['main']['temp'], j['main']['pressure'], j['main']['humidity'], j['wind']['speed'], j['wind'].get('deg', ""), j['dt'], str(current_utc_date)] for j in weather_resource_json['list']]


def forecast_handler(event, context):
    if event is not None:
        logger.info('running on AWS env')
    else:
        logger.info('running on local env')

    run_params = {
        'utcnow_date': utcnow_date(),
        'json_to_csv_f': transform_weather_data_to_csv,            
        'csv_files_path': os.environ.get('ROBOCLIMATE_CSV_FILES_PATH'),
        'csv_header': 'temp,pressure,humidity,wind_speed,wind_deg,dt,today'
    }
    for city_name, city_id in CITIES.items():        
        weather_resource_url = f"http://api.openweathermap.org/data/2.5/{WEATHER_RESOURCE}?id={city_id}&units=metric&appid={os.environ.get('OPEN_WEATHER_API')}"
        run_city(city_name, WEATHER_RESOURCE, weather_resource_url, run_params)


# when running on AWS env, __name__ = file name specified in AWS runtime's handler
if __name__ == '__main__':
    forecast_handler(None, None)
