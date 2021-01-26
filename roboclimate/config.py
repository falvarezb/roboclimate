import datetime as dt
from collections import namedtuple

City = namedtuple('City', 'id name firstMeasurement')
cities = {"london": City(2643743, 'london', dt.datetime(2019, 11, 28, 3, 0, 0, tzinfo=dt.timezone.utc)),
          "madrid": City(3117735, 'madrid', dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          "saopaulo": City(3448439, 'saopaulo', dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          "sydney": City(2147714, 'sydney', dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          "newyork": City(5128581, 'newyork', dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          "moscow": City(524901, 'moscow', None),
          "tokyo": City(1850147, 'tokyo', None),
          "nairobi": City(184745, 'nairobi', None),
          "asuncion": City(3439389, 'asuncion', None),
          "lagos": City(2332459, 'lagos', None)}

weather_resources = ['weather', 'forecast']
csv_folder = "csv_files"
csv_header = ['temp', 'pressure', 'humidity', 'wind_speed', 'wind_deg', 'dt', 'today']
tolerance = {'positive_tolerance': 1200, 'negative_tolerance': 30}  # tolerance in seconds
day_factor = 8  # number of data points per day

if __name__ == "__main__":
    for city in cities:
        print(city)
