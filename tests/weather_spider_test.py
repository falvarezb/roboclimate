import shutil
import os
import json
import httpretty
import pytest
from datetime import date
from unittest.mock import Mock, patch
from roboclimate.weather_spider import epoch_time, normalise_dt, init, transform_weather_data_to_csv, collect_current_weather_data, collect_five_day_weather_forecast_data


fixtures = dict(
    dt=1575061195,  # Friday, 29 November 2019 20:59:55 UTC
    current_utc_date=date(2019, 11, 29)
)


@pytest.fixture(scope='function')
def csv_folder():
    folder = "tests/temp"
    if os.path.exists(folder):
        shutil.rmtree(folder)
    yield folder
    shutil.rmtree(folder)


# see https://www.epochconverter.com/
def test_epoch_time():
    d = fixtures['current_utc_date']
    assert epoch_time(d) == {"0": 1574985600,
                             "3": 1574996400,
                             "6": 1575007200,
                             "9": 1575018000,
                             "12": 1575028800,
                             "15": 1575039600,
                             "18": 1575050400,
                             "21": 1575061200
                             }


def epoch_time_side_effect(value):
    if value == fixtures['current_utc_date']:
        return {"0": 1574985600,
                "3": 1574996400,
                "6": 1575007200,
                "9": 1575018000,
                "12": 1575028800,
                "15": 1575039600,
                "18": 1575050400,
                "21": 1575061200
                }
    return None


@patch('roboclimate.weather_spider.epoch_time')
def test_normalise_dt_success(mock_epoch_time):
    mock_epoch_time.side_effect = epoch_time_side_effect
    tolerance = 10
    assert normalise_dt(fixtures['dt'], fixtures['current_utc_date'], tolerance) == 1575061200


@patch('roboclimate.weather_spider.epoch_time')
def test_normalise_dt_fail(mock_epoch_time):
    mock_epoch_time.side_effect = epoch_time_side_effect
    tolerance = 1
    assert normalise_dt(fixtures['dt'], fixtures['current_utc_date'], tolerance) == fixtures['dt']


def test_init(csv_folder):
    cities = ["london", "madrid"]
    csv_header = ['field1', 'field2']

    init(csv_folder, csv_header, cities)

    with open(f"{csv_folder}/weather_london.csv") as f:
        assert f.readline() == "field1,field2\n"

    with open(f"{csv_folder}/weather_madrid.csv") as f:
        assert f.readline() == "field1,field2\n"

    with open(f"{csv_folder}/forecast_london.csv") as f:
        assert f.readline() == "field1,field2\n"

    with open(f"{csv_folder}/forecast_madrid.csv") as f:
        assert f.readline() == "field1,field2\n"


def test_transform_current_weather_data_to_csv():
    with open("tests/json_files/weather.json") as f:
        data_json = json.load(f)

    one_row_generator = lambda x: [x]
    identity_dt_normaliser = lambda dt, current_dt, tolerance: dt
    tolerance = 0

    csv_row = transform_weather_data_to_csv(data_json, fixtures['current_utc_date'], one_row_generator, identity_dt_normaliser, tolerance)[0]
    assert csv_row[0] == 300.15
    assert csv_row[1] == 1007
    assert csv_row[2] == 74
    assert csv_row[3] == 3.6
    assert csv_row[4] == 160
    assert csv_row[5] == 1485790200
    assert csv_row[6] == str(fixtures['current_utc_date'])


def test_transform_forecast_weather_data_to_csv():
    with open("tests/json_files/forecast.json") as f:
        data_json = json.load(f)

    rows_generator = lambda row: row['list']
    identity_dt_normaliser = lambda dt, current_dt, tolerance: dt
    tolerance = 0

    csv_row = transform_weather_data_to_csv(data_json, fixtures['current_utc_date'], rows_generator, identity_dt_normaliser, tolerance)
    assert csv_row[0][0] == 261.45
    assert csv_row[0][1] == 1023.48
    assert csv_row[0][2] == 79
    assert csv_row[0][3] == 4.77
    assert csv_row[0][4] == 232.505
    assert csv_row[0][5] == 1485799200
    assert csv_row[0][6] == str(fixtures['current_utc_date'])

    assert csv_row[1][0] == 261.41
    assert csv_row[1][1] == 1022.41
    assert csv_row[1][2] == 76
    assert csv_row[1][3] == 4.76
    assert csv_row[1][4] == 240.503
    assert csv_row[1][5] == 1485810000
    assert csv_row[1][6] == str(fixtures['current_utc_date'])


@httpretty.activate
def test_collect_current_weather_data(csv_folder):
    cities = {"london": 1}
    csv_header = ['temp', 'pressure', 'humidity', 'wind_speed', 'wind_deg', 'dt', 'today']
    tolerance = 60
    current_utc_date_generator = lambda: date(2017, 1, 30)

    init(csv_folder, csv_header, cities)

    with open("tests/json_files/weather.json") as f:
        json_body = f.read()
    
    httpretty.register_uri(httpretty.GET, 'http://api.openweathermap.org/data/2.5/weather',
                           body=json_body,
                           content_type='application/json',
                           status=200)

    collect_current_weather_data(current_utc_date_generator, cities, csv_folder, tolerance)

    with open(f"{csv_folder}/weather_london.csv") as f:
        rows = list(map(lambda row: row.split(','), f.readlines()))

    assert rows[1][0] == '300.15'
    assert rows[1][1] == '1007'
    assert rows[1][2] == '74'
    assert rows[1][3] == '3.6'
    assert rows[1][4] == '160'
    assert rows[1][5] == '1485790200'
    assert rows[1][6] == '2017-01-30\n'


@httpretty.activate
def test_collect_five_day_weather_forecast_data(csv_folder):
    cities = {"london": 1}
    csv_header = ['temp', 'pressure', 'humidity', 'wind_speed', 'wind_deg', 'dt', 'today']
    tolerance = 60
    current_utc_date_generator = lambda: date(2017, 1, 30)

    init(csv_folder, csv_header, cities)

    with open("tests/json_files/forecast.json") as f:
        json_body = f.read()
    
    httpretty.register_uri(httpretty.GET, 'http://api.openweathermap.org/data/2.5/forecast',
                           body=json_body,
                           content_type='application/json',
                           status=200)

    collect_five_day_weather_forecast_data(current_utc_date_generator, cities, csv_folder, tolerance)

    with open(f"{csv_folder}/forecast_london.csv") as f:
        rows = list(map(lambda row: row.split(','), f.readlines()))

    assert rows[1][0] == '261.45'
    assert rows[1][1] == '1023.48'
    assert rows[1][2] == '79'
    assert rows[1][3] == '4.77'
    assert rows[1][4] == '232.505'
    assert rows[1][5] == '1485799200'
    assert rows[1][6] == '2017-01-30\n'

    assert rows[2][0] == '261.41'
    assert rows[2][1] == '1022.41'
    assert rows[2][2] == '76'
    assert rows[2][3] == '4.76'
    assert rows[2][4] == '240.503'
    assert rows[2][5] == '1485810000'
    assert rows[2][6] == '2017-01-30\n'
