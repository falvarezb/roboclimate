from datetime import datetime, date

def current_utc_date_generator():
    current_utc_dt = datetime.utcnow()
    return date(current_utc_dt.year, current_utc_dt.month, current_utc_dt.day)

def one_year_ago(date_time):
    return n_years_ago(date_time, 1)

def n_years_ago(date_time, n):
    try:
        return date_time.replace(year=date_time.year-n)
    except ValueError:
        return None


def remove_29_feb(df):
    df['dt_iso'] = df['dt'].apply(datetime.fromtimestamp)
    return df.drop(df[df['dt_iso'].apply(lambda x: (x.month, x.day)) == (2, 29)].index)
