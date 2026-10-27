"""Rebuild the charts in docs/analysis from the roboclimate CSV files.

Produces, next to this script:
- london_temp_mase_by_season.png / .csv : MASE of London's 1- and 5-day temperature forecasts by season and year
- wind_rose_<city>.png / .csv           : direction a city's wind blows from (8 sectors), by Beaufort band and season,
                                          for each of the original 10 cities
- pressure_clock_<city>.png / .csv      : average day of measured vs forecast (t2) pressure and temperature;
                                          the pressure tide is a fixed clock, so a temperature offset is the forecast's
- pressure_clock_shifts.csv             : hours each city's forecast curve runs ahead (+) or behind (-), per variable
- temperature_history_<city>.png / .csv : measured temperature over the whole record (daily range, 30-day average)
- temperature_history_summary.csv       : period, readings, mean and extremes per city
- humidity_history_<city>.png / .csv    : the same for relative humidity
- humidity_history_summary.csv          : period, readings, mean, driest reading and share of damp readings per city
- humidity_by_month.png / .csv          : average humidity by calendar month for each city (whole record and each year)
- wind_speed_history_<city>.png / .csv  : the same history chart for wind speed, in km/h
- wind_speed_history_summary.csv        : period, readings, mean, highest reading and share of fresh winds per city
- wind_speed_by_month.png / .csv        : average wind speed by calendar month for each city

Needs weather_<city>.csv, temp/join_<city>.csv and pressure/join_<city>.csv (written by the Java or Python data analysis) in the data folder.

USAGE (from the repo root):
    bin/python docs/analysis/make_charts.py [--data csv_files] [--cities london madrid ...]
"""
import argparse
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use('Agg')
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402  (after selecting the non-interactive backend)

OUT = os.path.dirname(os.path.abspath(__file__))
THREE_HOURS = 3 * 3600

# palette: reference instance of the dataviz skill (light surface), validated with its palette validator
INK, INK2, MUTED, GRID, AXIS, SURF = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7', '#fcfcfb'
CATEGORICAL = ['#2a78d6', '#eb6834']                       # slots 1-2: t1, t5
BLUE_RAMP = ['#86b6ef', '#3987e5', '#1c5cab', '#0d366b']   # ordinal steps 250/400/550/700: Beaufort bands
SINGLE = '#2a78d6'

SEASON_OF_MONTH = {12: 'Winter', 1: 'Winter', 2: 'Winter', 3: 'Spring', 4: 'Spring', 5: 'Spring',
                   6: 'Summer', 7: 'Summer', 8: 'Summer', 9: 'Autumn', 10: 'Autumn', 11: 'Autumn'}
SEASON_LABEL = {'Winter': 'Winter (Dec–Feb)', 'Spring': 'Spring (Mar–May)', 'Summer': 'Summer (Jun–Aug)',
                'Autumn': 'Autumn (Sep–Nov)'}
SEASONS = ['Winter', 'Spring', 'Summer', 'Autumn']

# original cities: display name and climate, which decides how the Dec-Feb, Mar-May, Jun-Aug, Sep-Nov panels are named
CITIES = {'london': ('London', 'north'), 'madrid': ('Madrid', 'north'), 'newyork': ('New York', 'north'),
          'moscow': ('Moscow', 'north'), 'tokyo': ('Tokyo', 'north'), 'saopaulo': ('São Paulo', 'south'),
          'sydney': ('Sydney', 'south'), 'asuncion': ('Asunción', 'south'), 'nairobi': ('Nairobi', 'tropical'),
          'lagos': ('Lagos', 'tropical')}
# standard (non-DST) UTC offsets, as in roboclimate/common.py CITY_PARAMS
UTC_OFFSET = {'london': 0, 'madrid': 1, 'newyork': -5, 'moscow': 3, 'tokyo': 9, 'saopaulo': -3, 'sydney': 10,
              'asuncion': -4, 'nairobi': 3, 'lagos': 1}
# corrupted measurement episodes, excluded from the history charts of the listed variables: (first, last) reading in
# UTC, inclusive, and the variables affected.
# Nairobi, 12-13 May 2021: readings fall 4-10 °C below all five forecasts made for them (down to 5.1 °C), then jump
# 21-29 °C above them (42.9-47.9 °C; Nairobi's record high is about 31 °C). Same week as Moscow's source change
# (#30). Nairobi, 1 Mar 2025 03:00: a single 5.6 °C reading at 100% humidity between 17.6 and 18.9 °C, 11 °C below
# all forecasts. In both the whole reading is dropped.
# Isolated humidity readings 40+ points from both neighbours in the same direction and 30+ points outside all five
# forecasts (the only three in the 10 cities; their temperatures look normal): Sydney 21 Dec 2020 18:00, 10% between
# 100% and 93%; Sydney 25 Mar 2021 06:00, 90% between 42% and 43%; Lagos 12 Feb 2024 09:00, 17% between 94% and 66%.
# Isolated storm-force wind speeds: above 20 m/s (72 km/h) and 10+ m/s above both neighbours and above all five
# forecasts (the only two in the 10 cities): Lagos 3 Apr 2023 09:00, 32.4 m/s between 1.0 and 3.6 m/s (forecasts up
# to 5.0), and 12 Oct 2024 21:00, 24.2 m/s between 5.3 and 2.6 m/s (forecasts up to 5.4).
EXCLUDED_READINGS = {
    'nairobi': [('2021-05-12 15:00', '2021-05-13 18:00', ('temp', 'humidity')),
                ('2025-03-01 03:00', '2025-03-01 03:00', ('temp', 'humidity'))],
    'sydney': [('2020-12-21 18:00', '2020-12-21 18:00', ('humidity',)),
               ('2021-03-25 06:00', '2021-03-25 06:00', ('humidity',))],
    'lagos': [('2024-02-12 09:00', '2024-02-12 09:00', ('humidity',)),
              ('2023-04-03 09:00', '2023-04-03 09:00', ('wind_speed',)),
              ('2024-10-12 21:00', '2024-10-12 21:00', ('wind_speed',))]}
# suspect stretches left out of the by-month charts only (the history charts show everything as measured), per variable
# and city: (first, last) reading in UTC, inclusive. Both are on the measurement side, as the forecasts stay normal (#30).
# 19 May 2021 to the last reading before the outage: wind speed in New York, Tokyo and Sydney drops to about a third of
# normal (12.3 -> 6.1, 17.7 -> 5.4 and 17.9 -> 6.4 km/h) on the same day and is back at 17, 18 and 17 km/h after it.
# 9 Jun - 31 Jul 2026: wind speed in Tokyo and Sydney falls below half of normal (July 7 and 6 km/h against about 15)
# and recovers gradually in August; Madrid, São Paulo, Asunción, Nairobi and London dip less (20-40%) and are kept.
SUSPECT_2021 = ('2021-05-19 00:00', '2022-01-15 23:59')
SUSPECT_2026 = ('2026-06-09 00:00', '2026-07-31 23:59')
SUSPECT_PERIODS = {'wind_speed': {'newyork': [SUSPECT_2021], 'tokyo': [SUSPECT_2021, SUSPECT_2026],
                                  'sydney': [SUSPECT_2021, SUSPECT_2026]}}
MONTH_BLOCKS = ['Dec–Feb', 'Mar–May', 'Jun–Aug', 'Sep–Nov']
BLOCK_OF_MONTH = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}
PANEL_TITLES = {'north': ['Winter', 'Spring', 'Summer', 'Autumn'],
                'south': ['Summer', 'Autumn', 'Winter', 'Spring'],
                'tropical': [None, None, None, None]}      # near the equator: wet/dry seasons, so months only


def mase_pairs(join_df, horizons=(1, 5)):
    """Error pairs behind MASE, one row per target that has a naive reference.

    Same rule as roboclimate.metrics.mean_absolute_scaled_error: the naive forecast for horizon x is the actual
    value 8*x rows earlier, counted only when it is exactly x days earlier.
    """
    dts = join_df.dt.astype('int64').to_numpy()
    actual = join_df.temp.to_numpy(float)
    rows = []
    for x in horizons:
        period = 8 * x
        forecast = join_df[f't{x}'].to_numpy(float)
        for i in range(period, len(dts)):
            if dts[i] - dts[i - period] == period * THREE_HOURS:
                rows.append((x, dts[i], abs(actual[i] - forecast[i]), abs(actual[i] - actual[i - period])))
    pairs = pd.DataFrame(rows, columns=['x', 'dt', 'err_forecast', 'err_naive'])
    pairs['ts'] = pd.to_datetime(pairs.dt, unit='s', utc=True)
    return pairs


def chart_mase_by_season(data):
    pairs = mase_pairs(pd.read_csv(os.path.join(data, 'temp', 'join_london.csv')))
    month = pairs.ts.dt.month
    pairs['season'] = month.map(SEASON_OF_MONTH)
    pairs['syear'] = pairs.ts.dt.year + (month == 12).astype(int)     # December belongs to the following winter
    g = pairs.groupby(['season', 'syear', 'x']).agg(f=('err_forecast', 'sum'), n=('err_naive', 'sum'),
                                                    c=('err_forecast', 'size'))
    g['mase'] = np.where(g.c >= 400, g.f / g.n, np.nan)              # omit seasons mostly lost to outages
    table = g.mase.unstack('x').rename(columns={1: 't1 (1 day ahead)', 5: 't5 (5 days ahead)'})
    table.index = table.index.set_levels([SEASON_LABEL[s] for s in table.index.levels[0]], level=0)
    table.to_csv(os.path.join(OUT, 'london_temp_mase_by_season.csv'), float_format='%.3f')

    years = np.arange(2020, int(pairs.syear.max()) + 1)
    series = [(1, CATEGORICAL[0], 't1', -0.08), (5, CATEGORICAL[1], 't5', +0.08)]   # dodge keeps equal values visible
    plt.rcParams.update({'font.size': 10, 'axes.edgecolor': AXIS, 'xtick.color': MUTED, 'ytick.color': MUTED,
                         'axes.labelcolor': INK2, 'text.color': INK})
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.2), sharex=True, sharey=True, facecolor=SURF)
    for ax, season in zip(axes.flat, SEASONS):
        ax.set_facecolor(SURF)
        ax.axvspan(2021.5, 2022.5, color='#f0efec', zorder=0, lw=0)
        ax.text(2022, 0.04, 'no data\n(outage)', ha='center', va='bottom', fontsize=8, color=MUTED)
        ends = []
        for x, color, label, dx in series:
            s = g.loc[season].mase.unstack('x')[x].reindex(years)
            ax.plot(years + dx, s.to_numpy(), color=color, lw=2, marker='o', ms=6.5, mec=SURF, mew=2, zorder=3,
                    solid_capstyle='round')
            last = s.last_valid_index()
            if last is not None:
                ends.append([label, last + dx, s[last], 0])
        if len(ends) == 2 and abs(ends[0][2] - ends[1][2]) < 0.04:  # keep close end labels apart
            low, high = sorted(ends, key=lambda e: e[2])
            low[3], high[3] = -7, 7
        for label, x_end, y_end, dy in ends:
            ax.annotate(f"{label} {y_end:.2f}", (x_end, y_end), xytext=(8, dy), textcoords='offset points',
                        va='center', fontsize=8.5, color=INK2)
        ax.set_title(SEASON_LABEL[season], loc='left', fontsize=11, color=INK, pad=6)
        ax.grid(axis='y', color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for spine in ('top', 'right', 'left'):
            ax.spines[spine].set_visible(False)
        ax.tick_params(length=0)
        ax.set_xlim(years[0] - 0.4, years[-1] + 0.95)
        ax.set_ylim(0, 0.7)
        ax.set_xticks(years)
    for ax in axes[:, 0]:
        ax.set_ylabel('MASE')
    handles = [plt.Line2D([], [], color=c, lw=2, marker='o', ms=6.5, mec=SURF, mew=2) for _, c, _, _ in series]
    fig.legend(handles, ['t1 — forecast made the evening before', 't5 — forecast made 5 days before'],
               loc='upper left', bbox_to_anchor=(0.06, 0.915), ncol=2, frameon=False, fontsize=9.5, labelcolor=INK2)
    fig.suptitle('London temperature forecasts: MASE by season', x=0.06, y=0.99, ha='left', fontsize=14,
                 fontweight='bold', color=INK)
    fig.text(0.06, 0.935, "Lower is better; below 1 means the forecast beats a naive 'same time, x days earlier' "
             "guess. Seasons with fewer than 400 readings are omitted.", fontsize=9.5, color=INK2)
    first, last_ts = pairs.ts.min(), pairs.ts.max()
    fig.text(0.06, 0.012, f'Source: roboclimate, OpenWeather forecasts vs measurements, {first:%b %Y} – '
             f'{last_ts:%b %Y}. Winter is labelled by the year of its January.', fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0.04, 0.03, 1, 0.89))
    fig.savefig(os.path.join(OUT, 'london_temp_mase_by_season.png'), dpi=200, facecolor=SURF)
    plt.close(fig)


def chart_wind_rose(data, city):
    display, climate = CITIES.get(city, (city.title(), 'tropical'))
    w = pd.read_csv(os.path.join(data, f'weather_{city}.csv')).dropna(subset=['wind_deg', 'wind_speed'])
    w['ts'] = pd.to_datetime(w.dt.astype('int64'), unit='s', utc=True)
    # exclude calm readings (< 1 m/s = 3.6 km/h) and exactly 0°, which (as in METAR reports) codes calm/variable wind;
    # a genuine north wind is recorded as 360°, so 360° is kept and falls in the N sector
    v = w[(w.wind_speed >= 1.0) & (w.wind_deg != 0)].copy()
    v['kmh'] = v.wind_speed * 3.6
    names = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    v['sector'] = (((v.wind_deg % 360) + 22.5) // 45).astype(int) % 8
    v['block'] = v.ts.dt.month.map(BLOCK_OF_MONTH)
    # Beaufort thresholds in km/h: force 3 from 12, force 4 from 20, force 5 from 29
    bands = [(0, 'Light  4–11 km/h'), (12, 'Gentle  12–19 km/h'), (20, 'Moderate  20–28 km/h'),
             (29, 'Fresh or stronger  ≥ 29 km/h')]
    v['band'] = pd.cut(v.kmh, [b[0] for b in bands] + [999], right=False, labels=[b[1] for b in bands])
    share = v.pivot_table(index='sector', columns='band', values='wind_deg', aggfunc='size',
                          observed=False).reindex(range(8)).fillna(0) / len(v)
    seasons = v.pivot_table(index='sector', columns='block', values='wind_deg', aggfunc='size') \
        .reindex(index=range(8), columns=range(4)).fillna(0)
    seasons = seasons / seasons.sum()
    titles = [f"{t} ({m})" if t else m for t, m in zip(PANEL_TITLES[climate], MONTH_BLOCKS)]
    table = share.copy()
    table.index = names
    table['total'] = table.sum(axis=1)
    table.join(seasons.set_axis(names).set_axis([f"months_{m}" for m in MONTH_BLOCKS], axis=1)) \
        .to_csv(os.path.join(OUT, f'wind_rose_{city}.csv'), float_format='%.4f')
    # radial scales: the main rose fits its longest bar; the four seasonal roses share one scale
    rmax = np.ceil((share.sum(axis=1).max() + 0.03) / 0.05) * 0.05
    rmax_season = np.ceil((seasons.to_numpy().max() + 0.03) / 0.05) * 0.05
    step = 0.1 if rmax > 0.25 else 0.05
    rticks = list(np.arange(step, rmax - 0.01, step))
    rticks_season = [round(rmax_season / 2 / 0.05) * 0.05, round(rmax_season * 0.9 / 0.05) * 0.05]

    theta = np.radians(np.arange(8) * 45)
    width = np.radians(45) * 0.86

    def quietest_gap(values):
        """Angle (degrees) of the boundary between the two neighbouring sectors with the shortest bars."""
        i = min(range(8), key=lambda k: max(values[k], values[(k + 1) % 8]))
        return i * 45 + 22.5

    def style(ax, rmax, rticks, label_size, pad, rlabel_angle):
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_facecolor(SURF)
        ax.set_ylim(0, rmax)
        ax.set_xticks(theta)
        ax.set_xticklabels(names, fontsize=label_size, color=INK2)
        ax.set_yticks(rticks)
        ax.set_yticklabels([f"{t:.0%}" for t in rticks], fontsize=label_size - 2.5, color=MUTED)
        ax.set_rlabel_position(rlabel_angle)            # radial % labels where the bars are shortest
        ax.grid(color=GRID, lw=0.8)
        ax.spines['polar'].set_color(GRID)
        ax.tick_params(axis='x', pad=pad)

    fig = plt.figure(figsize=(12, 8.6), facecolor=SURF)
    ax = fig.add_axes([0.05, 0.17, 0.46, 0.62], projection='polar')
    bottom = np.zeros(8)
    for column, color in zip(share.columns, BLUE_RAMP):
        values = share[column].to_numpy()
        ax.bar(theta, values, width=width, bottom=bottom, color=color, edgecolor=SURF, linewidth=1.5,
               label=column, zorder=3)
        bottom += values
    style(ax, rmax, rticks, 12, 4, quietest_gap(bottom))
    for i in np.argsort(bottom)[::-1][:3]:              # label the three dominant directions only
        ax.annotate(f"{bottom[i]:.0%}", (theta[i], bottom[i]), ha='center', va='center', fontsize=10,
                    fontweight='bold', color=INK, bbox=dict(boxstyle='round,pad=0.25', fc=SURF, ec='none'))
    ax.set_title('All year', fontsize=12, color=INK, pad=22)
    fig.legend(*ax.get_legend_handles_labels(), loc='lower left', bbox_to_anchor=(0.05, 0.015), ncol=2,
               frameon=False, fontsize=9.5, labelcolor=INK2, title='Wind speed (Beaufort scale)',
               title_fontsize=9.5, alignment='left')
    size = 0.165
    for (x, y), block, title in zip([(0.605, 0.47), (0.815, 0.47), (0.605, 0.08), (0.815, 0.08)], range(4), titles):
        a = fig.add_axes([x, y, size, size * 12 / 8.6], projection='polar')   # keep the roses circular
        values = seasons[block].to_numpy()
        a.bar(theta, values, width=width, color=SINGLE, edgecolor=SURF, linewidth=1.2, zorder=3)
        style(a, rmax_season, rticks_season, 8.5, 1, quietest_gap(values))
        k = int(np.argmax(values))
        a.annotate(f"{names[k]} {values[k]:.0%}", (theta[k], values[k]), ha='center', va='center', fontsize=8.5,
                   color=INK, bbox=dict(boxstyle='round,pad=0.2', fc=SURF, ec='none'))
        a.set_title(title, fontsize=11, color=INK, pad=16)
    fig.text(0.04, 0.955, f"Where {display}'s wind comes from", fontsize=15, fontweight='bold', color=INK)
    fig.text(0.04, 0.92, f"Share of 3-hourly readings by the direction the wind blows from, {v.ts.min():%b %Y} – "
             f"{v.ts.max():%b %Y}. Calm readings (< 3.6 km/h) and 0° 'variable' placeholders excluded "
             f"({len(v):,} readings).", fontsize=9.5, color=INK2)
    fig.text(0.605, 0.855, 'By season (same scale)' if climate != 'tropical' else 'By months (same scale)',
             fontsize=10.5, color=INK2)
    fig.text(0.98, 0.012, 'Source: roboclimate, OpenWeather measurements', fontsize=8, color=MUTED, ha='right')
    fig.savefig(os.path.join(OUT, f'wind_rose_{city}.png'), dpi=200, facecolor=SURF)
    plt.close(fig)


def harmonic_fit(hours, values, periods):
    """Least-squares fit of a daily curve (mean + one sine/cosine pair per period, in hours); returns f(hours)."""
    def design(h):
        return np.column_stack([np.ones_like(h)] + [f(2 * np.pi * h / p) for p in periods for f in (np.cos, np.sin)])
    coef = np.linalg.lstsq(design(hours), values, rcond=None)[0]
    return lambda h: design(np.asarray(h, float)) @ coef


def curve_shift(f_forecast, f_measured):
    """Hours by which the forecast curve runs ahead of the measured one (positive = early), from the best overlap."""
    grid = np.arange(0, 24, 0.05)
    taus = np.arange(-4, 4.001, 0.05)
    errors = [np.mean((f_forecast(grid) - f_measured((grid + tau) % 24)) ** 2) for tau in taus]
    return taus[int(np.argmin(errors))]


def chart_pressure_clock(data, city, since='2024-06-24'):
    """Average day of measured and forecast (t2) pressure and temperature, in local standard time.

    The twice-daily atmospheric pressure tide happens at fixed solar times, so when measured and forecast pressure
    peak together the two data sets share a clock, and any offset left in the temperature curves belongs to the
    forecast itself. Data from `since` on: OpenWeather changed its pressure feed during the June 2024 outage (#30).
    """
    display = CITIES.get(city, (city.title(), ''))[0]
    offset = UTC_OFFSET[city]
    start = pd.Timestamp(since, tz='UTC').timestamp()
    xs = np.linspace(0, 24, 481)
    panels, rows = [], []
    for var, unit, periods in [('pressure', 'hPa', [24, 12]), ('temp', '°C', [24, 12, 8])]:
        j = pd.read_csv(os.path.join(data, var, f'join_{city}.csv'))
        j = j[j.dt >= start]
        hour = ((j.dt.astype('int64') % 86400) // 3600 + offset) % 24
        curves = {}
        for col, name in [(var, 'measured'), ('t2', 'forecast')]:
            mean = j[col].groupby(hour).mean().sort_index()
            anomaly = mean - mean.mean()
            curves[name] = (anomaly.index.to_numpy(float), anomaly.to_numpy(), harmonic_fit(anomaly.index.to_numpy(float), anomaly.to_numpy(), periods))
            rows += [(var, name, h, a) for h, a in anomaly.items()]
        panels.append((var, unit, curves, curve_shift(curves['forecast'][2], curves['measured'][2])))
    pd.DataFrame(rows, columns=['variable', 'series', 'local_hour', 'difference_from_daily_mean']) \
        .to_csv(os.path.join(OUT, f'pressure_clock_{city}.csv'), index=False, float_format='%.3f')

    tol = 0.75          # a quarter of the 3-hour sampling step: smaller offsets are not resolved

    def describe(shift):
        if abs(shift) < tol:
            return 'in step with the measurements'
        return f"about {abs(shift):.1f} h {'early' if shift > 0 else 'late'}"

    plt.rcParams.update({'font.size': 10, 'axes.edgecolor': AXIS, 'xtick.color': MUTED, 'ytick.color': MUTED,
                         'axes.labelcolor': INK2, 'text.color': INK})
    fig, axes = plt.subplots(2, 1, figsize=(9, 8.2), sharex=True, facecolor=SURF)
    for ax, (var, unit, curves, shift) in zip(axes, panels):
        ax.set_facecolor(SURF)
        ax.grid(axis='y', color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
        ax.axhline(0, color=AXIS, lw=0.8)
        for name, color, label, z in [('measured', CATEGORICAL[0], 'Measured', 3),
                                      ('forecast', CATEGORICAL[1], 'Forecast (2 days ahead)', 2)]:
            h, y, f = curves[name]
            ax.plot(xs, f(xs), color=color, lw=2, zorder=z, label=label)
            ax.scatter(np.r_[h, h[0] + 24], np.r_[y, y[0]],   # repeat the first reading a day later
                       s=64, color=color, edgecolor=SURF, linewidth=2,
                       zorder=z + 1)
        measured = curves['measured'][2](xs)
        if var == 'pressure':
            for lo, hi in [(4, 14), (16, 28)]:                       # morning and evening tide peaks
                window = np.arange(lo, hi, 0.05)                     # the evening one may fall after midnight
                peak = window[np.argmax(curves['measured'][2](window % 24))] % 24
                ax.axvline(peak, color=MUTED, lw=1, ls=(0, (3, 3)), zorder=1)
                ax.text(peak + 0.25, 0.97, f'peak {int(round(peak * 60)) // 60 % 24:02d}:{int(round(peak * 60)) % 60:02d}',
                        transform=ax.get_xaxis_transform(), color=INK2, fontsize=9, va='top')
            ax.set_title(f'Pressure: forecast {describe(shift)}', loc='left', fontsize=11.5, color=INK, pad=8)
            ax.text(0.01, 0.03, 'Twice-daily atmospheric tide, set by the sun: a fixed clock', color=MUTED,
                    fontsize=8.5, transform=ax.transAxes)
        else:
            # horizontal gap between the curves at half the measured daily swing, on the rise and on the fall
            forecast = curves['forecast'][2](xs)
            swing_m, swing_f = np.ptp(measured), np.ptp(forecast)
            level = measured.min() + 0.5 * swing_m
            comparable = 0.7 <= swing_f / swing_m <= 1.4   # with very different swings the gaps mislead
            for direction in ((1, -1) if comparable and abs(shift) >= tol else ()):
                crossings = np.where(np.diff(np.sign(measured - level)) == 2 * direction)[0]
                f_cross = np.where(np.diff(np.sign(forecast - level)) == 2 * direction)[0]
                if len(crossings) and len(f_cross):
                    xm, xf = xs[crossings[0]], xs[f_cross[np.argmin(abs(xs[f_cross] - xs[crossings[0]]))]]
                    if abs(xm - xf) >= 0.5:
                        ax.annotate('', xy=(xf, level), xytext=(xm, level),
                                    arrowprops=dict(arrowstyle='<->', color=INK2, lw=1.2))
                        ax.text((xm + xf) / 2, level, f'{abs(xm - xf):.1f} h\n', ha='center', va='bottom',
                                color=INK, fontsize=9.5, fontweight='bold')
            swing_note = '' if comparable else f'; daily swing {swing_f:.1f} °C forecast vs {swing_m:.1f} °C measured'
            ax.set_title(f'Temperature: forecast {describe(shift)}{swing_note}', loc='left', fontsize=11.5,
                         color=INK, pad=8)
        ax.set_ylabel(f'difference from daily mean ({unit})')
    axes[1].set_xticks(range(0, 25, 3))
    axes[1].set_xticklabels([f'{h:02d}:00' for h in range(0, 25, 3)])
    axes[1].set_xlim(0, 24)
    axes[1].set_xlabel(f'local standard time (UTC{offset:+d})'.replace('-', '−'))
    axes[0].legend(loc='lower left', bbox_to_anchor=(0, 1.07), ncol=2, frameon=False, fontsize=9.5, labelcolor=INK2)
    p_shift, t_shift = panels[0][3], panels[1][3]
    if abs(p_shift) >= tol:
        verdict = 'measured and forecast pressure disagree on the time'
    elif t_shift - p_shift >= tol:
        verdict = 'pressure keeps time, temperature runs early'
    elif t_shift - p_shift <= -tol:
        verdict = 'pressure keeps time, temperature runs late'
    else:
        verdict = 'pressure and temperature both in step'
    if not comparable:
        verdict = verdict.replace('temperature runs', 'temperature').replace(', ', '; ') + \
            (' and flattened' if swing_f < swing_m else ' and exaggerated')

    fig.suptitle(f'{display}: {verdict}', x=0.075, y=0.985, ha='left', fontsize=14, fontweight='bold', color=INK)
    last = pd.to_datetime(j.dt.max(), unit='s')
    fig.text(0.075, 0.94, f'Average day, {pd.Timestamp(since):%d %b %Y} – {last:%b %Y}. '
             'Dots: mean of the 3-hourly readings; lines: smooth fit through them.', fontsize=9, color=INK2)
    fig.text(0.075, 0.012, 'Measured = OpenWeather current weather; forecast = OpenWeather 5-day forecast issued '
             '2 days before (t2). Source: roboclimate.', fontsize=7.8, color=MUTED)
    fig.tight_layout(rect=(0.03, 0.03, 1, 0.965))
    fig.savefig(os.path.join(OUT, f'pressure_clock_{city}.png'), dpi=150, facecolor=SURF)
    plt.close(fig)
    return p_shift, t_shift


# variables with a history chart: file stem and title, unit, factor from the data's unit, which extremes to mark (and
# which of them to label above the point), readings share to report, footer; by_month is the spec of the by-month chart
# (title, words for the extremes, unit of the gap, y label and range, CSV column), None when there is no such chart
HISTORY_VARIABLES = {
    'temp': dict(stem='temperature', title='temperature', unit='°C', factor=1, fmt='{:.1f} °C', marks=('max', 'min'),
                 above=('max',), zero_line=True, label_box=False, share_at_least=None, by_month=None,
                 footer='Source: roboclimate. Extremes are of the 3-hourly readings, so true daily highs and lows '
                        'can be more extreme.'),
    'humidity': dict(stem='humidity', title='relative humidity', unit='%', factor=1, fmt='{:.0f}%', marks=('min',),
                     above=('min',), zero_line=False, label_box=True, share_at_least=90,
                     by_month=dict(title='humidity', words=('wettest', 'driest'), gap_unit='points',
                                   ylabel='relative humidity (%)', ylim=(20, 100), column='humidity'),
                     footer='Source: roboclimate. The band and the marked low are of the 3-hourly readings, so true '
                            'daily extremes can be more extreme.'),
    'wind_speed': dict(stem='wind_speed', title='wind speed', unit='km/h', factor=3.6, fmt='{:.0f} km/h',
                       marks=('max',), above=('max',), zero_line=False, label_box=True, share_at_least=29,
                       by_month=dict(title='wind speed', words=('windiest', 'calmest'), gap_unit='km/h',
                                     ylabel='wind speed (km/h)', ylim=None, column='wind_speed_kmh'),
                       footer='Source: roboclimate. 3-hourly readings of OpenWeather current wind speed (m/s × 3.6), '
                              'so gusts between readings are not captured.')}


def measurements(data, city, variable):
    """Measured values of `variable` indexed by UTC time, without the EXCLUDED_READINGS episodes."""
    w = pd.read_csv(os.path.join(data, f'weather_{city}.csv')).drop_duplicates('dt')
    w['ts'] = pd.to_datetime(w.dt.astype('int64'), unit='s')
    values = w.set_index('ts')[variable].sort_index()
    for first, last, variables in EXCLUDED_READINGS.get(city, []):
        if variable in variables:
            values = values[(values.index < pd.Timestamp(first)) | (values.index > pd.Timestamp(last))]
    return values


def chart_history(data, city, variable, ylim):
    """Measured temperature or relative humidity over the whole record: daily range band, 30-day average of the daily
    mean and the marked extremes.

    Readings in the EXCLUDED_READINGS episodes are dropped for the variables listed there; every other reading
    is plotted as measured. Days with fewer than 6 of their 8 readings are left blank, and gaps of 3 days or
    more are shaded.
    """
    spec = HISTORY_VARIABLES[variable]
    display = CITIES.get(city, (city.title(), ''))[0]
    values = measurements(data, city, variable) * spec['factor']
    daily = values.resample('D').agg(['min', 'max', 'mean', 'size'])
    daily.loc[daily['size'] < 6, ['min', 'max', 'mean']] = np.nan
    daily['avg30'] = daily['mean'].rolling(30, center=True, min_periods=20).mean()
    daily.rename(columns={'size': 'readings'}).rename_axis('date') \
        .to_csv(os.path.join(OUT, f"{spec['stem']}_history_{city}.csv"), float_format='%.2f')
    step = values.index.to_series().diff()
    gaps = [(t - d, t) for t, d in step[step >= pd.Timedelta('3D')].items()]

    plt.rcParams.update({'font.size': 10, 'axes.edgecolor': AXIS, 'xtick.color': MUTED, 'ytick.color': MUTED,
                         'axes.labelcolor': INK2, 'text.color': INK})
    fig, ax = plt.subplots(figsize=(13, 5.6), facecolor=SURF)
    ax.set_facecolor(SURF)
    ax.fill_between(daily.index, daily['min'], daily['max'], color=BLUE_RAMP[0], alpha=0.55, lw=0, step='mid',
                    label='Daily range (lowest–highest reading)')
    ax.plot(daily.index, daily.avg30, color=SINGLE, lw=2, label='30-day average of the daily mean')
    for start, end in gaps:
        ax.axvspan(start, end, color='#f0efec', lw=0, zorder=0)
        if (end - start).days > 60:
            ax.text(start + (end - start) / 2, ylim[0] + 2, f'no data\n{start:%b %Y} – {end:%b %Y}', ha='center',
                    va='bottom', fontsize=8.5, color=MUTED)
    for mark in spec['marks']:
        ts = values.idxmax() if mark == 'max' else values.idxmin()
        above = mark in spec['above']
        ax.scatter([ts], [values[ts]], s=40, color=INK, zorder=5, edgecolor=SURF, linewidth=1.5)
        ax.annotate(f"{spec['fmt'].format(values[ts])}  {ts:%d %b %Y}", (ts, values[ts]),
                    xytext=(8, 4 if above else -4), textcoords='offset points', va='bottom' if above else 'top',
                    fontsize=9, color=INK, zorder=6,
                    bbox=dict(boxstyle='round,pad=0.2', fc=SURF, ec='none', alpha=0.85) if spec['label_box'] else None)
    if spec['zero_line']:
        ax.axhline(0, color=AXIS, lw=0.8)
    ax.grid(axis='y', color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ['top', 'right']:
        ax.spines[side].set_visible(False)
    ax.set_ylabel(spec['unit'])
    ax.set_ylim(*ylim)
    if variable == 'humidity':
        ax.set_yticks(range(0, 101, 20))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_xlim(pd.Timestamp('2019-11-01'), values.index.max() + pd.Timedelta('10D'))   # same window for every city
    ax.legend(loc='lower left', bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=9.5, labelcolor=INK2)
    fig.suptitle(f"{display} {spec['title']}, measured", x=0.06, y=0.97, ha='left', fontsize=14, fontweight='bold',
                 color=INK)
    fig.text(0.06, 0.905, f'{values.index.min():%d %b %Y} – {values.index.max():%d %b %Y}, {len(values):,} '
             'three-hourly readings (OpenWeather current weather). Same scale for every city. Days with fewer than 6 '
             'readings blank.', fontsize=9, color=INK2)
    fig.text(0.06, 0.015, spec['footer'], fontsize=7.8, color=MUTED)
    fig.tight_layout(rect=(0.03, 0.03, 1, 0.89))
    fig.savefig(os.path.join(OUT, f"{spec['stem']}_history_{city}.png"), dpi=150, facecolor=SURF)
    plt.close(fig)
    full_years = daily['mean'].groupby(daily.index.year).agg(['mean', 'count'])
    stats = {'first': f'{values.index.min():%Y-%m-%d}', 'last': f'{values.index.max():%Y-%m-%d}',
             'readings': len(values), 'mean_of_daily_means': daily['mean'].mean()}
    for mark in spec['marks']:
        ts = values.idxmax() if mark == 'max' else values.idxmin()
        stats[mark], stats[f'{mark}_at'] = values[ts], f'{ts:%Y-%m-%d %H:%M}'
    if spec['share_at_least']:
        stats[f"percent_at_least_{spec['share_at_least']}"] = 100 * (values >= spec['share_at_least']).mean()
    stats['full_years'] = ' '.join(str(y) for y in full_years.index[full_years['count'] >= 330])
    return stats


def chart_by_month(data, cities, variable):
    """Average of a variable by calendar month, one panel per city, ordered by the size of the seasonal swing.

    Bold line: mean of the daily means of every day of that calendar month over the whole record (days with fewer
    than 6 of 8 readings left out). Thin lines: each year's own monthly mean, for months with at least 20 such days.
    """
    spec = HISTORY_VARIABLES[variable]
    bm = spec['by_month']
    rows, panels, last = [], [], []
    for city in cities:
        values = measurements(data, city, variable) * spec['factor']
        last.append(values.index.max())
        for first, final in SUSPECT_PERIODS.get(variable, {}).get(city, []):
            values = values[(values.index < pd.Timestamp(first)) | (values.index > pd.Timestamp(final))]
        daily = values.resample('D').agg(['mean', 'size'])
        daily = daily[daily['size'] >= 6]['mean']
        climate = daily.groupby(daily.index.month).mean()
        per_year = daily.groupby([daily.index.year, daily.index.month]).agg(['mean', 'size'])
        per_year = per_year[per_year['size'] >= 20]
        rows += [(city, 'all', month, climate[month], int((daily.index.month == month).sum())) for month in climate.index]
        rows += [(city, year, month, r['mean'], int(r['size'])) for (year, month), r in per_year.iterrows()]
        panels.append((city, climate, per_year['mean'].unstack(0), climate.max() - climate.min()))
    pd.DataFrame(rows, columns=['city', 'year', 'month', bm['column'], 'days']) \
        .to_csv(os.path.join(OUT, f"{spec['stem']}_by_month.csv"), index=False, float_format='%.2f')
    panels.sort(key=lambda p: -p[3])
    ylim = bm['ylim'] or (0, 5 * np.ceil(max(max(p[1].max(), p[2].max().max()) for p in panels) / 5) + 5)

    plt.rcParams.update({'font.size': 10, 'axes.edgecolor': AXIS, 'xtick.color': MUTED, 'ytick.color': MUTED,
                         'axes.labelcolor': INK2, 'text.color': INK})
    fig, axes = plt.subplots(2, 5, figsize=(16, 7.4), sharex=True, sharey=True, facecolor=SURF)
    months = np.arange(1, 13)
    for ax, (city, climate, years, swing) in zip(axes.flat, panels):
        ax.set_facecolor(SURF)
        ax.grid(axis='y', color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for side in ['top', 'right']:
            ax.spines[side].set_visible(False)
        for year in years.columns:
            ax.plot(months, years[year].reindex(months), color=BLUE_RAMP[0], lw=1, alpha=0.8, zorder=2)
        ax.plot(months, climate.reindex(months), color=SINGLE, lw=2.4, marker='o', ms=5, mec=SURF, mew=1.2, zorder=3)
        for month, above in [(climate.idxmax(), True), (climate.idxmin(), False)]:
            ax.annotate(spec['fmt'].format(climate[month]), (month, climate[month]), xytext=(0, 7 if above else -7),
                        textcoords='offset points', ha='center', va='bottom' if above else 'top', fontsize=9,
                        fontweight='bold', color=INK, zorder=4)
        ax.set_title(CITIES.get(city, (city.title(), ''))[0], loc='left', fontsize=11.5, color=INK, pad=14)
        ax.text(0, 1.03, f"{bm['words'][0]}–{bm['words'][1]} month: {swing:.0f} {bm['gap_unit']}",
                transform=ax.transAxes, fontsize=8.5, color=INK2)
        ax.set_xticks(months)
        ax.set_xticklabels(list('JFMAMJJASOND'))
        ax.set_xlim(0.5, 12.5)
        ax.set_ylim(*ylim)
    for ax in axes[:, 0]:
        ax.set_ylabel(bm['ylabel'])
    fig.suptitle(f"Average {bm['title']} by month of the year", x=0.04, y=0.985, ha='left', fontsize=14,
                 fontweight='bold', color=INK)
    fig.text(0.04, 0.925, 'Bold line: average of the daily means of each calendar month over the whole record. Thin lines: '
             f"each year on its own (months with 20+ days of data). Cities ordered by the gap between "
             f"{bm['words'][0]} and {bm['words'][1]} month.", fontsize=9, color=INK2)
    left_out = {}                                    # cities grouped by the stretches left out for them
    for city in cities:
        periods = tuple(SUSPECT_PERIODS.get(variable, {}).get(city, []))
        if periods:
            left_out.setdefault(periods, []).append(CITIES[city][0])
    note = ''
    if left_out:
        stretches = '; '.join(f"{', '.join(names)}: " + ' and '.join(
            f'{pd.Timestamp(a):%d %b %Y} – {pd.Timestamp(b):%d %b %Y}' for a, b in periods)
            for periods, names in left_out.items())
        note = f'\nLeft out because wind speeds were far below normal (see README): {stretches}.'
    fig.text(0.04, 0.012, f'Source: roboclimate, OpenWeather current weather, up to {max(last):%d %b %Y}. '
             f'Southern-hemisphere cities (São Paulo, Sydney, Asunción) have their seasons the other way round.{note}',
             fontsize=8, color=MUTED, va='bottom' if note else 'baseline')
    fig.tight_layout(rect=(0.01, 0.05 if note else 0.03, 1, 0.915))
    fig.savefig(os.path.join(OUT, f"{spec['stem']}_by_month.png"), dpi=150, facecolor=SURF)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data', default=os.environ.get('ROBOCLIMATE_CSV_FILES_PATH', 'csv_files'),
                        help='folder with weather_*.csv and the <variable>/join_*.csv files (default: csv_files)')
    parser.add_argument('--cities', nargs='+', default=list(CITIES), help='cities for the per-city charts (default: original 10)')
    args = parser.parse_args()
    chart_mase_by_season(args.data)
    for city in args.cities:
        chart_wind_rose(args.data, city)
    shifts = {city: chart_pressure_clock(args.data, city) for city in args.cities}
    pd.DataFrame(shifts, index=['pressure_shift_h', 'temp_shift_h']).T.rename_axis('city') \
        .to_csv(os.path.join(OUT, 'pressure_clock_shifts.csv'), float_format='%.2f')
    temps = pd.concat(pd.read_csv(os.path.join(args.data, f'weather_{city}.csv')).temp for city in args.cities)
    ylims = {'temp': (5 * np.floor(temps.min() / 5) - 5, 5 * np.ceil(min(temps.max(), 45) / 5) + 5),   # shared by cities
             'humidity': (0, 105)}
    wind_max = max((measurements(args.data, city, 'wind_speed') * HISTORY_VARIABLES['wind_speed']['factor']).max()
                   for city in args.cities)
    ylims['wind_speed'] = (0, 10 * np.ceil(wind_max / 10) + 10)
    for variable, spec in HISTORY_VARIABLES.items():
        summary = {city: chart_history(args.data, city, variable, ylims[variable]) for city in args.cities}
        pd.DataFrame(summary).T.rename_axis('city') \
            .to_csv(os.path.join(OUT, f"{spec['stem']}_history_summary.csv"), float_format='%.2f')
    for variable, spec in HISTORY_VARIABLES.items():
        if spec['by_month']:
            chart_by_month(args.data, args.cities, variable)
    print(f'charts written to {OUT}')


if __name__ == '__main__':
    main()
