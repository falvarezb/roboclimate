import numpy as np
from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import mean_absolute_error as mae

import math
import datetime as dt

y_true = [3, -0.5, 2, 7]
y_pred = [2.5, 0.0, 2, 8]
print(mse(y_true, y_pred))
print(mae(y_true, y_pred))

my_mse = sum([(y_true[i] - y_pred[i])**2 for i in range(0, len(y_true))])/len(y_true)
my_mae = sum([abs(y_true[i] - y_pred[i]) for i in range(0, len(y_true))])/len(y_true)

print(my_mse)
print(my_mae)

def epoch_time(ref_date):
    return {"0": dt.datetime(ref_date.year, ref_date.month, ref_date.day).timestamp(),
            "3": dt.datetime(ref_date.year, ref_date.month, ref_date.day, 3).timestamp(),
            "6": dt.datetime(ref_date.year, ref_date.month, ref_date.day, 6).timestamp(),
            "9": dt.datetime(ref_date.year, ref_date.month, ref_date.day, 9).timestamp(),
            "12": dt.datetime(ref_date.year, ref_date.month, ref_date.day, 12).timestamp(),
            "15": dt.datetime(ref_date.year, ref_date.month, ref_date.day, 15).timestamp(),
            "18": dt.datetime(ref_date.year, ref_date.month, ref_date.day, 18).timestamp(),
            "21": dt.datetime(ref_date.year, ref_date.month, ref_date.day, 21).timestamp(),
            }

#datetime.utcnow()
print(epoch_time(dt.datetime(2019, 11, 24)))