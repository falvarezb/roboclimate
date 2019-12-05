import csv
import os
import datetime
import jsonlines

new_files = "./new_files"
# move here files already processed
old_files = "./old_files"
csv_files = "./csv_files"

csv_header = ['temp', 'pressure', 'humidity', 'wind_speed', 'wind_deg', 'dt']


def pre_process_weather_resource(weather_resource, func):
    new_file = f"{new_files}/{weather_resource}.jsonl"
    old_file = f"{old_files}/{weather_resource}.jsonl"
    with jsonlines.open(new_file, "r") as reader:
        csv_file = f"{csv_files}/{weather_resource}.csv"
        is_write_header = not os.path.exists(csv_file)
        with open(csv_file, 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            if is_write_header:
                csv_writer.writerow(csv_header)
            for row in reader.iter():
                for j in func(row):
                    csv_writer.writerow([j['main']['temp'], j['main']['pressure'], j['main']['humidity'],
                                         j['wind']['speed'], j['wind'].get('deg', ""), j['dt']])
    os.replace(new_file, old_file)


def pre_process_current_weather():
    pre_process_weather_resource("weather", lambda row: list([row]))


def pre_process_five_day_weather_forecast():
    pre_process_weather_resource("forecast", lambda row: row['list'])





def main():
    if not os.path.exists(old_files):
        os.makedirs(old_files)

    if not os.path.exists(csv_files):
        os.makedirs(csv_files)

    # pre_process_current_weather()
    pre_process_five_day_weather_forecast()

    # scheduler = BlockingScheduler()
    # scheduler.add_job(current_weather, "interval", [locations['london']], minutes=1)
    # scheduler.add_job(five_day_weather_forecast, "interval", [locations['london']], minutes=1)
    # scheduler.start()


if __name__ == '__main__':
    main()
