import pandas as pd
from datetime import datetime
from roboclimate.util import one_year_ago, remove_29_feb, n_years_ago

def test_one_year_ago():
    assert one_year_ago(datetime(2019, 12, 20, 5, 0, 0)) == datetime(2018, 12, 20, 5, 0, 0)


def test_one_year_ago_leap_year():
    assert one_year_ago(datetime(2020, 2, 29, 5, 0, 0)) is None

def test_n_years_ago():
    assert n_years_ago(datetime(2019, 12, 20, 5, 0, 0), 3) == datetime(2016, 12, 20, 5, 0, 0)


def test_n_years_ago_leap_year():
    assert n_years_ago(datetime(2020, 2, 29, 5, 0, 0), 3) is None


def test_remove_29_feb():
    """
        temp   dt              today       t5   t4   t3   t2   t1
    0   1      1582858800      2020-02-28  4.0  3    2.0  1    1.0
    1   2      1582945200      2020-02-29  3    1    4.0  5    3
 
    """

    df = pd.DataFrame({'temp': [1, 2], 'dt': [1582858800, 1582945200], 'today': ['2020-02-28', '2020-02-29'],
            't5': [4.0, 3], 't4': [3, 1], 't3': [2.0, 4.0], 't2': [1, 5], 't1': [1.0, 3]})

    df_without_29_feb = remove_29_feb(df)
    assert df_without_29_feb.shape[0] == 1
    assert df_without_29_feb.iloc[0].dt_iso.day == 28
    