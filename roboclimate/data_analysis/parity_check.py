"""Check that the Java data analysis produces the same results as the reference Python one (data_analysis.py).

Both analyses run on identical copies of the input CSVs; every join file must contain the same rows with the
same values and every metrics file the same metrics (relative tolerance 1e-9; NaN on both sides counts as equal).

By default the input is a small generated dataset for 'london' that exercises the tricky cases: a gap in the
3-hourly series (MASE must not pair readings across it), blank wind_deg values in measurements and forecasts
(only wind_deg may lose those rows), and measurements with fewer than 5 forecasts (no join row).

USAGE (from the repo root; the Java module needs JDK 22 for its string templates):
    JAVA_HOME=<jdk22> bin/python roboclimate/data_analysis/parity_check.py            # generated fixture
    JAVA_HOME=<jdk22> bin/python roboclimate/data_analysis/parity_check.py --data DIR  # real weather_*/forecast_* CSVs (~6 s for csv_files)
Exit status 0 when the outputs match, 1 otherwise.
"""
import argparse
import datetime as dt
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JAVA_SRC = os.path.join(REPO, 'roboclimate', 'data_analysis', 'src', 'roboclimate')
WEATHER_VARIABLES = ['temp', 'pressure', 'humidity', 'wind_speed', 'wind_deg']
CSV_HEADER = 'temp,pressure,humidity,wind_speed,wind_deg,dt,today'
REL_TOL = 1e-9
THREE_HOURS = 3 * 3600


def generate_fixture(folder):
    """Two weeks of 3-hourly 'london' data with a gap, blank wind_deg values and incomplete forecasts."""
    rnd = random.Random(42)
    start = int(dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    slots = [start + i * THREE_HOURS for i in range(14 * 8)]
    gap = set(slots[8 * 9:8 * 10]) | {slots[8 * 11 + 3]}           # a missing day and a missing single slot
    blank_wind_measurement = {slots[8 * 6 + 2], slots[8 * 12 + 5]}
    blank_wind_forecast = {(slots[8 * 7 + 4], 2), (slots[8 * 13 + 1], 4)}  # (target dt, horizon in days)
    incomplete_forecasts = {slots[8 * 8 + 6]: 3}                     # target dt -> horizon whose forecast is missing

    def day(ts):
        return dt.datetime.fromtimestamp(ts, dt.timezone.utc).date().isoformat()

    def values(ts, noise):
        hour = (ts - start) / 3600
        return [round(10 + 5 * math.sin(hour / 24 * 2 * math.pi) + rnd.gauss(0, noise), 2),
                round(1010 + rnd.gauss(0, 3 * noise), 2),
                round(70 + rnd.gauss(0, 5 * noise), 2),
                round(abs(4 + rnd.gauss(0, noise)), 2),
                round(rnd.uniform(0, 359))]

    weather, forecast = [CSV_HEADER], [CSV_HEADER]
    for ts in slots:
        if ts not in gap:
            v = values(ts, 1.0)
            if ts in blank_wind_measurement:
                v[4] = ''
            weather.append(','.join(map(str, v + [ts, day(ts)])))
        for horizon in range(1, 6):                                  # forecasts made 1..5 days before the target
            made = ts - horizon * 86400
            if made < start or incomplete_forecasts.get(ts) == horizon:
                continue
            v = values(ts, 0.5 * horizon)
            if (ts, horizon) in blank_wind_forecast:
                v[4] = ''
            forecast.append(','.join(map(str, v + [ts, day(made)])))
    for name, rows in [('weather_london.csv', weather), ('forecast_london.csv', forecast)]:
        with open(os.path.join(folder, name), 'w', encoding='utf-8') as f:
            f.write('\n'.join(rows) + '\n')
    return ['london']


def run_java(folder):
    java_home = os.environ.get('JAVA_HOME')
    javac = os.path.join(java_home, 'bin', 'javac') if java_home else 'javac'
    java = os.path.join(java_home, 'bin', 'java') if java_home else 'java'
    classes = tempfile.mkdtemp(prefix='parity_classes_')
    sources = [os.path.join(JAVA_SRC, f) for f in sorted(os.listdir(JAVA_SRC)) if f.endswith('.java')]
    subprocess.run([javac, '-source', '22', '--enable-preview', '-d', classes, *sources],
                   check=True, capture_output=True, text=True)
    out = subprocess.run([java, '--enable-preview', '-cp', classes, 'roboclimate.Main'], check=True,
                         capture_output=True, text=True, env=dict(os.environ, ROBOCLIMATE_CSV_FILES_PATH=folder))
    shutil.rmtree(classes)
    return out.stdout


def run_python(folder, cities):
    code = ("import logging, sys\n"
            "logging.basicConfig(level='WARNING')\n"
            "import roboclimate.data_analysis as d\n"
            "for c in sys.argv[1:]:\n"
            "    d.analyse_city_data(c)\n")
    env = dict(os.environ, ROBOCLIMATE_CSV_FILES_PATH=folder, PYTHONPATH=REPO)
    subprocess.run([sys.executable, '-c', code, *cities], check=True, env=env, cwd=folder, capture_output=True)


def close(a, b):
    if np.isnan(a) and np.isnan(b):
        return True
    return math.isclose(a, b, rel_tol=REL_TOL, abs_tol=1e-12)


def compare(java_dir, python_dir, cities):
    problems, compared = [], 0
    for var in WEATHER_VARIABLES:
        for city in cities:
            jfile, pfile = (os.path.join(d, var, f'join_{city}.csv') for d in (java_dir, python_dir))
            if not (os.path.exists(jfile) and os.path.exists(pfile)):
                problems.append(f'{var}/{city}: join file missing (java={os.path.exists(jfile)}, python={os.path.exists(pfile)})')
                continue
            j = pd.read_csv(jfile).assign(dt=lambda df: df.dt.astype('int64')).set_index('dt')
            p = pd.read_csv(pfile).assign(dt=lambda df: df.dt.astype('int64')).set_index('dt')
            only_j, only_p = sorted(set(j.index) - set(p.index)), sorted(set(p.index) - set(j.index))
            if only_j or only_p:
                problems.append(f'{var}/{city}: join rows differ — only in Java: {len(only_j)}, only in Python: {len(only_p)}')
            common = sorted(set(j.index) & set(p.index))
            cols = [var, 't5', 't4', 't3', 't2', 't1']
            diff = np.abs(j.loc[common, cols].to_numpy(float) - p.loc[common, cols].to_numpy(float))
            if common and np.nanmax(diff) > 1e-9:
                problems.append(f'{var}/{city}: join values differ (max {np.nanmax(diff):.3g})')

            jm, pm = (os.path.join(d, var, f'metrics_{city}.csv') for d in (java_dir, python_dir))
            if os.path.exists(jm) != os.path.exists(pm):
                problems.append(f'{var}/{city}: metrics file only on one side (java={os.path.exists(jm)})')
                continue
            if not os.path.exists(jm):
                continue
            jdf, pdf = pd.read_csv(jm), pd.read_csv(pm)
            for metric in ['mae', 'rmse', 'medae', 'mase']:
                for i, horizon in enumerate(['t5', 't4', 't3', 't2', 't1']):
                    compared += 1
                    a, b = float(jdf[metric][i]), float(pdf[metric][i])
                    if not close(a, b):
                        problems.append(f'{var}/{city}: {metric} {horizon} java={a!r} python={b!r}')
    return problems, compared


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data', help='folder with real weather_<city>.csv / forecast_<city>.csv files')
    args = parser.parse_args()

    work = tempfile.mkdtemp(prefix='parity_')
    java_dir, python_dir = os.path.join(work, 'java'), os.path.join(work, 'python')
    for d in (java_dir, python_dir):
        os.makedirs(d)
    if args.data:
        files = [f for f in os.listdir(args.data) if f.startswith(('weather_', 'forecast_')) and f.endswith('.csv')]
        cities = sorted({f.split('_', 1)[1][:-4] for f in files if f.startswith('weather_')})
        for f in files:
            shutil.copy(os.path.join(args.data, f), java_dir)
    else:
        cities = generate_fixture(java_dir)
    for f in os.listdir(java_dir):
        shutil.copy(os.path.join(java_dir, f), python_dir)
    for d in (java_dir, python_dir):
        for var in WEATHER_VARIABLES:
            os.makedirs(os.path.join(d, var))

    run_java(java_dir)
    run_python(python_dir, cities)
    problems, compared = compare(java_dir, python_dir, cities)
    print(f'compared {len(cities)} cities x {len(WEATHER_VARIABLES)} variables, {compared} metric values (work dir: {work})')
    for p in problems:
        print(f'MISMATCH {p}')
    print('PASS: Java matches Python' if not problems else f'FAIL: {len(problems)} mismatches')
    if not problems:
        shutil.rmtree(work)
    sys.exit(0 if not problems else 1)


if __name__ == '__main__':
    main()
