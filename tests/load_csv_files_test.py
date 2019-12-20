import pandas as pd
from roboclimate.data_analysis import load_data, load_forecast_temp_data

def test_load_true_temp():
    data = load_data('tests/csv_files/weather.csv')
    expected_df = pd.DataFrame({'temp': [10, 20], 'dt': [100, 200], 'today': ['2019-11-26', '2019-11-27']})
    assert data.equals(expected_df)

def test_load_forecast_temp():
    data = load_data('tests/csv_files/forecast.csv')
    expected_df = pd.DataFrame({'temp': [10, 20], 'dt': [100, 200], 'today': ['2019-11-26', '2019-11-27']})
    assert data.equals(expected_df)
