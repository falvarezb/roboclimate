import pandas as pd
import numpy as np
from roboclimate.data_analysis import forecast_precision


def test_forecast_precision():
    """
            temp   dt       today       t5   t4   t3   t2   t1
        0   1      100      2019-11-30  4.0  3    2.0  1    1.0
        1   2      200      2019-11-30  3    1    4.0  5    3
    """

    data = pd.DataFrame({'temp': [1, 2], 'dt': [100, 200], 'today': ['2019-11-30']*2,
                         't5': [4.0, 3], 't4': [3, 1], 't3': [2.0, 4.0], 't2': [1, 5], 't1': [1.0, 3]})

    result = forecast_precision(data)

    assert result['mae'] == [2, 1.5, 1.5, 1.5, 0.5]
    assert result['rmse'] == [2.23606797749979, 1.5811388300841898, 1.5811388300841898, 2.1213203435596424, 0.7071067811865476]
    assert result['medae'] == [2, 1.5, 1.5, 1.5, 0.5]
    assert result['mase'] == [1, 1, 2, 3, 1]
    assert result['mase1d'] == [np.nan, np.nan, np.nan, np.nan, np.nan]
