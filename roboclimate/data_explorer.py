"""Data Explorer

    Functions to explore captured data:  missing values, data intervals, etc
"""


import datetime as dt
import pandas as pd
import roboclimate.config as rconf
from roboclimate.config import City
import roboclimate.util as rutil


def load_weather_file(city: City):
    return pd.read_csv(f"csv_files/weather_{city.name}.csv", dtype={'dt': 'int64'})


def load_forecast_file(city: City):
    return pd.read_csv(f"csv_files/forecast_{city.name}.csv", dtype={'dt': 'int64'})


def load_csv_files(city: City, weather_variable: str) -> dict:
    actual_value_df = pd.read_csv(f"csv_files/weather_{city.name}.csv", usecols=[weather_variable, 'dt', 'today'], dtype={'dt': 'int64'})
    forecast_value_df = pd.read_csv(f"csv_files/forecast_{city.name}.csv", usecols=[weather_variable, 'dt', 'today'], dtype={'dt': 'int64'})
    join_data_df = pd.read_csv(f"csv_files/{weather_variable}/join_{city.name}.csv", usecols=[weather_variable, 'dt', 'today', 't5', 't4', 't3', 't2', 't1'])
    metrics_df = pd.read_csv(f"csv_files/{weather_variable}/metrics_{city.name}.csv")
    return {"true_temp_df": actual_value_df, "forecast_temp_df": forecast_value_df, "join_data_df": join_data_df, "metrics_df": metrics_df}


def dts(start: dt.datetime, end: dt.datetime = dt.datetime.now()):
    """
    List of datetimes for which weather data should be recorded
    In theory, the times 0,3,6,9,12,15,18,21 of each day
    """
    return pd.DataFrame(data=rutil.date_and_timestamp(start, end), columns=['dt', 'today'])


def missing_weather_datapoints(city: City, start_dt: dt.datetime = None, end_dt: dt.datetime = dt.datetime.now()) -> pd.DataFrame:
    """
    Finds datetimes when no weather data was recorded    
    """
    start_dt = start_dt if start_dt else city.firstMeasurement
    df = load_weather_file(city)
    merged = df.merge(dts(start_dt, end_dt), how='right', on='dt', indicator=True)
    return merged[merged['_merge'] == 'right_only']  # .groupby('today_y').count()['_merge']


def unexpected_weather_datapoints(city: City, start_dt: dt.datetime = None, end_dt: dt.datetime = dt.datetime.now()) -> pd.DataFrame:
    """
    Finds weather data recorded at dts other than the times 0,3,6,9,12,15,18,21 of each day    
    """
    start_dt = start_dt if start_dt else city.firstMeasurement
    start_dt_ts = start_dt.timestamp()
    end_dt_ts = end_dt.timestamp()
    df = load_weather_file(city)
    df = df[(df['dt'] >= start_dt_ts) & (df['dt'] < end_dt_ts)]
    merged = df.merge(dts(start_dt, end_dt), how='left', on='dt', indicator=True)
    return merged[merged['_merge'] == 'left_only']  # .groupby('today_x').count()['_merge']


def weather_datapoints_without_five_forecasts(city: City, weather_variable: str, start_dt: dt.datetime = None, end_dt: dt.datetime = dt.datetime.now()) -> pd.DataFrame:
    """
    Finds dts for which not all five forecasts were made

    Given that dts without the five forecasts are excluded when constructing 'join_data_df',
    said dts can be found by doing the right join between the DataFrames: 'join_data_df' and 'dts'

    So based on the above implementation, in reality this function returns missing weather datapoints + weather datapoints without 5 forecasts
    """
    start_dt = start_dt if start_dt else city.firstMeasurement
    files = load_csv_files(city, weather_variable)
    merged = files['join_data_df'].merge(dts(start_dt, end_dt), how='right', on='dt', indicator=True)
    return merged[merged['_merge'] == 'right_only']  # .groupby('today_y').count()['_merge']


def missing_forecast_datapoints(city: City, start_dt: dt.datetime = None, end_dt: dt.datetime = dt.datetime.now()) -> pd.DataFrame:
    """
    Finds days when no forecast was recorded (everyday day 40 forecast datapoints are recorded: 5 days * 8 datetimes/day)    
    """
    start_dt = start_dt if start_dt else city.firstMeasurement
    df = load_forecast_file(city)
    merged = df.merge(dts(start_dt, end_dt), how='right', on='today', indicator=True)
    return merged[merged['_merge'] == 'right_only'].groupby('today').count().index.values


def data_intervals(city: City, weather_variable: str) -> list:
    """Returns list of data intervals from a given 'join_data' file

    An interval is a sequence of contiguous datapoints (two datapoints are contiguous if
    their 'dt' values differ by 3h, 3*60*60 seconds)

    Args:
        city (City):
        weather_variable (str):

    Returns:
        list: list of intervals, each interval is represented by a tuple, the values of a tuple t are:
        t[0] --> position of the first row of the interval in the join_data dataframe
        t[1] --> datetime (iso format) of the beginning of the interval
        t[2] --> position of the last row of the interval in the join_data dataframe
        t[3] --> datetime (iso format) of the end of the interval
    """
    step_3hours = 3 * 60 * 60  # number of seconds in between datapoints
    dts = load_csv_files(city, weather_variable)['join_data_df']['dt']
    intervals = []
    interval_left_side = dts[0]
    left_index = 0
    for i in range(1, len(dts)):
        if dts[i] - dts[i - 1] != step_3hours:
            intervals.append((left_index, dt.datetime.fromtimestamp(interval_left_side).isoformat(), i-1, dt.datetime.fromtimestamp(dts[i - 1]).isoformat()))
            interval_left_side = dts[i]
            left_index = i

    intervals.append((left_index, dt.datetime.fromtimestamp(interval_left_side).isoformat(), i-1, dt.datetime.fromtimestamp(dts[i - 1]).isoformat()))
    return intervals

def print_intervals(intervals: list):
    """Print list of intervals in a user-friendly manner

    0:895 -- 2020-06-16T01:00:00:2020-10-05T22:00:00
    896:2255 -- 2020-10-11T01:00:00:2021-03-29T22:00:00
    2256:2319 -- 2021-04-04T01:00:00:2021-04-11T22:00:00
    """
    print("\n".join(map(lambda x: f"{x[0]}:{x[2]} -- {x[1]}:{x[3]}", intervals)))


if __name__ == "__main__":
    for city in rconf.cities.values():
        print(city.name)
        start_dt = dt.datetime(2023, 3, 9, 0, 0, 0, tzinfo=dt.timezone.utc)
        end_dt = dt.datetime(2023, 3, 21, 0, 0, 0, tzinfo=dt.timezone.utc)
        # print(missing_weather_datapoints(city, start_dt, end_dt))
        # print(unexpected_weather_datapoints(city, start_dt, end_dt))
        # print(missing_forecast_datapoints(city, start_dt, end_dt))
        # print(weather_datapoints_without_five_forecasts(city, 'temp', start_dt, end_dt))
    # weather_datapoints_without_five_forecasts(rconf.cities['madrid'], 'temp', end_dt = end_dt).to_csv('./madrid_missing.csv')    
    print_intervals(data_intervals(rconf.cities['madrid'], 'temp'))