import pandas as pd
import numpy as np
from roboclimate.data_analysis import forecast_precision, read_historical_data, load_data, join_true_temp_and_forecast


def test_load_true_temp():
    data = load_data('tests/csv_files/weather.csv')
    expected_df = pd.DataFrame({'temp': [10, 20], 'dt': [100, 200], 'today': ['2019-11-26', '2019-11-27']})
    assert data.equals(expected_df)


def test_load_forecast_temp():
    data = load_data('tests/csv_files/forecast.csv')
    expected_df = pd.DataFrame({'temp': [10, 20], 'dt': [100, 200], 'today': ['2019-11-26', '2019-11-27']})
    assert data.equals(expected_df)


def test_read_historical_data():
    result = read_historical_data("tests/csv_files/historical_data.csv")

    assert result.shape[0] == 2
    assert result.iloc[0].temp == 3
    assert result.iloc[1].temp == 5


def test_remove_duplicates_from_historical_data():
    historical_data = read_historical_data("tests/csv_files/historical_data_duplicates.csv")

    assert historical_data.shape[0] == 1
    assert historical_data.iloc[0].temp == 3


def test_forecast_precision():
    """
        temp   dt              today       t5   t4   t3   t2   t1
    0   1      1575082800      2019-11-30  4.0  3    2.0  1    1.0
    1   2      1575093600      2019-11-30  3    1    4.0  5    3  
    """
    joined_data = pd.DataFrame({'temp': [1, 2], 'dt': [1575082800, 1575093600], 'today': ['2019-11-30']*2,
                                't5': [4.0, 3], 't4': [3, 1], 't3': [2.0, 4.0], 't2': [1, 5], 't1': [1.0, 3]})
    historical_data = read_historical_data("tests/csv_files/historical_data.csv")

    result = forecast_precision(joined_data, historical_data)

    assert result['mae'] == [2, 1.5, 1.5, 1.5, 0.5]
    assert result['rmse'] == [2.23606797749979, 1.5811388300841898, 1.5811388300841898, 2.1213203435596424, 0.7071067811865476]
    assert result['medae'] == [2, 1.5, 1.5, 1.5, 0.5]
    assert result['mase'] == [1, 1, 2, 3, 1]
    assert result['mase1d'] == [np.nan, np.nan, np.nan, np.nan, np.nan]
    assert result['mase1y'] == [0.8, 0.6, 0.6, 0.6, 0.2]


def test_29_feb_discarded_when_calculating_mase1y():
    """
        temp   dt              today       t5   t4   t3   t2   t1
    0   1      1582858800      2020-02-28  4.0  3    2.0  1    1.0
    1   2      1582945200      2020-02-29  3    1    4.0  5    3
    """
    joined_data = pd.DataFrame({'temp': [1, 2], 'dt': [1582858800, 1582945200], 'today': ['2020-02-28', '2020-02-29'],
                                't5': [4.0, 3], 't4': [3, 1], 't3': [2.0, 4.0], 't2': [1, 5], 't1': [1.0, 3]})
    historical_data = read_historical_data("tests/csv_files/historical_data_29_feb.csv")

    result = forecast_precision(joined_data, historical_data)

    assert result['mase1y'] == [1.5, 1, 0.5, 0, 0]


def test_join_one_element_in_current_weather():
    """
        temp   dt       today       
    0   0.5    100      2019-11-30 


        temp   dt       today       
    0   1      100      2019-11-30
    1   2      100      2019-11-28
    2   1.5    100      2019-11-27
    3   3      100      2019-11-29
    4   4      100      2019-11-26  

    """
    current_weather_df = pd.DataFrame({'temp': [0.5], 'dt': [100], 'today': ['2019-11-30']})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3, 4], 'dt': [100]*5, 'today': ['2019-11-30', '2019-11-28', '2019-11-27', '2019-11-29', '2019-11-26']})

    result = join_true_temp_and_forecast(current_weather_df, forecast_df)
    assert result.equals(pd.DataFrame({'temp': [0.5], 'dt': [100], 'today': ['2019-11-30'], 't5': [4.0], 't4': [1.5], 't3': [2.0], 't2': [3.0], 't1': [1.0]}))


def test_join_two_elements_in_current_weather():
    """
        temp   dt       today       
    0   0.5    100      2019-11-30
    1   0.6    200      2019-11-30


        temp   dt       today       
    0   1      100      2019-11-30
    1   2      100      2019-11-28
    2   1.5    100      2019-11-27
    3   3      100      2019-11-29
    4   4      100      2019-11-26
    5   5      200      2019-11-30
    6   2      200      2019-11-28
    7   4      200      2019-11-27
    8   3      200      2019-11-29
    9   1      200      2019-11-26
    """
    current_weather_df = pd.DataFrame({'temp': [0.5, 0.6], 'dt': [100, 200], 'today': ['2019-11-30']*2})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3, 4, 5, 2, 4, 3, 1], 'dt': [100]*5 + [200]*5,
                                'today': ['2019-11-30', '2019-11-28', '2019-11-27', '2019-11-29', '2019-11-26']*2})

    result = join_true_temp_and_forecast(current_weather_df, forecast_df)
    expected = pd.DataFrame({'temp': [0.5, 0.6], 'dt': [100, 200], 'today': ['2019-11-30']*2,
                             't5': [4.0, 1], 't4': [1.5, 4], 't3': [2.0, 2], 't2': [3.0, 3], 't1': [1.0, 5]})

    assert result.equals(expected)


def test_join_record_discarded_when_missing_temperatures():
    """
        temp   dt       today       
    0   0.5    100      2019-11-30 


        temp   dt       today       
    0   1      100      2019-11-30
    1   2      100      2019-11-28
    2   1.5    100      2019-11-29
    3   3      100      2019-11-26
    """
    current_weather_df = pd.DataFrame({'temp': [0.5], 'dt': [100], 'today': ['2019-11-30']})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3], 'dt': [100]*4, 'today': ['2019-11-30', '2019-11-28', '2019-11-29', '2019-11-26']})

    result = join_true_temp_and_forecast(current_weather_df, forecast_df)
    print(result)
    assert result.equals(pd.DataFrame())
