from datetime import date
from roboclimate.open_weather.weather_spider import epoch_time


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
