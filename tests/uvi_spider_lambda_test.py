import shutil
import os
import json
import time
from datetime import date
from unittest.mock import patch, call
import pytest
import uvi_spider_lambda as rspider
from datetime import date


tmp_folder = "tests/temp"

@pytest.fixture(scope='module')
def csv_folder():
    folder = tmp_folder
    if not os.path.exists(folder):
        os.mkdir(folder)
    yield folder
    shutil.rmtree(folder)


@patch('common.requests')
@patch('uvi_spider_lambda.get_yesterday')
@patch.dict('os.environ', {'OPEN_WEATHER_API': 'api_key', 'ROBOCLIMATE_CSV_FILES_PATH': tmp_folder})
def test_collect_uvi_data(get_yesterday, req, csv_folder):
    get_yesterday.return_value = date(2024, 3, 1)
    with open("tests/json_files/uvi.json", encoding='UTF-8') as f:
        json_body = json.loads(f.read())

    req.get.return_value.json.return_value = json_body
    rspider.handler(None, None)
    time.sleep(1)
    assert req.get.call_count == 10

    # checking a few calls
    req.get.assert_has_calls([
        call("https://api.openweathermap.org/data/3.0/onecall/timemachine?lat=51.5073219&lon=-0.1276474&units=metric&dt=1709294400&appid=api_key", timeout=10),
        call("https://api.openweathermap.org/data/3.0/onecall/timemachine?lat=40.4167047&lon=-3.7035825&units=metric&dt=1709290800&appid=api_key", timeout=10)
    ], any_order=True)

    assert len(os.listdir(csv_folder)) == 10

    # checking a few files
    with open(f"{csv_folder}/uvi_london.csv", encoding='UTF-8') as f:
        rows = list(map(lambda row: row.split(','), f.readlines()))

    assert rows[0][0] == 'uvi'
    assert rows[0][1] == 'epochdt'
    assert rows[0][2] == 'isodt\n'
    assert rows[1][0] == '5.08'
    assert rows[1][1] == '1709294400'
    assert rows[1][2] == '2024-03-01T12:00:00+00:00\n'

    with open(f"{csv_folder}/uvi_madrid.csv", encoding='UTF-8') as f:
        rows = list(map(lambda row: row.split(','), f.readlines()))

    assert rows[0][0] == 'uvi'
    assert rows[0][1] == 'epochdt'
    assert rows[0][2] == 'isodt\n'
    assert rows[1][0] == '5.08'
    assert rows[1][1] == '1709290800'
    assert rows[1][2] == '2024-03-01T12:00:00+01:00\n'
