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

## Pressure as a clock: measured vs forecast daily cycles (original 10 cities)

`pressure_clock_<city>.png` · `pressure_clock_<city>.csv` for the same 10 cities · `pressure_clock_shifts.csv`

Average day of measured and forecast (t2, issued 2 days before) pressure and temperature, as the difference from the
daily mean, in local standard time. Data from 2024-06-24 on, after OpenWeather changed its pressure feed (#30).

The sun drives a twice-daily atmospheric pressure tide that peaks at fixed local times (about 09:00–10:00 and
22:00–23:00). It is a clock both data sets must share: when measured and forecast pressure peak together, the
timestamps of the two series agree, so any offset left in the temperature curves comes from the forecast itself.

| City | Pressure offset (h) | Temperature offset (h) | Reading |
|---|---|---|---|
| London | +0.55 | +0.35 | in step |
| Madrid | +0.15 | +0.10 | in step |
| New York | +0.10 | +0.20 | in step |
| Moscow | +0.45 | +0.55 | in step |
| Tokyo | +0.10 | −0.25 | in step |
| São Paulo | +0.35 | +0.40 | in step |
| Sydney | +0.20 | +0.30 | in step |
| Asunción | +0.25 | +0.20 | in step |
| **Nairobi** | 0.00 | **+1.25** | temperature forecast runs early |
| **Lagos** | 0.00 | **+1.15** | temperature forecast early and flattened (daily swing 1.8 °C vs 4.8 °C measured) |

- Offset = hours by which the forecast curve runs ahead of the measured one (+ = early), from the best overlap of the
  two smooth curves (`pressure_clock_shifts.csv`). Offsets under 0.75 h, a quarter of the 3-hour sampling step, are
  read as in step.
- Lines are least-squares fits through the 8 three-hourly means (24 h and 12 h harmonics for pressure, plus 8 h for
  temperature); the dots are the means themselves.
- The tide is strong near the equator (±2–3 hPa in Nairobi and Lagos) and weak at high latitude (±0.3 hPa in Moscow),
  where the pressure curves are noisier.
- Times are local *standard* time all year (UTC offsets as in `roboclimate/common.py`), so daylight saving does not
  affect the curves. Asunción has used UTC−3 all year since October 2024; the chart keeps the UTC−4 used in the code.
- Nairobi's early temperature cycle is largest in the sunny Dec–May months and smallest in the overcast Jun–Aug, and
  humidity shows the same lead: it points to how fast the model's land surface heats and cools, not to cloud timing.
  Lagos' forecast flattens the daily cycle to about a third of the measured swing, possibly because its grid cell
  blends sea or lagoon with land.

## Temperature history (original 10 cities)

`temperature_history_<city>.png` · `temperature_history_<city>.csv` for the same 10 cities ·
`temperature_history_summary.csv`

Measured temperature over the whole record: the band is each day's lowest to highest 3-hourly reading, the line the
30-day average of the daily mean. All cities share the same temperature scale and time window, so charts can be
compared directly (Moscow's −28 °C to +34 °C against Lagos' 21–38 °C).

| City | From | Readings | Mean of daily means | Highest reading | Lowest reading |
|---|---|---|---|---|---|
| London | 28 Nov 2019 | 16,504 | 12.5 °C | 36.6 °C (13 Aug 2026) | −3.9 °C (18 Jan 2024) |
| Madrid | 11 Jun 2020 | 14,929 | 16.9 °C | 40.9 °C (14 Aug 2021) | −7.3 °C (12 Jan 2021) |
| New York | 11 Jun 2020 | 14,930 | 14.3 °C | 38.4 °C (2 Jul 2026) | −15.3 °C (8 Feb 2026) |
| Moscow | 27 Jan 2021 | 13,095 | 8.3 °C | 34.5 °C (12 Jul 2025) | −28.4 °C (17 Jan 2026) |
| Tokyo | 27 Jan 2021 | 13,095 | 18.4 °C | 37.9 °C (8 Jul 2024) | −2.2 °C (8 Feb 2026) |
| São Paulo | 11 Jun 2020 | 14,931 | 20.5 °C | 36.8 °C (2 Oct 2020) | 4.7 °C (30 Jul 2021) |
| Sydney | 11 Jun 2020 | 14,931 | 17.9 °C | 42.1 °C (28 Jan 2025) | 4.5 °C (19 Jul 2023) |
| Asunción | 27 Jan 2021 | 13,094 | 23.8 °C | 42.9 °C (18 Feb 2026) | 0.7 °C (29 Jun 2021) |
| Nairobi | 27 Jan 2021 | 13,082 | 19.5 °C | 30.9 °C (26 Jan 2026) | 9.6 °C (28 Aug 2021) |
| Lagos | 27 Jan 2021 | 13,093 | 27.9 °C | 38.1 °C (15 Mar 2024) | 21.1 °C (7 Jul 2021) |

All records end on 10 Oct 2026.

- Collection outages: no data from 15 Jan 2022 to 9 Mar 2023 and from 27 May to 24 Jun 2024 (shaded). Days with fewer
  than 6 of their 8 readings are left blank. The mean of daily means covers uneven numbers of each season, so treat it
  as a rough level, not a climate normal.
- Extremes are of the 3-hourly readings (UTC 00, 03, … 21), so the true daily highs and lows can be more extreme.
- Excluded as corrupted (`EXCLUDED_READINGS` in `make_charts.py`), Nairobi only: 12 May 2021 15:00 – 13 May 2021 18:00
  UTC (10 readings falling to 5.1 °C, 4–10 °C below every forecast made for them, then jumping to 42.9–47.9 °C,
  21–29 °C above them; Nairobi's record high is about 31 °C), and 1 Mar 2025 03:00 UTC (a single 5.6 °C reading at
  100% humidity between 17.6 and 18.9 °C). No other city has a reading more than 10 °C outside all five of its
  forecasts except during sudden storms the forecasts missed (Moscow, São Paulo, Asunción), which are kept.
- CSV columns: daily `min`, `max`, `mean`, number of `readings` and the 30-day average `avg30`.
