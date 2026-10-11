# Analysis charts

Charts from analyses of the roboclimate data. Each PNG has a CSV with the exact values plotted.
The committed versions were produced on 2026-10-11 from the S3 backup of 2026-10-10 (London measurements from
2019-11-28, forecast comparisons from 2019-12-03), after the Java/Python parity fix (#25).

## Regenerating

`make_charts.py` rebuilds all charts and CSVs in this folder from the data files. Refresh the data and run the
analysis first, so the `join_*.csv` files are current (from the repo root):

```bash
terraform/download_csv_files_from_s3.sh myadmin csv_files     # latest backup from S3
# run the Java analysis (roboclimate/data_analysis/readme.md) or data_analysis.py
bin/python docs/analysis/make_charts.py                       # --data DIR to use another folder
```

## London temperature forecasts: MASE by season

`london_temp_mase_by_season.png` · `london_temp_mase_by_season.csv`

MASE of the 1-day (t1) and 5-day (t5) temperature forecasts for London, by season and year. MASE below 1 means the
forecast beats a naive "same time, x days earlier" forecast; lower is better. Compare a line with itself over time
rather than t1 with t5: each horizon is scaled by its own naive baseline.

- Winter is labelled by the year of its January (December counts towards the following winter).
- Season/year cells with fewer than 400 readings are omitted (mostly collection outages); 2022 has no data
  (measurements missing from 2022-01-15 to 2023-03-09).
- MASE uses the current definition in `roboclimate/metrics.py`; see #27 for a proposed refinement (< 1% change for London).

## London wind rose

`london_wind_rose.png` · `london_wind_rose.csv`

Direction the wind blows from, in 8 compass sectors, as a share of 3-hourly measurements: overall (split by
Beaufort wind-speed band, in km/h) and by season (same scale).

- Calm readings (< 3.6 km/h, i.e. 1 m/s) are excluded, as are readings with direction exactly 0°, which appear to be
  placeholders for light or variable wind (73% of the raw "north" readings, at 1.9 m/s on average) — 14,518 readings remain.
- Speed bands follow the Beaufort scale thresholds in km/h: light 4–11, gentle 12–19, moderate 20–28, fresh or stronger ≥ 29.
- CSV columns: share of all readings per sector and speed band, the sector total, and the per-season share (`season_*`).
