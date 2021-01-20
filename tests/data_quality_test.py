from unittest.mock import Mock, patch
import pandas as pd
import roboclimate.data_quality as rdq


@patch('roboclimate.data_quality.load_csv_files')
@patch('roboclimate.data_quality.dts')
def test_missing_temps(dts_mock, load_csv_files_mock):
    load_csv_files_mock.return_value = {"true_temp_df": pd.DataFrame({'temp': [1, 2, 3], 'dt': [100, 200, 300]})}
    dts_mock.return_value = pd.DataFrame({'dt': [100, 200, 300, 400]})
    city = Mock()

    result = rdq.missing_temps(city)
    assert len(result) == 1
    assert result.iloc[0]['dt'] == 400


@patch('roboclimate.data_quality.load_csv_files')
@patch('roboclimate.data_quality.dts')
def test_unexpected_temps(dts_mock, load_csv_files_mock):
    load_csv_files_mock.return_value = {"true_temp_df": pd.DataFrame({'temp': [1, 2, 3], 'dt': [100, 200, 301]})}
    dts_mock.return_value = pd.DataFrame({'dt': [100, 200, 300]})
    city = Mock()

    result = rdq.unexpected_temps(city)
    assert len(result) == 1
    assert result.iloc[0]['temp'] == 3
    assert result.iloc[0]['dt'] == 301


@patch('roboclimate.data_quality.load_csv_files')
@patch('roboclimate.data_quality.dts')
def test_temps_without_five_forecasts(dts_mock, load_csv_files_mock):
    load_csv_files_mock.return_value = {"join_data_df": pd.DataFrame({'temp': [1, 2, 3], 'dt': [100, 200, 300]})}
    dts_mock.return_value = pd.DataFrame({'dt': [100, 200, 300, 400]})
    city = Mock()

    result = rdq.temps_without_five_forecasts(city)
    assert len(result) == 1
    assert result.iloc[0]['dt'] == 400


@patch('roboclimate.data_quality.load_csv_files')
@patch('roboclimate.data_quality.dts')
def test_missing_forecasts(dts_mock, load_csv_files_mock):
    load_csv_files_mock.return_value = {"forecast_temp_df": pd.DataFrame({'today': ['2020-12-01', '2020-12-02']})}
    dts_mock.return_value = pd.DataFrame({'today': ['2020-12-01', '2020-12-02', '2020-12-03']})
    city = Mock()

    result = rdq.missing_forecasts(city)
    assert len(result) == 1
    assert result.iloc[0]['today'] == '2020-12-03'
