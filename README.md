# About Roboclimate

Have you ever complained about the weatherman failing to predict the weather correctly?
That's what this project is about: the realiability of the weather forecasts.
To do so we'll investigate the accuracy of the meteorological models.

## Scope

### Weather variables

- temperature
- pressure
- humidity
- wind intensity
- wind direction


### Locations

- London
- Madrid
- Sydney
- New York
- Sao Paulo
- Tokyo
- Moscow
- Asuncion
- Nairobi
- Lagos



## Models

### Naive forecast

Consists in assuming that the next value is the same as the one of the last period.

The tricky part is to identify what the last value is. For instance, if we measure the temperature
every 3 hours and we want to predict the temperature today at 3pm, what is the last value: today's temperature at 12pm, yesterday's temperature at 3pm or maybe last year's temperature on the same day at 3pm?


### Meteorological models

Provided by OpenWeather API (https://openweathermap.org/technology)


## Metrics

Metrics are used to evaluate the accuracy of the models' predictions when compared to the actual values.


### Mean absolute scaled error (MASE)

Mean absolute scaled error is a measure of the precision of a model compared to the naive forecast.

It is the mean absolute error of the forecast values, divided by the mean absolute error of the naive forecast.

Values greater than one indicate that the naive method performs better than the forecast values under consideration.

https://en.wikipedia.org/wiki/Mean_absolute_scaled_error

### Mean absolute error (MAE)

Average of the absolute value of the errors (the errors being the differences between predicted and real values)

### Root mean squared error (RMSE)

Square root of the average of the square of the errors

It weighs outliers more heavily than MAE as a result of the squaring of each term, which effectively weighs large errors more heavily than small ones

### Median absolute error (MEDAE)

Median of the absolute value of the errors.

It is robust to outliers


## Methodology

1. Actual weather variables are measured (read from OpenWeather API) every 3 hours: 12am, 3am, 6am and so on.
2. Every day, we get the forecast of those weather variables for each of the hours under consideration (12am, 3am, 6am...) over the next 5 days
3. Metrics are calculated by comparing each actual value with the value forecasted 1 day before, 2 days before, etc.

## Technical information

This project comprises two different applications:

- data collection
- data analysis

### Data collection

Data collection consists of two different python modules (`weather_spider.py`, `forecast_spider`) that run as two separate lambda functions on AWS. Those modules share common functionality through `common.py`

The data collected is stored on an EFS (Elastic File System).

This data is obtained from https://openweathermap.org through the endpoints:
- current weather data
- 5 day forecast

Given that the 5 day forecast only include data every 3 hours (00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00), those are the data points for which we get the current weather data too.

The data is recorded in 2 types of csv files:

- `weather_*.csv`
- `forecast_*.csv`

where `*` represents each of the locations.


Dependencies corresponding to the production code of data collection must be kept separate in the file `lambda_requirements.txt`. This file is used to generate the artifact to be deployed as a lambda function.


On the other hand, `requirements.txt` has all the dependencies to run all modules and their corresponding tests.


### Data analysis

Data analysis is carried out by the modules:

- `data_analysis.py`, to calculate metrics
- `data_explorer.py`, to explore the quality of the data collected (like missing datapoints)
- `streamlit_app.py`, Streamlit dashboard to visualize data


Steps:

- join the records from `weather_*.csv` and `forecast_*.csv` by the datetime field `dt` to match the actual measurement with each of the forecasts made over the 5 previous days; the result is stored in `join_*.csv``
- calculate the precision of the forecast according to the different metrics; the result is stored on `metrics_*.csv`


### Tests

```
pytest --cov-branch --cov-report html --cov=roboclimate tests/
```

Coverage report is generated in the folder `htmlcov`

### Deployment

