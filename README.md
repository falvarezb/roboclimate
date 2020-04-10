# About this project

## Description and motivation

Have you ever complained about the weatherman failing to predict the weather correctly?

That's the question this project aims to answer: how reliable are the weather predictions?

To do so we'll compare the accuracy of different weather models ranging from a naive approach to  sophisticated meteorological models.

## Scope

For now, we consider only one weather variable, temperature, and one location, London.


## Models

### Naive forecast

Consists in assuming that the next value is the same as the one of the last period.

The tricky part is to identify what the last value is. For instance, if we measure the temperature
every 3 hours and we want to predict the temperature today at 3pm, what is the last value: today's temperature at 12pm, yesterday's temperature at 3pm or maybe last year's temperature on the same day at 3pm?

### Average values

Following with the previous example, we could use the average of the temperature over the last 20
years on the same day at 3pm

### Meteorological models

Provided by OpenWeather (https://openweathermap.org/technology)


## Metrics

Metrics are used to evaluate the accuracy of the models' predictions when compared to the actual values.


### Mean absolute scaled error (MASE)

Mean absolute scaled error is a measure of the precision of a model compared to the naive forecast.

It is the mean absolute error of the forecast values, divided by the mean absolute error of the naive forecast.

Values greater than one indicate that the naive method performs better than the forecast values under consideration.

https://en.wikipedia.org/wiki/Mean_absolute_scaled_error

### Mean absolute error (MAE)

Average of the absolute value of the errors (the errors being the differences between predicted and real values)

The mean absolute error uses the same scale as the data being measured.

### Mean squared error (MSE)

Average of the square of the errors

It weights outliers more heavily than MEA as a result of the squaring of each term, which effectively weights large errors more heavily than small ones

### Median absolute error (MEDAE)

Median of the absolute value of the errors.

It is robust to outliers


## Applications

This project comprises several applications that combined constitute our data pipeline.

### Weather spider

The weather spider collects data about the actual weather and the meteorological forecast for the following 5 days.

This data is obtained from https://openweathermap.org through the endpoints:

- current weather data
- 5 day forecast

Given that the 5 day forecast only include data every 3 hours (00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00), those are the data points for which we get the current weather data too.

The data is recorded on 2 csv files:

- weather.csv
- forecast.csv

that are created inside a folder called 'csv_files' that, in turn, is created in the location where the script is executed from.

Example of data contained on weather.csv:

```
temp,pressure,humidity,wind_speed,wind_deg,dt,today
1.56,1031,93,1.5,,1575331200.0,2019-12-03
1.38,1030,86,2.1,230,1575342000.0,2019-12-03
```

and forecast.csv:

```
temp,pressure,humidity,wind_speed,wind_deg,dt,today
2.36,1021,89,1.41,189,1575428400,2019-12-03
2.62,1021,88,0.99,175,1575439200,2019-12-03
```

### Data anlysis

...


## Housekeeping

Export environment settings to provision cloud instance:

```
conda env export > roboclimate.yml
```
