from datetime import datetime, date


def current_utc_date_generator():
    current_utc_dt = datetime.utcnow()
    return date(current_utc_dt.year, current_utc_dt.month, current_utc_dt.day)


def one_year_ago(date_time):
    return n_years_ago(date_time, 1)


def n_years_ago(date_time, n):
    try:
        return date_time.replace(year=date_time.year - n)
    except ValueError:
        return None


def remove_29_feb(df):
    df['dt_iso'] = df['dt'].apply(datetime.fromtimestamp)
    return df.drop(df[df['dt_iso'].apply(lambda x: (x.month, x.day)) == (2, 29)].index)


def csv_file_path(csv_folder, filename, city_name):
    return f"{csv_folder}/{filename}_{city_name}.csv"


def date_and_timestamp(start_datetime, end_datetime_not_included):
    """
    Args:
        start_datetime: datetime(2019,11,30,0,0,0)
        end_datetime: datetime(2019,11,30,9,0,0)

    Returns:
        list: returns [(1575072000, '2019-11-30'), (1575082800, '2019-11-30'), (1575093600, '2019-11-30')] that corresponds to
        ['2019-11-30 00:00:00', '2019-11-30 00:03:00', '2019-11-30 00:06:00']
    """
    step_3hours = 3600*3
    return [(x, date.fromtimestamp(x).isoformat()) for x in range(int(start_datetime.timestamp()), int(end_datetime_not_included.timestamp()), step_3hours)]
