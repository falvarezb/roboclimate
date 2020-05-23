import pandas as pd
from roboclimate.data_analysis import join_true_temp_and_forecast


def test_one_element_in_current_weather():
    current_weather_df = pd.DataFrame({'temp': [0.5], 'dt': [100], 'today': ['2019-11-30']})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3, 4], 'dt': [100]*5, 'today': ['2019-11-30', '2019-11-28', '2019-11-27', '2019-11-29', '2019-11-26']})

    result = join_true_temp_and_forecast(current_weather_df, forecast_df)
    assert result.equals(pd.DataFrame({'temp': [0.5], 'dt': [100], 'today': ['2019-11-30'], 't5': [4.0], 't4': [1.5], 't3': [2.0], 't2': [3.0], 't1': [1.0]}))


def test_two_elements_in_current_weather():
    current_weather_df = pd.DataFrame({'temp': [0.5, 0.6], 'dt': [100, 200], 'today': ['2019-11-30']*2})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3, 4, 5, 2, 4, 3, 1], 'dt': [100]*5 + [200]*5,
                                'today': ['2019-11-30', '2019-11-28', '2019-11-27', '2019-11-29', '2019-11-26']*2})

    result = join_true_temp_and_forecast(current_weather_df, forecast_df)
    expected = pd.DataFrame({'temp': [0.5, 0.6], 'dt': [100, 200], 'today': ['2019-11-30']*2,
                             't5': [4.0, 1], 't4': [1.5, 4], 't3': [2.0, 2], 't2': [3.0, 3], 't1': [1.0, 5]})

    assert result.equals(expected)


def test_record_discarded_when_missing_temperatures():
    current_weather_df = pd.DataFrame({'temp': [0.5], 'dt': [100], 'today': ['2019-11-30']})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3], 'dt': [100]*4, 'today': ['2019-11-30', '2019-11-28', '2019-11-29', '2019-11-26']})

    result = join_true_temp_and_forecast(current_weather_df, forecast_df)
    print(result)
    assert result.equals(pd.DataFrame())

