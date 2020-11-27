from datetime import datetime
import pandas as pd
from roboclimate.util import one_year_ago, n_years_ago
import roboclimate.util as rutil


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

    df_without_29_feb = rutil.remove_29_feb(df)
    assert df_without_29_feb.shape[0] == 1
    assert df_without_29_feb.iloc[0].dt_iso.day == 28


def test_read_historical_data():
    result = rutil.read_historical_data("tests/csv_files/historical_data.csv")

    assert result.shape[0] == 2
    assert result.iloc[0].temp == 3
    assert result.iloc[1].temp == 5


def test_remove_duplicates_from_historical_data():
    historical_data = rutil.read_historical_data("tests/csv_files/historical_data_duplicates.csv")

    assert historical_data.shape[0] == 1
    assert historical_data.iloc[0].temp == 3
