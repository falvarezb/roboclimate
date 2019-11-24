import json
import time
import os
import requests
import jsonlines
from apscheduler.schedulers.blocking import BlockingScheduler


#resource = weather | forecast
#id = london | madrid | ...

# newly fetched data
new_files = "./new_files"
locations = {"london": 2643743}
api_key = os.environ.get("OPEN_WEATHER_API")
main_path = "http://api.openweathermap.org/data/2.5"


def fetch_weather_data(weather_resource, location):
    result = requests.get(f"{main_path}/{weather_resource}?id={location}&appid={api_key}&units=metric").text
    result = json.loads(result)
    # unix_time = int(time.time())
    with jsonlines.open(f"{new_files}/{weather_resource}.jsonl", "a") as writer:
        writer.write(result)


def current_weather(location):
    fetch_weather_data("weather", location)


def five_day_weather_forecast(location):
    fetch_weather_data("forecast", location)


def main():
    if not os.path.exists(new_files):
        os.makedirs(new_files)

    scheduler = BlockingScheduler()
    scheduler.add_job(current_weather, "interval", [locations['london']], minutes=1)
    scheduler.add_job(five_day_weather_forecast, "interval", [locations['london']], minutes=1)
    scheduler.start()

if __name__ == '__main__':
    main()
