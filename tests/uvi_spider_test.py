import shutil
import os
import json
import time
from datetime import date
from unittest.mock import patch
import pytest
from requests.models import Response
from requests.exceptions import ConnectionError
import uvi_spider as rspider
from common import run_city
from datetime import timedelta, timezone, datetime, date

@pytest.fixture(scope='module')
def csv_folder():
    folder = "tests/temp"
    if not os.path.exists(folder):
        os.mkdir(folder)
    yield folder
    shutil.rmtree(folder)

@patch('common.requests')
def test_collect_uvi_data(req, csv_folder):    
    run_params = {
        'json_to_csv_f': rspider.transform_weather_data_to_csv,
        'csv_files_path': csv_folder,
        'csv_header': rspider.CSV_HEADER,
        'timezone': timezone(timedelta(hours=-3)),
        'weather_resource': rspider.WEATHER_RESOURCE,
        'weather_resource_url': 'weather_resource_url'
    }

    with open("tests/json_files/uvi.json", encoding='UTF-8') as f:
        json_body = json.loads(f.read())

    req.get.return_value.json.return_value = json_body

    run_city('london', run_params)
    time.sleep(1)

    req.get.assert_any_call("weather_resource_url", timeout=10)

    with open(f"{csv_folder}/uvi_london.csv", encoding='UTF-8') as f:
        rows = list(map(lambda row: row.split(','), f.readlines()))

    assert rows[0][0] == 'uvi'
    assert rows[0][1] == 'epochdt'
    assert rows[0][2] == 'isodt\n'
    assert rows[1][0] == '5.08'
    assert rows[1][1] == '1709294400'
    assert rows[1][2] == '2024-03-01T09:00:00-03:00\n'