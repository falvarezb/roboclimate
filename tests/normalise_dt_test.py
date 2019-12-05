from datetime import date
from unittest.mock import Mock
from roboclimate.open_weather.weather_spider import normalise_dt


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

epoch_time = Mock(side_effect = side_effect)


def test_normalise_dt_success():
    tolerance = 10
    assert normalise_dt(dt, current_utc_date, tolerance) == 1575061200


def test_normalise_dt_fail():
    tolerance = 1
    assert normalise_dt(dt, current_utc_date, tolerance) == dt
