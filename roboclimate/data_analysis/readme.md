Java module to analyze data gathered by the Weather Spiders (`weather_spider_lambda.py` and `forecast_spider_lambda.py`)

It replaces the python module `data_analysis.py` as it is more efficient and faster. `data_analysis.py` remains the
reference implementation: both must produce the same join and metrics files (see [Parity check](#parity-check)).


## How to run

Environment variable `ROBOCLIMATE_CSV_FILES_PATH` must be set to the path where the csv files are stored.

```commandline
javac -source 22 --enable-preview -d out src/roboclimate/*.java
java --enable-preview -cp out roboclimate.Main
```

Requires JDK 22: the code uses string templates (`STR."..."`), a preview feature removed in JDK 23.


## Parity check

`parity_check.py` runs this module and `data_analysis.py` on identical copies of the same input and fails if any join row
or metric differs (relative tolerance 1e-9). Run it after any change to either analysis (from the repo root):

```commandline
JAVA_HOME=<jdk22> bin/python roboclimate/data_analysis/parity_check.py             # generated fixture, ~5 s
JAVA_HOME=<jdk22> bin/python roboclimate/data_analysis/parity_check.py --data DIR  # real CSVs; slow (Python takes minutes per city)
```

The generated fixture covers the cases where the two implementations once diverged:
- a blank value (e.g. `wind_deg`) in a measurement or forecast must exclude that record for that variable only;
- MASE only pairs data points exactly `period x 3h` apart, so gaps in the time series are never paired across;
- a measurement with fewer than 5 forecasts produces no join row.
