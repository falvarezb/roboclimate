import shutil
import os
from datetime import date
from unittest.mock import Mock
from roboclimate.weather_spider import epoch_time, normalise_dt, init


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


# fixtures
dt = 1575061195  # Friday, 29 November 2019 20:59:55 UTC
current_utc_date = date(2019, 11, 29)


def side_effect(value):
    if value == current_utc_date:
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


epoch_time = Mock(side_effect=side_effect)


def test_normalise_dt_success():
    tolerance = 10
    assert normalise_dt(dt, current_utc_date, tolerance) == 1575061200


def test_normalise_dt_fail():
    tolerance = 1
    assert normalise_dt(dt, current_utc_date, tolerance) == dt


def test_init():
    folder = "tests/myfolder"
    cities = ["london", "madrid"]
    csv_header = ['field1', 'field2']
    weather_resource_names = ['real', 'forecast']

    #before test
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

    #after test
    shutil.rmtree(folder)
