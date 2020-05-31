from datetime import datetime, timezone
from sklearn.metrics import mean_absolute_error as mae
import numpy as np
from roboclimate.util import one_year_ago

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
     
    return mae(real_data[period:], predicted_data[period:]) / mae(real_data[period:], real_data[:-period])


def mean_absolute_scaled_error_1day(real_data, predicted_data):
    """
    This version of the function 'mean_absolute_scaled_error' considers as "last period" the temperature at the same time 1 day ago

    Given that the elements of the array 'real_data' represent the temperature at 3-hour intervals, the "last period" will be
    8 elements behind

    """

    period = 8
    if len(real_data) <= period:
        return np.nan
    return mean_absolute_scaled_error(real_data, predicted_data, period)


def mean_absolute_scaled_error_1year(real_data_without_feb_29, predicted_data_without_feb_29, dt_data_without_feb_29, historical_data):
    """
    This version of the function 'mean_absolute_scaled_error' considers as "last period" the temperature from 1 year ago,
    on the same date at the same time.

    """

    previous_year_datetime = lambda dt: one_year_ago(datetime.fromtimestamp(dt, tz=timezone.utc))    
    naive_prediction = [historical_data[previous_year_datetime(j)] for j in dt_data_without_feb_29]

    return mae(real_data_without_feb_29, predicted_data_without_feb_29) / mae(real_data_without_feb_29, naive_prediction)


