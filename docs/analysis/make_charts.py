"""Rebuild the charts in docs/analysis from the roboclimate CSV files.

Produces, next to this script:
- london_temp_mase_by_season.png / .csv : MASE of London's 1- and 5-day temperature forecasts by season and year
- wind_rose_<city>.png / .csv           : direction a city's wind blows from (8 sectors), by Beaufort band and season,
                                          for each of the original 10 cities

Needs weather_<city>.csv and temp/join_london.csv (written by the Java or Python data analysis) in the data folder.

USAGE (from the repo root):
    bin/python docs/analysis/make_charts.py [--data csv_files] [--cities london madrid ...]
"""
import argparse
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use('Agg')
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


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data', default=os.environ.get('ROBOCLIMATE_CSV_FILES_PATH', 'csv_files'),
                        help='folder with weather_*.csv and the <variable>/join_*.csv files (default: csv_files)')
    parser.add_argument('--cities', nargs='+', default=list(CITIES), help='cities for the wind roses (default: original 10)')
    args = parser.parse_args()
    chart_mase_by_season(args.data)
    for city in args.cities:
        chart_wind_rose(args.data, city)
    print(f'charts written to {OUT}')


if __name__ == '__main__':
    main()
