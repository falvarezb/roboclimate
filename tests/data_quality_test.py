from unittest.mock import Mock, patch, ANY
import datetime as dt
import pandas as pd
import roboclimate.data_quality as rdq


@patch('roboclimate.data_quality.load_weather_file')
@patch('roboclimate.data_quality.dts')
def test_missing_weather_datapoints(dts_mock, load_weather_file_mock):
    load_weather_file_mock.return_value = pd.DataFrame({'temp': [1, 2, 3], 'dt': [100, 200, 300]})
    dts_mock.return_value = pd.DataFrame({'dt': [100, 200, 300, 400]})
    city = Mock()

    result = rdq.missing_weather_datapoints(city)
    assert len(result) == 1
    assert result.iloc[0]['dt'] == 400


@patch('roboclimate.data_quality.load_weather_file')
@patch('roboclimate.data_quality.dts')
def test_missing_weather_datapoints_without_dates(dts_mock, load_weather_file_mock):
    load_weather_file_mock.return_value = pd.DataFrame({'temp': [1, 2, 3], 'dt': [100, 200, 300]})
    dts_mock.return_value = pd.DataFrame({'dt': [100, 200, 300, 400]})
    start_dt = dt.datetime(2020, 11, 28, 3, 0, 0, tzinfo=dt.timezone.utc)
    city = rdq.City(1, 'xx', start_dt)

    rdq.missing_weather_datapoints(city)
    dts_mock.assert_called_once_with(start_dt, ANY)


@patch('roboclimate.data_quality.load_weather_file')
@patch('roboclimate.data_quality.dts')
def test_missing_weather_datapoints_with_dates(dts_mock, load_weather_file_mock):
    load_weather_file_mock.return_value = pd.DataFrame({'temp': [1, 2, 3], 'dt': [100, 200, 300]})
    dts_mock.return_value = pd.DataFrame({'dt': [100, 200, 300, 400]})
    start_dt = dt.datetime(2020, 11, 28, 3, 0, 0, tzinfo=dt.timezone.utc)
    end_dt = dt.datetime(2020, 11, 28, 4, 0, 0, tzinfo=dt.timezone.utc)
    city = Mock()

    rdq.missing_weather_datapoints(city, start_dt, end_dt)
    dts_mock.assert_called_once_with(start_dt, end_dt)


@patch('roboclimate.data_quality.load_weather_file')
@patch('roboclimate.data_quality.dts')
def test_unexpected_weather_datapoints(dts_mock, load_weather_file_mock):
    start_date = dt.datetime(2023, 3, 16, 9, 0, 0, tzinfo=dt.timezone.utc)
    # 1679043600 = 2023-03-17 09:00:00
    load_weather_file_mock.return_value = pd.DataFrame({'temp': [1, 2, 3], 'dt': [100, 1679043600, 1679043601]})
    dts_mock.return_value = pd.DataFrame({'dt': [1, 2, 1679043600]})
    city = Mock()

    result = rdq.unexpected_weather_datapoints(city, start_date)
    assert len(result) == 1
    assert result.iloc[0]['temp'] == 3
    assert result.iloc[0]['dt'] == 1679043601


@patch('roboclimate.data_quality.load_csv_files')
@patch('roboclimate.data_quality.dts')
def test_temps_without_five_forecasts(dts_mock, load_csv_files_mock):
    load_csv_files_mock.return_value = {"join_data_df": pd.DataFrame({'temp': [1, 2, 3], 'dt': [100, 200, 300]})}
    dts_mock.return_value = pd.DataFrame({'dt': [100, 200, 300, 400]})
    city = Mock()

    result = rdq.weather_datapoints_without_five_forecasts(city, 'temp')
    assert len(result) == 1
    assert result.iloc[0]['dt'] == 400


@patch('roboclimate.data_quality.load_forecast_file')
@patch('roboclimate.data_quality.dts')
def test_missing_forecast_datapoints(dts_mock, load_forecast_file_mock):
    load_forecast_file_mock.return_value = pd.DataFrame({'today': ['2020-12-01', '2020-12-02']})
    dts_mock.return_value = pd.DataFrame({'today': ['2020-12-01', '2020-12-02', '2020-12-03']})
    city = Mock()

    result = rdq.missing_forecast_datapoints(city)
    assert len(result) == 1
    assert result[0] == '2020-12-03'
