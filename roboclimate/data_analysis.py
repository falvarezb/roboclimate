
import logging
from math import sqrt
import pandas as pd
from sklearn.metrics import mean_absolute_error as mae
from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import median_absolute_error as medae
from roboclimate.metrics import mean_absolute_scaled_error_tx as masetx, mean_absolute_scaled_error_1year as mase1y
import roboclimate.config as config
import roboclimate.util as util

logger = logging.getLogger(__name__)


def load_data(file):
    return pd.read_csv(file, dtype={'dt': 'int64'})

# def load_data(file, weather_variable):
#     return pd.read_csv(file, usecols=[weather_variable, 'dt', 'today'], dtype={'dt': 'int64'})


def join_actual_values_and_forecast(actual_values_df, forecast_df):
    """
    Joins the records from weather.csv and forecast.csv by the field dt, effectively
    matching the actual values of the weather variables with the forecast done over the 5 previous days.
    If the forecast of any of the 5 previous days is not available, the entire record is discarded

    actual_values_df
    -----------------

      temp    pressure  .....    dt   today
    0   0.5   1010               100  2019-11-30
    1   0.6   999                200  2019-11-30


    forecast_df
    ----------------

      temp     pressure     ....    dt      today
    0   1.0    1000                 100     2019-11-29
    1   2.0    1002                 100     2019-11-27
    2   1.5    990                  100     2019-11-26
    3   3.0    1020                 100     2019-11-28
    4   4.0    992                  100     2019-11-25
    5   5.0    1013                 200     2019-11-29
    6   2.0    1012                 200     2019-11-27
    7   4.0    1000                 200     2019-11-26
    8   3.0    1030                 200     2019-11-28
    9   1.0    1000                 200     2019-11-25
    10  2.1    1005                 300     2019-11-29
    11  2.2    1006                 300     2019-11-27
    12  2.3    1007                 300     2019-11-26
    13  2.4    1008                 300     2019-11-28
    14  2.5    1009                 300     2019-11-25


    result
    ------

       temp   dt       today   t5   t4   t3   t2   t1
    0   0.5  100  2019-11-30  4.0  1.5  2.0  3.0  1.0
    1   0.6  200  2019-11-30  1.0  4.0  2.0  3.0  5.0


       pressure   dt       today   t5   t4   t3   t2   t1
    0  1010       100  2019-11-30  992  990  1002 1020 1000
    1  999        200  2019-11-30  1000 1000 1012 1030 1013

    .....

    """

    headers = ['t5', 't4', 't3', 't2', 't1']
    # discarding empty values
    actual_values_df.dropna(inplace=True)
    # initializing dataframes
    dfs_dict = {weather_variable: pd.DataFrame() for _, weather_variable in config.weather_variables.items()}

    for row in actual_values_df.iterrows():
        try:
            # 1st row (dt=100)
            # -----------------
            #               0           1           2           3           4
            # temp          4.0         1.5         2.0         3.0         1.0
            # pressure      991         990         1002        1020        1000
            # ....
            # dt            100         100         100         100         100
            # today         2019-11-25  2019-11-26  2019-11-27  2019-11-28  2019-11-29
            #
            transposed_forecast_df = forecast_df[forecast_df['dt'] == row[1]['dt']].sort_values('today').T
            if transposed_forecast_df.shape[1] == len(headers):
                for weather_variable, df in dfs_dict.items():

                    # weather_variable = temp
                    # ------------------------
                    #
                    #       t5  t4  t3  t2  t1
                    # 0     4.0 1.5 2.0 3.0 1.0
                    #
                    tees_df = pd.DataFrame({i: [j] for i, j in zip(headers, transposed_forecast_df.loc[weather_variable])}, index=[row[0]])

                    # weather_variable = temp
                    # ------------------------
                    #     temp  dt   today
                    # 0   0.5   100  2019-11-30
                    #
                    weather_variable_df = pd.DataFrame({weather_variable: [row[1][weather_variable]], 'dt': [
                                                       row[1]['dt']], 'today': [row[1]['today']]}, index=[row[0]])

                    # weather_variable = temp
                    # ------------------------
                    #     temp  dt   today      t5  t4  t3  t2  t1
                    # 0   0.5   100  2019-11-30 4.0 1.5 2.0 3.0 1.0
                    #
                    joined_df = df.append(weather_variable_df.join(tees_df))
                    dfs_dict[weather_variable] = joined_df
            # else:
            #     logger.warning(f"number of {weather_variable} {len(temps)} != 5 for timestamp {row[1]['dt']}")
        except Exception:
            logger.error(f"Error while processing row \n {row[1]}", exc_info=True)

    return dfs_dict


def forecast_precision(joined_data, weather_variable):
    return {
        "mae": [mae(joined_data[weather_variable], joined_data[f't{i}']) for i in range(5, 0, -1)],
        "rmse": [sqrt(mse(joined_data[weather_variable], joined_data[f't{i}'])) for i in range(5, 0, -1)],
        "medae": [medae(joined_data[weather_variable], joined_data[f't{i}']) for i in range(5, 0, -1)],
        "mase": masetx(joined_data, weather_variable),
        "mase1y": mase1y(joined_data, weather_variable)
    }


def select_intervals(join_data_df: pd.DataFrame, intervals: list) -> pd.DataFrame:
    if intervals is None:
        return join_data_df
    else:
        df = join_data_df
        for interval in intervals:
            df = df.iloc[interval[0]:interval[1]]
        return df


def analyse_data(intervals: list = None):
    for city_name in config.cities.keys():
        analyse_city_data(city_name, intervals)


def analyse_city_data(city_name: str, intervals: list = None):
    """Calculates metrics corresponding to the given city and intervals

    Two file types are generated for each weather attribute: join_{city}.csv and
    metrics_{city}.csv.

    join* files contain the result of joining each weather measurement with its 5
    forecasts. See function 'join_actual_values_and_forecast' for more details.

    metrics* files contain the values of the different metrics for each tx forecast.
    First row is t5, second row t4 and so on up to the fifth row that is t1.

    Args:
        city_name (str):
        intervals (list, optional): output generated by data_explorer.data_intervals
    """
    try:
        # file pointers
        weather_file = util.csv_file_path(config.csv_folder, config.weather_resources[0], city_name)
        forecast_file = util.csv_file_path(config.csv_folder, config.weather_resources[1], city_name)

        join_data_dict = join_actual_values_and_forecast(load_data(weather_file), load_data(forecast_file))

        for _, weather_variable in config.weather_variables.items():
            try:
                # file pointers
                join_file = util.csv_file_path(config.csv_folder, "join", city_name, weather_variable)
                metrics_file = util.csv_file_path(config.csv_folder, "metrics", city_name, weather_variable)

                selected_df = select_intervals(join_data_dict[weather_variable], intervals)
                selected_df.to_csv(join_file, index=False)
                metrics = forecast_precision(selected_df, weather_variable)
                pd.DataFrame(metrics).to_csv(metrics_file, index=False)
            except Exception:
                logger.error(f"Error while processing {weather_variable} for {city_name}", exc_info=True)
    except Exception:
        logger.error(f"Error while processing {city_name}", exc_info=True)


def main():
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level='INFO')
    analyse_city_data('madrid', [(2328,2840)])
    logger.info('END')


if __name__ == "__main__":
    main()
