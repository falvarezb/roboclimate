import pandas as pd
from roboclimate.data_analysis import join_actual_values_and_forecast
import roboclimate.data_analysis as rda
import numpy as np


def test_forecast_precision():
    """
        temp   dt              today       t5   t4   t3   t2   t1
    0   1      1575082800      2019-11-30  4.0  3    2.0  1    1.0
    1   2      1575093600      2019-11-30  3    1    4.0  5    3
    """
    joined_data = pd.DataFrame({'temp': [1, 2], 'dt': [1575082800, 1575093600], 'today': ['2019-11-30'] * 2,
                                't5': [4.0, 3], 't4': [3, 1], 't3': [2.0, 4.0], 't2': [1, 5], 't1': [1.0, 3]})

    result = rda.forecast_precision(joined_data, 'temp')

    assert result['mae'] == [2, 1.5, 1.5, 1.5, 0.5]
    assert result['rmse'] == [2.23606797749979, 1.5811388300841898, 1.5811388300841898, 2.1213203435596424, 0.7071067811865476]
    assert result['medae'] == [2, 1.5, 1.5, 1.5, 0.5]
    assert 'mase' in result


def test_join_one_element_in_current_weather():
    """
        temp   pressure     dt       today
    0   0.5    1020         100      2019-11-30


        temp   pressure     dt       today
    0   1      1000         100      2019-11-29
    1   2      990          100      2019-11-27
    2   1.5    1010         100      2019-11-26
    3   3      1000         100      2019-11-28
    4   4      1020         100      2019-11-25

    """
    current_weather_df = pd.DataFrame({'temp': [0.5], 'pressure': [1020], 'dt': [100], 'today': ['2019-11-30']})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3, 4], 'pressure': [1000, 990, 1010, 1000, 1020], 'dt': [100] *
                               5, 'today': ['2019-11-29', '2019-11-27', '2019-11-26', '2019-11-28', '2019-11-25']})

    result = join_actual_values_and_forecast(current_weather_df, forecast_df)
    assert result['temp'].equals(pd.DataFrame({'temp': [0.5], 'dt': [100], 'today': ['2019-11-30'],
                                 't5': [4.0], 't4': [1.5], 't3': [2.0], 't2': [3.0], 't1': [1.0]}))
    assert result['pressure'].equals(pd.DataFrame({'pressure': [1020], 'dt': [100], 'today': ['2019-11-30'],
                                     't5': [1020], 't4': [1010], 't3': [990], 't2': [1000], 't1': [1000]}))


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
    10  2.1    300      2019-11-29
    11  2.2    300      2019-11-27
    12  2.3    300      2019-11-26
    13  2.4    300      2019-11-28
    14  2.5    300      2019-11-25
    """
    current_weather_df = pd.DataFrame({'temp': [0.5, 0.6], 'dt': [100, 200], 'today': ['2019-11-30'] * 2})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3, 4, 5, 2, 4, 3, 1, 2.1, 2.2, 2.3, 2.4, 2.5], 'dt': [100] * 5 + [200] * 5 + [300] * 5,
                                'today': ['2019-11-30', '2019-11-28', '2019-11-27', '2019-11-29', '2019-11-26'] * 3})

    result = join_actual_values_and_forecast(current_weather_df, forecast_df)
    expected = pd.DataFrame({'temp': [0.5, 0.6], 'dt': [100, 200], 'today': ['2019-11-30'] * 2,
                             't5': [4.0, 1], 't4': [1.5, 4], 't3': [2.0, 2], 't2': [3.0, 3], 't1': [1.0, 5]})

    assert result['temp'].equals(expected)


def test_join_record_discarded_when_missing_forecasts():
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
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3], 'dt': [100] * 4, 'today': ['2019-11-30', '2019-11-28', '2019-11-29', '2019-11-26']})

    result = join_actual_values_and_forecast(current_weather_df, forecast_df)
    assert result['temp'].equals(pd.DataFrame())


def test_join_record_discarded_when_has_empty_value():
    """
        temp   dt       today
    0    nan   100      2019-11-30


        temp   dt       today
    0   1      100      2019-11-30
    1   2      100      2019-11-28
    2   1.5    100      2019-11-29
    3   3      100      2019-11-26
    4   3      100      2019-11-27
    """
    current_weather_df = pd.DataFrame({'temp': [np.nan], 'dt': [100], 'today': ['2019-11-30']})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3], 'dt': [100] * 4, 'today': ['2019-11-30', '2019-11-28', '2019-11-29', '2019-11-26']})

    result = join_actual_values_and_forecast(current_weather_df, forecast_df)
    assert result['temp'].equals(pd.DataFrame())
