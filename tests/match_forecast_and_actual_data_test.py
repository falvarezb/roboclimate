import pandas as pd


def match_forecast_and_actual_data(current_weather_df, forecast_df):
    headers = ['t5', 't4', 't3', 't2', 't1']
    df = pd.DataFrame()
    for row in current_weather_df.iterrows():
        temps = forecast_df[forecast_df['dt'] == row[1]['dt']].sort_values('today').T.loc['temp']        
        temps_df = pd.DataFrame(dict([(i, [j]) for (i, j) in zip(headers, temps)]), index=[row[0]])
        df = df.append(pd.DataFrame([row[1]]).join(temps_df))
    return df


def test_one_element_in_current_weather():
    current_weather_df = pd.DataFrame({'temp': [0.5], 'dt': [100], 'today': ['2019-11-30']})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3, 4], 'dt': [100]*5, 'today': ['2019-11-30', '2019-11-28', '2019-11-27', '2019-11-29', '2019-11-26']})

    result = match_forecast_and_actual_data(current_weather_df, forecast_df)
    assert result.equals(pd.DataFrame({'temp': [0.5], 'dt': [100], 'today': ['2019-11-30'], 't5': [4.0], 't4': [1.5], 't3': [2.0], 't2': [3.0], 't1': [1.0]}))


def test_two_elements_in_current_weather():
    current_weather_df = pd.DataFrame({'temp': [0.5, 0.6], 'dt': [100, 200], 'today': ['2019-11-30']*2})
    forecast_df = pd.DataFrame({'temp': [1, 2, 1.5, 3, 4, 5, 2, 4, 3, 1], 'dt': [100]*5 + [200]*5,'today': ['2019-11-30', '2019-11-28', '2019-11-27', '2019-11-29', '2019-11-26']*2})

    result = match_forecast_and_actual_data(current_weather_df, forecast_df)
    expected = pd.DataFrame({'temp': [0.5, 0.6], 'dt': [100, 200], 'today': ['2019-11-30']*2,'t5': [4.0, 1], 't4': [1.5, 4], 't3': [2.0, 2], 't2': [3.0, 3], 't1': [1.0, 5]})
    assert result.equals(expected)
