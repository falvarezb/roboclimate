# About Roboclimate

Have you ever complained about the weatherman failing to predict the weather correctly?
That's what this project is about: the realiability of the weather forecasts.
To do so we'll investigate the accuracy of the meteorological models.

## Scope

### Weather variables

- temperature
- pressure
- humidity
- wind speed
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
- Quito
- Guayaquil
- Belem
- Reykjavik
- Ushuaia
- La Paz
- Cairo
- Mumbai
- Singapore
- Santos



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

This project comprises two Python applications (the Lambda functions run on Python 3.13):

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


Lambda dependencies are locked separately under `lambda/` (see `lambda/README.md` for locking, building, deploying and releasing).

`requirements.txt` has all the dependencies to run all modules and their corresponding tests locally.


### Data analysis

Data analysis is carried out by the modules:

- `data_analysis.py`, to calculate metrics
- `data_explorer.py`, to explore the quality of the data collected (like missing datapoints)
- `streamlit_app.py`, Streamlit dashboard to visualize data


Steps:

- join the records from `weather_*.csv` and `forecast_*.csv` by the datetime field `dt` to match the actual measurement with each of the forecasts made over the 5 previous days; the result is stored in `join_*.csv``
- calculate the precision of the forecast according to the different metrics; the result is stored on `metrics_*.csv`


The files `weather_*.csv` and `forecast_*.csv` need to be [downloaded from the EFS](./terraform/readme.md#%20CSV%20files)


### Tests

```
pytest --cov-branch --cov-report html --cov=roboclimate tests/
```

Coverage report is generated in the folder `htmlcov`

### Environment variables

__OPEN_WEATHER_API__

Key to access OpenWeather API

__ROBOCLIMATE_HOME__

Path to the root folder of the project

__ROBOCLIMATE_CSV_FILES_PATH__

Path to the root folder containing the different csv files, e.g.
```
csv_files
├── forecast_london.csv
├── forecast_madrid.csv
├── humidity
│   ├── join_london.csv
│   ├── join_madrid.csv
│   ├── metrics_london.csv
│   ├── metrics_madrid.csv
├── pressure
│   ├── join_london.csv
│   ├── join_madrid.csv
│   ├── metrics_london.csv
│   ├── metrics_madrid.csv
├── temp
│   ├── join_london.csv
│   ├── join_madrid.csv
│   ├── metrics_london.csv
│   ├── metrics_madrid.csv
├── weather_london.csv
├── weather_madrid.csv
├── wind_deg
│   ├── join_london.csv
│   ├── join_madrid.csv
│   ├── metrics_london.csv
│   ├── metrics_madrid.csv
└── wind_speed
    ├── join_london.csv
    ├── join_madrid.csv
    ├── metrics_london.csv
    ├── metrics_madrid.csv
```

### Deployment

See [deploy](./terraform/readme.md)

### Adding a city

The city list is repeated in several places; update all of them in one PR.

1. **Look up the city on OpenWeather** (never from memory):
   - coordinates from the geocoding API: `https://api.openweathermap.org/geo/1.0/direct?q=<city>,<country code>&limit=1&appid=<key>`
   - the city id from the weather API: `https://api.openweathermap.org/data/2.5/weather?q=<city>,<country code>&appid=<key>` — check the returned `name` and `coord` match the geocoding result.
2. **Edit these places** (use a lowercase, ASCII key without spaces, e.g. `lapaz`):
   - `roboclimate/common.py` — `CITIES` (`"key": id`) and `CITY_PARAMS` (`CityParams('key', lat, lon, tz_offset)`)
   - `roboclimate/config.py` — `cities` (`City(id, 'key', firstMeasurement)`)
   - `roboclimate/data_analysis/src/roboclimate/Main.java` — the `cities` list
   - the [Locations](#locations) list above

   `tz_offset` is the city's **standard UTC offset, ignoring daylight saving** (e.g. Madrid `1`, Cairo `2`, Mumbai `5.5`): the UV spider uses it to request each day's reading at 12:00 local standard time. The tests derive the number of cities from `CITY_PARAMS`, so they need no change.
3. **Verify:** run the tests and `terraform/artifact_prep.sh all`, then run the built spider packages in the Lambda emulator against a throwaway copy of the CSVs and check the new city gains rows (see `lambda/prerelease_check.sh` for the emulator invocation).
4. **Ship** following [lambda/README.md](./lambda/README.md): deploy from `master`, `lambda/prerelease_check.sh` on each new spider version (it checks that every configured city gains rows), then a release PR that bumps the pinned versions **and** sets the new cities' `firstMeasurement` in `config.py` to the first scheduled weather run after the release (runs are every 3 hours from 00:00 UTC).
5. **Expect a delay before analysis:** forecasts are compared 1–5 days ahead, so a new city has no joined records until about 5 days after its first run. Until then both analyses (Java and the legacy `data_analysis.py`) log a warning and skip the city ("no data yet") or just its metrics ("no joined records yet", writing a header-only join file), and the dashboard lists a city only once its metrics exist.
