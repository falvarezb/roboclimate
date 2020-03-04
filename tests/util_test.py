from roboclimate.util import oneYearAgo

def test_calculate_time_one_year_ago():
    date = '2019-12-20 05:00:00'
    assert oneYearAgo(date) == '2018-12-20 05:00:00'