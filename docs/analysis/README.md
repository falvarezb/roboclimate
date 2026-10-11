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

## Wind roses (original 10 cities)

`wind_rose_<city>.png` · `wind_rose_<city>.csv` for london, madrid, newyork, moscow, tokyo, saopaulo, sydney,
asuncion, nairobi, lagos

Direction the wind blows from, in 8 compass sectors, as a share of 3-hourly measurements: all year (split by
Beaufort wind-speed band, in km/h) and by three-month block (same scale within each city).

| City | Dominant directions (all year) |
|---|---|
| London | SW 29%, W 18%, E 16% |
| Madrid | SW 21%, NE 17%, W 17% |
| New York | W 22%, NW 16%, NE 16% |
| Moscow | SW 17%, W 17%, NW 14% |
| Tokyo | S 26%, N 25%, NE 12% |
| São Paulo | SE 24%, E 23%, S 18% |
| Sydney | S 18%, NW 17%, W 17% |
| Asunción | S 27%, NE 22%, E 17% |
| Nairobi | E 33%, NE 32%, SE 11% |
| Lagos | SW 46%, S 27%, W 12% |

- Calm readings (< 3.6 km/h, i.e. 1 m/s) are excluded, and so are readings of exactly 0°: as in METAR station reports,
  000° codes calm or variable wind, while a genuine north wind is recorded as 360° (every city has both). For London,
  49% of the raw north-sector readings are exactly 0°, at 1.9 m/s on average versus 4.1 m/s for other directions.
- The three-month panels are named by local season: northern cities Winter = Dec–Feb; southern cities (São Paulo,
  Sydney, Asunción) Summer = Dec–Feb; Nairobi and Lagos, near the equator with wet/dry rather than four seasons,
  are labelled by months only.
- Each city's main rose has its own radial scale (Lagos peaks at 46%), so compare shapes rather than bar lengths
  across cities.
- Speed bands follow the Beaufort scale thresholds in km/h: light 4–11, gentle 12–19, moderate 20–28, fresh or stronger ≥ 29.
- Moscow's directions are mostly not multiples of 10° (16%, against 68–90% elsewhere), suggesting a different
  underlying source for that city.
- CSV columns: share of all readings per sector and speed band, the sector total, and the per-block share (`months_*`).
