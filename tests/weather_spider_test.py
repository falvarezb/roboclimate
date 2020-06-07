import shutil
import os
import json
from datetime import date
from unittest.mock import Mock
from roboclimate.weather_spider import epoch_time, normalise_dt, init, transform_weather_data_to_csv


fixtures = dict(
    dt=1575061195,  # Friday, 29 November 2019 20:59:55 UTC
    current_utc_date=date(2019, 11, 29)
)

# see https://www.epochconverter.com/


def test_epoch_time():
    d = date(2019, 11, 29)
    assert epoch_time(d) == {"0": 1574985600,
                             "3": 1574996400,
                             "6": 1575007200,
                             "9": 1575018000,
                             "12": 1575028800,
                             "15": 1575039600,
                             "18": 1575050400,
                             "21": 1575061200
                             }


def side_effect(value):
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


# epoch_time = Mock(side_effect=side_effect)


def test_normalise_dt_success():
    tolerance = 10
    assert normalise_dt(fixtures['dt'], fixtures['current_utc_date'], tolerance) == 1575061200


def test_normalise_dt_fail():
    tolerance = 1
    assert normalise_dt(fixtures['dt'], fixtures['current_utc_date'], tolerance) == fixtures['dt']


def test_init():
    folder = "tests/temp"
    cities = ["london", "madrid"]
    csv_header = ['field1', 'field2']
    weather_resource_names = ['real', 'forecast']

    # before test
    if os.path.exists(folder):
        shutil.rmtree(folder)

    init(folder, csv_header, cities, weather_resource_names)

    with open(f"{folder}/real_london.csv") as f:
        assert f.readline() == "field1,field2\n"

    with open(f"{folder}/real_madrid.csv") as f:
        assert f.readline() == "field1,field2\n"

    with open(f"{folder}/forecast_london.csv") as f:
        assert f.readline() == "field1,field2\n"

    with open(f"{folder}/forecast_madrid.csv") as f:
        assert f.readline() == "field1,field2\n"

    # after test
    shutil.rmtree(folder)


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
