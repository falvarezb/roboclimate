    # """
    # Module to implement the mean absolute scaled error (https://en.wikipedia.org/wiki/Mean_absolute_scaled_error)

    # mean absolute scaled error (mase) is a measure of the precision of a model compared to the naive forecast
    # the naive forecast consists in assuming that the next value is the same as the one of the prior period.

    # However, "prior period" may mean different things depending on whether the time series under consideration is
    # seasonal or non-seasonal.
    # For instance, for the temperature forecast, we may consider as prior value the temperature on the same day and time
    # of the previous month, year, etc.

    # This module contain functions to calculate both seasonal and non-seasonal mase.

    # An additional problem to contend with is data quality: if there are missing values in the time series, it may not be
    # possible to get the value corresponding to the prior period.   
    # """


from datetime import datetime, timezone
from sklearn.metrics import mean_absolute_error as mae
import numpy as np
from roboclimate.util import n_years_ago, remove_29_feb
import roboclimate.config as rconf




def mean_absolute_scaled_error(real_data, predicted_data, period=1) -> float:
    """
    This function is the basic building block of this module.
    By default this function takes as prior period the previous value in the time series, that is the temperature corresponding to 3 hours ago.

    Parameters
    ----------

    real_data: array

        array of true values (recorded at 3-hour intervals)

    predicted_data: array

        data predicted by the model under evaluation

    period: int

        relative position in the time series corresponding to the "prior period"

    Returns
    -------

    float

        ratio between the mean absolute error of the model under evaluation and the mean absolute error of the
        naive forecast

        if there is no "prior period" for any of the elements in the series (this may happen if there are no enough
        elements in the data series), np.nan is returned

    """

    if len(real_data) <= period:
        return np.nan
    return mae(real_data[period:], predicted_data[period:]) / mae(real_data[period:], real_data[:-period])



def mean_absolute_scaled_error_1year(joined_data, weather_variable):
    """
    This function considers as "prior period" the temperature corresponding to 1 year ago, on the same day at the same time.

    It calculates the mase for each of the 5 forecast predictions, namely: t1, t2, t3, t4 and t5

    Parameters
    ----------

    joined_data: DataFrame

       temp   dt       today   t5   t4   t3   t2   t1
    0   0.5  100  2019-11-30  4.0  1.5  2.0  3.0  1.0
    1   0.6  200  2019-11-30  1.0  4.0  2.0  3.0  5.0


    weather_variable: str
        name of the weather variable contained by joined_data; in the previous example is 'temp'

    
    Returns
    -------

    list[float]

        list containing the mase for each tx model: [mase(t5), mase(t4), mase(t3), mase(t2), mase(t1)]

        if there is no "prior period" for any of the elements in the series (this may happen if there are no enough
        elements in the data series), np.nan is returned

    TODO: instead of stopping the entire calculation, just discard the offending data point and continue calculation with rest of data
    """
    joined_data_without_29_feb = remove_29_feb(joined_data)
    return [mean_absolute_scaled_error(joined_data_without_29_feb[weather_variable], joined_data_without_29_feb[f't{i}'], 365 * rconf.day_factor) for i in range(5, 0, -1)]


def mean_absolute_scaled_error_year_avg(joined_data, historical_data, weather_variable, years_back=19):
    """
    This function considers as "last period" the avg temperature, on the same date at the same time, over the years present in 
    the historical data (currently up to 19 years for London)

    In case the historical data does not contain the data point for any of the datetimes considered, the mae is not calculated
    and np.nan is returned

    TODO: instead of stopping the entire calculation, just discard the offending data point and continue calculation with rest of data
    """

    def previous_years_avg(dt):
        date_time = datetime.fromtimestamp(dt, tz=timezone.utc)
        return np.average([historical_data[weather_variable][n_years_ago(date_time, n)] for n in range(1, years_back + 1)])

    try:
        joined_data_without_29_feb = remove_29_feb(joined_data)
        naive_prediction = [previous_years_avg(dt) for dt in joined_data_without_29_feb['dt']]
        return [mae(joined_data_without_29_feb[weather_variable], joined_data_without_29_feb[f't{i}']) / mae(joined_data_without_29_feb[weather_variable], naive_prediction) for i in range(5, 0, -1)]
    except KeyError as err:
        print(f"{err} not found in historical data")
        return np.nan


def mean_absolute_scaled_error_tx(joined_data, weather_variable) -> 'list[float]':
    """
    This function considers as "prior period" the temperature corresponding to 1 year ago, on the same day at the same time.

    This function calculates the mase for each of the 5 forecast models: t1, t2, t3, t4 and t5.
    For each model, the natural "prior period" is the number of days of the forecast: 1, 2, 3, 4, 5

    Data quality issues like missing values of the "prior period" are considered negligible since any effect will 
    be very localised: 'mase(tx)' calculation will be affected only in those cases where there are missing values in the 
    previous 'x*rconf.day_factor' elements of the time series (in such a case, the wrong datetimes will be compared)

    Parameters
    ----------

    joined_data: DataFrame

       temp   dt       today   t5   t4   t3   t2   t1
    0   0.5  100  2019-11-30  4.0  1.5  2.0  3.0  1.0
    1   0.6  200  2019-11-30  1.0  4.0  2.0  3.0  5.0


    weather_variable: str
        name of the weather variable contained by joined_data; in the previous example is 'temp'

    
    Returns
    -------

    list[float]

        list containing the mase for each tx model: [mase(tx), for x in 5...1]

        if a model cannot be calculated becase there are no enough elements in the data series, np.nan is returned for said model   
    """
    return [mean_absolute_scaled_error(joined_data[weather_variable], joined_data[f't{i}'], i * rconf.day_factor) for i in range(5, 0, -1)]
