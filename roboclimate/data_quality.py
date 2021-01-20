from collections import namedtuple
import datetime as dt
import pandas as pd
import roboclimate.config as rconf
import roboclimate.util as rutil

City = namedtuple('City', 'name firstMeasurement')
city_names = list(rconf.cities.keys())
cities = [City(city_names[0], dt.datetime(2019, 11, 28, 3, 0, 0, tzinfo=dt.timezone.utc)),
          City(city_names[1], dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          City(city_names[2], dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          City(city_names[3], dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc)),
          City(city_names[4], dt.datetime(2020, 6, 11, 18, 0, 0, tzinfo=dt.timezone.utc))]


def load_csv_files(city: City) -> dict:
    true_temp_df = pd.read_csv(f"csv_files/weather_{city.name}.csv", usecols=['temp', 'dt', 'today'], dtype={'dt': 'int64'})
    forecast_temp_df = pd.read_csv(f"csv_files/forecast_{city.name}.csv", usecols=['temp', 'dt', 'today'], dtype={'dt': 'int64'})
    join_data_df = pd.read_csv(f"csv_files/join_{city.name}.csv", usecols=['temp', 'dt', 'today', 't5', 't4', 't3', 't2', 't1'])
    metrics_df = pd.read_csv(f"csv_files/metrics_{city.name}.csv")
    return {"true_temp_df": true_temp_df, "forecast_temp_df": forecast_temp_df, "join_data_df": join_data_df, "metrics_df": metrics_df}


def dts(start, end=dt.datetime.now()):
    """
    List of date-times for which a temperature should be recorded
    In theory, the times 0,3,6,9,12,15,18,21 of each day
    """
    return pd.DataFrame(data=rutil.date_and_timestamp(start, end), columns=['dt', 'today'])


def missing_temps(city: City) -> pd.DataFrame:
    """
    Finds dts for which the temperature was not recorded
    Returns the right join between the DataFrames: 'true_temp_df' and 'dts'
    """
    df = load_csv_files(city)
    merged = df['true_temp_df'].merge(dts(city.firstMeasurement), how='right', on='dt', indicator=True)
    return merged[merged['_merge'] == 'right_only']  # .groupby('today_y').count()['_merge']


def unexpected_temps(city) -> pd.DataFrame:
    """
    Finds temperatures recorded at dts other than the times 0,3,6,9,12,15,18,21 of each day
    Returns the left join between the DataFrames: 'true_temp_df' and 'dts'
    """
    df = load_csv_files(city)
    merged = df['true_temp_df'].merge(dts(city.firstMeasurement), how='left', on='dt', indicator=True)
    return merged[merged['_merge'] == 'left_only']  # .groupby('today_x').count()['_merge']


def temps_without_five_forecasts(city) -> pd.DataFrame:
    """
    Finds dts for which no all five forecasts were made

    Given that dts without the five forecasts are omitted when constructing 'join_data_df',
    said dts can be found by doing the right join between the DataFrames: 'join_data_df' and 'dts'
    """
    df = load_csv_files(city)
    merged = df['join_data_df'].merge(dts(city.firstMeasurement), how='right', on='dt', indicator=True)
    return merged[merged['_merge'] == 'right_only']  # .groupby('today_y').count()['_merge']


def missing_forecasts(city) -> pd.DataFrame:
    """
    Finds days when no forecast was made
    Returns the right join between the DataFrames: 'forecast_temp_df' and 'dts'
    """
    df = load_csv_files(city)
    merged = df['forecast_temp_df'].merge(dts(city.firstMeasurement), how='right', on='today', indicator=True)
    return merged[merged['_merge'] == 'right_only']  # .groupby('today_x').count()['_merge']


if __name__ == "__main__":
    for city in cities:
        print(city.name)
        print(missing_temps(city))
