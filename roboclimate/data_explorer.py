"""Data Explorer

    Functions to explore captured data:  missing values, etc
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
    df = df[(df['dt'] >= start_dt_ts) & (df['dt'] < end_dt_ts) ]
    merged = df.merge(dts(start_dt, end_dt), how='left', on='dt', indicator=True)
    return merged[merged['_merge'] == 'left_only']  # .groupby('today_x').count()['_merge']


def weather_datapoints_without_five_forecasts(city: City, weather_variable: str, start_dt: dt.datetime = None, end_dt: dt.datetime = dt.datetime.now()) -> pd.DataFrame:
    """
    Finds dts for which not all five forecasts were made

    Given that dts without the five forecasts are excluded when constructing 'join_data_df',
    said dts can be found by doing the right join between the DataFrames: 'join_data_df' and 'dts'
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


if __name__ == "__main__":
    for city in rconf.cities.values():
        print(city.name)
        start_dt = dt.datetime(2023, 3, 9, 0, 0, 0, tzinfo=dt.timezone.utc)
        end_dt = dt.datetime(2023, 3, 20, 21, 0, 0, tzinfo=dt.timezone.utc)
        # print(missing_weather_datapoints(city, start_dt, end_dt))
        # print(unexpected_weather_datapoints(city, start_dt, end_dt))
        # print(missing_forecast_datapoints(city, start_dt, end_dt))
        # print(weather_datapoints_without_five_forecasts(city, 'temp', start_dt, end_dt))
