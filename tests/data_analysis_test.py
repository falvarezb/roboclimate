import pandas as pd
import numpy as np
from roboclimate.data_analysis import forecast_precision, read_historical_data


def test_forecast_precision():
    """
        temp   dt              today       t5   t4   t3   t2   t1
    0   1      1575082800      2019-11-30  4.0  3    2.0  1    1.0
    1   2      1575093600      2019-11-30  3    1    4.0  5    3

                            temp
    2018-11-30 03:00:00     3   
    2018-11-30 06:00:00     5   
    """
    stub = {'temp': [1, 2], 'dt': [1575082800, 1575093600], 'today': ['2019-11-30']*2,
            't5': [4.0, 3], 't4': [3, 1], 't3': [2.0, 4.0], 't2': [1, 5], 't1': [1.0, 3]}
    stub_df = pd.DataFrame({'temp': [3, 5], 'dt': ['2018-11-30 03:00:00', '2018-11-30 06:00:00']})
    stub_df.set_index(pd.DatetimeIndex(stub_df['dt']), inplace=True)

    result = forecast_precision(pd.DataFrame(stub), stub_df)

    assert result['mae'] == [2, 1.5, 1.5, 1.5, 0.5]
    assert result['rmse'] == [2.23606797749979, 1.5811388300841898, 1.5811388300841898, 2.1213203435596424, 0.7071067811865476]
    assert result['medae'] == [2, 1.5, 1.5, 1.5, 0.5]
    assert result['mase'] == [1, 1, 2, 3, 1]
    assert result['mase1d'] == [np.nan, np.nan, np.nan, np.nan, np.nan]
    assert result['mase1y'] == [0.8, 0.6, 0.6, 0.6, 0.2]


def test_mase1y_29_feb_discarded():
    """
        temp   dt              today       t5   t4   t3   t2   t1
    0   1      1582858800      2020-02-28  4.0  3    2.0  1    1.0
    1   2      1582945200      2020-02-29  3    1    4.0  5    3

                            temp
    2019-02-28 03:00:00     3   
    2019-03-01 03:00:00     5  
    """
    stub = pd.DataFrame({'temp': [1, 2], 'dt': [1582858800, 1582945200], 'today': ['2020-02-28', '2020-02-29'],
            't5': [4.0, 3], 't4': [3, 1], 't3': [2.0, 4.0], 't2': [1, 5], 't1': [1.0, 3]})
    stub_df = pd.DataFrame({'temp': [3, 5], 'dt': ['2019-02-28 03:00:00', '2019-03-01 03:00:00']})
    stub_df.set_index(pd.DatetimeIndex(stub_df['dt']), inplace=True)

    result = forecast_precision(stub, stub_df)

    assert result['mase1y'] == [1.5, 1, 0.5, 0, 0]


def test_read_historical_data():
    """
        temp     dt_iso
         3       2018-02-27 00:00:00
         5       2019-03-28 03:00:00
    """

    stub_df = pd.DataFrame({'temp': [3, 5], 'dt_iso': ['2018-02-27 00:00:00', '2019-03-28 03:00:00']})

    result = read_historical_data(stub_df)

    assert result.shape[0] == 2
    assert result.iloc[0].temp == 3
    assert result.iloc[1].temp == 5


def test_remove_duplicates_from_historical_data():
    """
        temp     dt_iso
         3       2019-03-28 03:00:00
         5       2019-03-28 03:00:00
    """

    stub_df = pd.DataFrame({'temp': [3, 5], 'dt_iso': ['2019-03-28 03:00:00', '2019-03-28 03:00:00']})

    result = read_historical_data(stub_df)

    assert result.shape[0] == 1
    assert result.iloc[0].temp == 3