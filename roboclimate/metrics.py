from sklearn.metrics import mean_absolute_error as mae
import numpy as np

def mean_absolute_scaled_error(real_data, predicted_data):
    """
    https://en.wikipedia.org/wiki/Mean_absolute_scaled_error
    mean absolute scaled error is a measure of the precision of a model compared to the naive forecast
    naive forecast consists in assuming that the next value is the same as the one of the last period.

    However, "last period" may mean different things for different applications. 
    This function takes as last period the previous value in the time series, that is the temperature from 3 hours ago.

    Parameters
    ----------

    real_data: array

        array of true temperatures recorded at 3-hour intervals

    predicted_data: array

        data predicted by the model under evaluation

    Returns
    -------

    float

        ratio between the mean absolute error of the model under evaluation and the mean absolute error of the
        naive forecast

    """
     
    return mae(real_data[1:], predicted_data[:-1]) / mae(real_data[1:], real_data[:-1])


def mean_absolute_scaled_error_1day(real_data, predicted_data):
    """
    This version of the function 'mean_absolute_scaled_error' considers as "last period" the temperature from 1 day ago
    at the same time

    Given that the elements of the array 'real_data' represent the temperature at 3-hour intervals, the "last period" will be
    8 elements behind

    """

    if len(real_data) <= 8:
        return np.nan
    return mae(real_data[8:], predicted_data[:-8]) / mae(real_data[8:], real_data[:-8])


def mean_absolute_scaled_error_1year(real_data, predicted_data):
    """
    This version of the function 'mean_absolute_scaled_error' considers as "last period" the temperature from 1 year ago,
    on the same date at the same time

    """

    return mae(real_data, predicted_data) / mae(real_data[8:], real_data[:-8])
