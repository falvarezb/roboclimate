import pandas as pd
import numpy as np
from roboclimate.metrics import mean_absolute_scaled_error_revisited as maser, mean_absolute_scaled_error_1year_revisited as maser1y
from roboclimate.config import day_factor


def test_maser():
    """
         temp   dt              today       t5   t4   t3   t2   t1
    00   1      1575082800      2019-11-30  4.0  3    2.0  1    1.0
    01   2      1575093600      2019-11-30  3    1    4.0  5    3
    02   1      1575104400      2019-11-30  4.0  3    2.0  1    1.0
    03   2      1575115200      2019-11-30  3    1    4.0  5    3
    04   1      1575126000      2019-11-30  4.0  3    2.0  1    1.0
    05   2      1575136800      2019-11-30  3    1    4.0  5    3
    06   1      1575147600      2019-11-30  4.0  3    2.0  1    1.0
    07   2      1575158400      2019-12-01  3    1    4.0  5    3
    08   2      1575169200      2019-12-01  4.0  3    2.0  1    1.0
    09   2      1575180000      2019-12-01  4.0  3    2.0  1    1.0
    10   2      1575190800      2019-12-01  4.0  3    2.0  1    1.0
    11   2      1575201600      2019-12-01  4.0  3    2.0  1    1.0
    12   2      1575212400      2019-12-01  4.0  3    2.0  1    1.0
    13   2      1575223200      2019-12-01  4.0  3    2.0  1    1.0
    14   2      1575234000      2019-12-01  4.0  3    2.0  1    1.0
    15   2      1575244800      2019-12-02  4.0  3    2.0  1    1.0
    16   2      1575255600      2019-12-02  4.0  3    2.0  1    1.0
    """
    joined_data = pd.DataFrame({'temp': [1, 2, 1, 2, 1, 2, 1, 2, 2] + [2] * day_factor,
                                'dt': [1575082800, 1575093600, 1575104400, 1575115200, 1575126000, 1575136800, 1575147600, 1575158400, 1575169200, 1575180000, 1575190800, 1575201600, 1575212400, 1575223200, 1575234000, 1575244800, 1575255600],
                                'today': ['2019-11-30'] * 7 + ['2019-12-01'] * day_factor + ['2019-12-02'] * 2,
                                't5': [4.0, 3, 4.0, 3, 4.0, 3, 4.0, 3, 4.0] + [4.0] * day_factor,
                                't4': [3, 1, 3, 1, 3, 1, 3, 1, 3] + [3] * day_factor,
                                't3': [2.0, 4.0, 2.0, 4.0, 2.0, 4.0, 2.0, 4.0, 2.0] + [2.0] * day_factor,
                                't2': [1, 5, 1, 5, 1, 5, 1, 5, 1] + [1] * day_factor,
                                't1': [1.0, 3, 1.0, 3, 1.0, 3, 1.0, 3, 1.0] + [1.0] * day_factor})

    assert maser(joined_data) == [np.nan, np.nan, np.nan, 1, 2.25]


def test_maser_1y():
    leap_year_temp = [1] * (59 * day_factor) + [5] * day_factor + [1] * (306 * day_factor)
    year2_temp = [2] * (60 * day_factor)
    total_data_points = len(leap_year_temp) + len(year2_temp)
    joined_data = pd.DataFrame({'temp': leap_year_temp + year2_temp,
                                'dt': [1575082800] * (59 * day_factor) + [1582934400, 1582945200, 1582956000, 1582966800, 1582977600, 1582988400, 1582999200, 1583010000] + [1575082800] * (366 * day_factor),
                                'today': ['yyyy-mm-dd'] * total_data_points,
                                't5': [1] * total_data_points,
                                't4': [1] * total_data_points,
                                't3': [1] * total_data_points,
                                't2': [1] * total_data_points,
                                't1': [1] * total_data_points})

    assert maser1y(joined_data) == [1, 1, 1, 1, 1]
