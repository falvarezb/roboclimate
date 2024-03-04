import shutil
import os
import json
import time
from datetime import date
from unittest.mock import patch
import pytest
from requests.models import Response
from requests.exceptions import ConnectionError
import weather_spider as rspider
import common


@pytest.fixture(scope='function')
def fixtures():
    return dict(
        dt=1575061195,  # Friday, 29 November 2019 20:59:55 UTC
        dt_on_the_dot=1575061200,  # Friday, 29 November 2019 21:00:00 UTC
        dt_higher_than_reference=1575061202,  # Friday, 29 November 2019 21:00:02 UTC
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
    assert rspider.epoch_time(d) == {"0": 1574985600.0,
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


@patch('weather_spider.epoch_time')
def test_normalise_dt_success(mock_epoch_time, fixtures):
    mock_epoch_time.side_effect = epoch_time_side_effect_gen(fixtures['current_utc_date'])
    tolerance = {'positive_tolerance': 10, 'negative_tolerance': 5}
    assert rspider.normalise_datetime(fixtures['dt'], fixtures['current_utc_date'], tolerance) == 1575061200.0


@patch('weather_spider.epoch_time')
def test_normalise_dt_success_when_dt_on_the_dot(mock_epoch_time, fixtures):
    mock_epoch_time.side_effect = epoch_time_side_effect_gen(fixtures['current_utc_date'])
    tolerance = {'positive_tolerance': 10, 'negative_tolerance': 5}
    assert rspider.normalise_datetime(fixtures['dt_on_the_dot'], fixtures['current_utc_date'], tolerance) == 1575061200.0


@patch('weather_spider.epoch_time')
def test_normalise_dt_success_when_dt_higher_than_reference(mock_epoch_time, fixtures):
    mock_epoch_time.side_effect = epoch_time_side_effect_gen(fixtures['current_utc_date'])
    tolerance = {'positive_tolerance': 10, 'negative_tolerance': 5}
    assert rspider.normalise_datetime(fixtures['dt_higher_than_reference'], fixtures['current_utc_date'], tolerance) == 1575061200.0


@patch('weather_spider.epoch_time')
def test_normalise_dt_fail(mock_epoch_time, fixtures):
    mock_epoch_time.side_effect = epoch_time_side_effect_gen(fixtures['current_utc_date'])
    tolerance = {'positive_tolerance': 1, 'negative_tolerance': 5}
    assert rspider.normalise_datetime(fixtures['dt'], fixtures['current_utc_date'], tolerance) == fixtures['dt']


@patch('common.requests')
def test_collect_current_weather_data(req, csv_folder):
    run_params = {
        'utcnow_date': date(2017, 1, 30),
        'tolerance': {'positive_tolerance': 60, 'negative_tolerance': 5},
        'json_to_csv_f': rspider.transform_weather_data_to_csv,
        'csv_files_path': csv_folder,
        'csv_header': 'temp,pressure,humidity,wind_speed,wind_deg,dt,today'
    }

    with open("tests/json_files/weather.json", encoding='UTF-8') as f:
        json_body = json.loads(f.read())

    req.get.return_value.json.return_value = json_body

    rspider.run_city('london', rspider.WEATHER_RESOURCE, 'weather_resource_url', run_params)
    time.sleep(1)

    req.get.assert_any_call("weather_resource_url", timeout=10)

    with open(f"{csv_folder}/weather_london.csv", encoding='UTF-8') as f:
        rows = list(map(lambda row: row.split(','), f.readlines()))

    assert rows[1][0] == '300.15'
    assert rows[1][1] == '1007'
    assert rows[1][2] == '74'
    assert rows[1][3] == '3.6'
    assert rows[1][4] == '160'
    assert rows[1][5] == '1485790200'
    assert rows[1][6] == '2017-01-30\n'


@patch('common.read_remote_resource')
@patch('common.logger')
def test_log_error_when_fetching_data(logger, read_remote_resource):
    try:
        read_remote_resource.side_effect = ConnectionError('error')
        common.fetch_data('url')
    except Exception:
        assert logger.error.call_args[0][0] == "Error '%s' while reading '%s'"
        assert logger.error.call_args[0][1].args[0] == 'error'
        assert logger.error.call_args[0][2] == "url"


@patch('common.logger')
def test_log_error_when_transforming_data(logger):
    try:
        response = Response()
        response.status_code = 200
        response._content = b'I am not a json'
        common.transform_data(response, None)
    except Exception:
        assert logger.error.call_args[0][0] == "Error '%s' while parsing '%s'"
        assert logger.error.call_args[0][1].args[0] == 'Expecting value: line 1 column 1 (char 0)'
        assert logger.error.call_args[0][2] == 'I am not a json'


@patch('common.fetch_data')
@patch('common.logger')
def test_log_error_when_running_city(logger, fetch_data):
    fetch_data.side_effect = Exception('error')
    rspider.run_city('city name', rspider.WEATHER_RESOURCE, 'weather_resource_url', {})
    assert logger.error.call_args[0][0] == "Error '%s' while processing '%s'"
    assert logger.error.call_args[0][1].args[0] == 'error'
    assert logger.error.call_args[0][2] == "city name"
