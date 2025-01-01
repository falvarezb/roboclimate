Java module to analyze data gathered by the Weather Spiders (`weather_spider_lambda.py` and `forecast_spider_lambda.py`)

It replaces the python module `data_analysis.py` as it is more efficient and faster.


## How to run

Environment variable `ROBOCLIMATE_CSV_FILES_PATH` must be set to the path where the csv files are stored.

```commandline
javac -source 22 --enable-preview -d out src/roboclimate/*.java
java --enable-preview -cp out roboclimate.Main
```