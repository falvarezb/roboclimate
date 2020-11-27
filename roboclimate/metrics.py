from datetime import datetime, timezone
from sklearn.metrics import mean_absolute_error as mae
import numpy as np
from roboclimate.util import one_year_ago, n_years_ago, remove_29_feb


def mean_absolute_scaled_error(real_data, predicted_data, period=1):
    """
    https://en.wikipedia.org/wiki/Mean_absolute_scaled_error
    mean absolute scaled error is a measure of the precision of a model compared to the naive forecast
    naive forecast consists in assuming that the next value is the same as the one of the last period.

    However, "last period" may mean different things for different applications.
    By default this function takes as last period the previous value in the time series, that is the temperature from 3 hours ago.

    Parameters
    ----------

    real_data: array

        array of true temperatures recorded at 3-hour intervals

    predicted_data: array

        data predicted by the model under evaluation

    period: int

        element in the temperature series considered as last period

    Returns
    -------

    float

        ratio between the mean absolute error of the model under evaluation and the mean absolute error of the
        naive forecast

    """

    if len(real_data) <= period:
        return np.nan
    return mae(real_data[period:], predicted_data[period:]) / mae(real_data[period:], real_data[:-period])


def mean_absolute_scaled_error_1year(joined_data):
    """
    This function considers as "last period" the temperature from 1 year ago, on the same date at the same time.
    In case the historical data does not contain the data point for any of the datetimes considered, the mae is not calculated
    and np.nan is returned

    TODO: instead of stopping the entire calculation, just discard the offending data point and continue calculation with rest of data
    """
    joined_data_without_29_feb = remove_29_feb(joined_data)
    return [mean_absolute_scaled_error(joined_data_without_29_feb['temp'], joined_data_without_29_feb[f't{i}'], 365 * 8) for i in range(5, 0, -1)]


def mean_absolute_scaled_error_year_avg(joined_data, historical_data, years_back=19):
    """
    This function considers as "last period" the avg temperature, on the same date at the same time, over the years present in 
    the historical data (currently up to 19 years for London)

    In case the historical data does not contain the data point for any of the datetimes considered, the mae is not calculated
    and np.nan is returned

    TODO: instead of stopping the entire calculation, just discard the offending data point and continue calculation with rest of data
    """

    def previous_years_avg(dt):
        date_time = datetime.fromtimestamp(dt, tz=timezone.utc)
        return np.average([historical_data['temp'][n_years_ago(date_time, n)] for n in range(1, years_back + 1)])

    try:
        joined_data_without_29_feb = remove_29_feb(joined_data)
        naive_prediction = [previous_years_avg(dt) for dt in joined_data_without_29_feb['dt']]
        return [mae(joined_data_without_29_feb['temp'], joined_data_without_29_feb[f't{i}']) / mae(joined_data_without_29_feb['temp'], naive_prediction) for i in range(5, 0, -1)]
    except KeyError as err:
        print(f"{err} not found in historical data")
        return np.nan


def mean_absolute_scaled_error_tx(joined_data):
    return [mean_absolute_scaled_error(joined_data['temp'], joined_data[f't{i}'], i * 8) for i in range(5, 0, -1)]
