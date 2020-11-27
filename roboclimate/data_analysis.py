import logging
from math import sqrt
import pandas as pd
from sklearn.metrics import mean_absolute_error as mae
from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import median_absolute_error as medae
from roboclimate.metrics import mean_absolute_scaled_error_year_avg as mase_year_avg, mean_absolute_scaled_error_tx, mean_absolute_scaled_error_1year
from roboclimate.util import remove_29_feb
import roboclimate.config as config
import roboclimate.util as util

logger = logging.getLogger(__name__)


def load_data(file):
    return pd.read_csv(file, usecols=['temp', 'dt', 'today'], dtype={'dt': 'int64'})


def join_true_temp_and_forecast(true_temp_df, forecast_temp_df):
    """

    Joins the records from weather.csv and forecast.csv by the field dt, effectively
    matching the true temperature with the forecast done over the 5 previous days.
    If the forecast of any of the 5 previous days is not available, the entire record is discarded

    true_temp_df
    ------------

      temp   dt       today
    0   0.5  100  2019-11-30
    1   0.6  200  2019-11-30


    forecast_temp_df
    ----------------

      temp   dt       today
    0   1.0  100  2019-11-30
    1   2.0  100  2019-11-28
    2   1.5  100  2019-11-27
    3   3.0  100  2019-11-29
    4   4.0  100  2019-11-26
    5   5.0  200  2019-11-30
    6   2.0  200  2019-11-28
    7   4.0  200  2019-11-27
    8   3.0  200  2019-11-29
    9   1.0  200  2019-11-26


    result
    ------

       temp   dt       today   t5   t4   t3   t2   t1
    0   0.5  100  2019-11-30  4.0  1.5  2.0  3.0  1.0
    1   0.6  200  2019-11-30  1.0  4.0  2.0  3.0  5.0

    """

    headers = ['t5', 't4', 't3', 't2', 't1']
    df = pd.DataFrame()
    for row in true_temp_df.iterrows():
        try:
            temps = forecast_temp_df[forecast_temp_df['dt'] == row[1]['dt']].sort_values('today').T.loc['temp']
            if len(temps) == len(headers):
                temps_df = pd.DataFrame({i: [j] for i, j in zip(headers, temps)}, index=[row[0]])
                df = df.append(pd.DataFrame([row[1]]).join(temps_df))
            else:
                logger.warning(f"number of temperatures {len(temps)} != 5 for timestamp {row[1]['dt']}")
        except Exception:
            logger.error(f"Error while processing row \n {row[1]}", exc_info=True)

    return df


def forecast_precision(joined_data):
    return {
        "mae": [mae(joined_data['temp'], joined_data[f't{i}']) for i in range(5, 0, -1)],
        "rmse": [sqrt(mse(joined_data['temp'], joined_data[f't{i}'])) for i in range(5, 0, -1)],
        "medae": [medae(joined_data['temp'], joined_data[f't{i}']) for i in range(5, 0, -1)],
        "mase": mean_absolute_scaled_error_tx(joined_data),
        "mase1y": mean_absolute_scaled_error_1year(joined_data)
    }


def analyse_data():
    # london_df = read_historical_data("london_weather_historical_data.csv")

    for city_name in config.cities.keys():
        try:
            weather_file = util.csv_file_path(config.csv_folder, config.weather_resources[0], city_name)
            forecast_file = util.csv_file_path(config.csv_folder, config.weather_resources[1], city_name)
            join_file = util.csv_file_path(config.csv_folder, "join", city_name)
            metrics_file = util.csv_file_path(config.csv_folder, "metrics", city_name)
            join_data_df = join_true_temp_and_forecast(load_data(weather_file), load_data(forecast_file))
            join_data_df.to_csv(join_file, index=False)
            # metrics = forecast_precision(join_data_df, london_df)
            metrics = forecast_precision(join_data_df)
            pd.DataFrame(metrics).to_csv(metrics_file, index=False)
        except Exception:
            logger.error(f"Error while processing {city_name}", exc_info=True)


def main():
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level='INFO')
    analyse_data()
    print('END')


if __name__ == "__main__":
    main()
