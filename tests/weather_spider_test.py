import shutil
import os
import json
import pytest
from datetime import date
from unittest.mock import Mock, patch
from roboclimate.weather_spider import epoch_time, normalise_dt, transform_weather_data_to_csv, collect_current_weather_data, collect_five_day_weather_forecast_data
import roboclimate.config as rconf
import roboclimate.util as rutil

@pytest.fixture(scope='function')
def fixtures():
    return dict(
        dt=1575061195,  # Friday, 29 November 2019 20:59:55 UTC
        dt_on_the_dot=1575061200, # Friday, 29 November 2019 21:00:00 UTC
        dt_higher_than_reference=1575061202, # Friday, 29 November 2019 21:00:02 UTC
        current_utc_date=date(2019, 11, 29)
)

@pytest.fixture(scope='module')
def csv_folder():
    folder = "tests/temp"
    if not os.path.exists(folder):        
        os.mkdir(folder)
    yield folder
    shutil.rmtree(folder)

# see https://www.epochconverter.com/
def test_epoch_time(fixtures):
    d = fixtures['current_utc_date']
    assert epoch_time(d) == {"0": 1574985600.0,
                             "3": 1574996400.0,
                             "6": 1575007200.0,
                             "9": 1575018000.0,
                             "12": 1575028800.0,
                             "15": 1575039600.0,
                             "18": 1575050400.0,
                             "21": 1575061200.0
                             }


def epoch_time_side_effect_gen(current_utc_date):
    def epoch_time_side_effect(value):
        if value == current_utc_date:
            return {"0": 1574985600.0,
                    "3": 1574996400.0,
                    "6": 1575007200.0,
                    "9": 1575018000.0,
                    "12": 1575028800.0,
                    "15": 1575039600.0,
                    "18": 1575050400.0,
                    "21": 1575061200.0
                    }
        return None
    return epoch_time_side_effect


@patch('roboclimate.weather_spider.epoch_time')
def test_normalise_dt_success(mock_epoch_time, fixtures):
    mock_epoch_time.side_effect = epoch_time_side_effect_gen(fixtures['current_utc_date'])
    tolerance = {'positive_tolerance': 10, 'negative_tolerance': 5}
    assert normalise_dt(fixtures['dt'], fixtures['current_utc_date'], tolerance) == 1575061200.0

@patch('roboclimate.weather_spider.epoch_time')
def test_normalise_dt_success_when_dt_on_the_dot(mock_epoch_time, fixtures):
    mock_epoch_time.side_effect = epoch_time_side_effect_gen(fixtures['current_utc_date'])
    tolerance = {'positive_tolerance': 10, 'negative_tolerance': 5}
    assert normalise_dt(fixtures['dt_on_the_dot'], fixtures['current_utc_date'], tolerance) == 1575061200.0

@patch('roboclimate.weather_spider.epoch_time')
def test_normalise_dt_success_when_dt_higher_than_reference(mock_epoch_time, fixtures):
    mock_epoch_time.side_effect = epoch_time_side_effect_gen(fixtures['current_utc_date'])
    tolerance = {'positive_tolerance': 10, 'negative_tolerance': 5}
    assert normalise_dt(fixtures['dt_higher_than_reference'], fixtures['current_utc_date'], tolerance) == 1575061200.0


@patch('roboclimate.weather_spider.epoch_time')
def test_normalise_dt_fail(mock_epoch_time, fixtures):
    mock_epoch_time.side_effect = epoch_time_side_effect_gen(fixtures['current_utc_date'])
    tolerance = {'positive_tolerance': 1, 'negative_tolerance': 5}
    assert normalise_dt(fixtures['dt'], fixtures['current_utc_date'], tolerance) == fixtures['dt']





def test_transform_current_weather_data_to_csv(fixtures):
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


def test_transform_forecast_weather_data_to_csv(fixtures):
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


@patch('roboclimate.weather_spider.requests')
@patch('roboclimate.weather_spider.os.environ')
def test_collect_current_weather_data(env, req, csv_folder):
    cities = dict(list(rconf.cities.items())[0:1]) #taking first element of rconf.cities
    csv_header = rconf.csv_header
    tolerance = {'positive_tolerance': 60, 'negative_tolerance': 5}
    current_utc_date_generator = lambda: date(2017, 1, 30)

    rutil.init(csv_folder, csv_header, cities)

    with open("tests/json_files/weather.json") as f:
        json_body = json.loads(f.read())
    
    response_mock = Mock()
    response_mock.json.return_value = json_body
    req.get.return_value = response_mock
    env.get.return_value='id'

    collect_current_weather_data(current_utc_date_generator, cities, csv_folder, tolerance)
    
    req.get.assert_any_call("http://api.openweathermap.org/data/2.5/weather?id=2643743&units=metric&appid=id")

    print(f"myfolder:{csv_folder}/weather_london.csv")
    with open(f"{csv_folder}/weather_london.csv") as f:
        rows = list(map(lambda row: row.split(','), f.readlines()))

    assert rows[1][0] == '300.15'
    assert rows[1][1] == '1007'
    assert rows[1][2] == '74'
    assert rows[1][3] == '3.6'
    assert rows[1][4] == '160'
    assert rows[1][5] == '1485790200'
    assert rows[1][6] == '2017-01-30\n'


@patch('roboclimate.weather_spider.requests')
@patch('roboclimate.weather_spider.os.environ')
def test_collect_five_day_weather_forecast_data(env, req, csv_folder):
    cities = dict(list(rconf.cities.items())[0:1]) #taking first element of rconf.cities
    csv_header = ['temp', 'pressure', 'humidity', 'wind_speed', 'wind_deg', 'dt', 'today']
    tolerance = 60
    current_utc_date_generator = lambda: date(2017, 1, 30)

    rutil.init(csv_folder, csv_header, cities)

    with open("tests/json_files/forecast.json") as f:
        json_body = json.loads(f.read())

    response_mock = Mock()
    response_mock.json.return_value = json_body
    req.get.return_value = response_mock
    env.get.return_value='id'

    collect_five_day_weather_forecast_data(current_utc_date_generator, cities, csv_folder, tolerance)

    req.get.assert_any_call("http://api.openweathermap.org/data/2.5/forecast?id=2643743&units=metric&appid=id")

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
