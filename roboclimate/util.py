from datetime import datetime


def one_year_ago(date_time):
    try:
        return date_time.replace(year=date_time.year-1)
    except ValueError:
        return None


def remove_29_feb(df):
    df['dt_iso'] = df['dt'].apply(datetime.fromtimestamp)
    return df.drop(df[df['dt_iso'].apply(lambda x: (x.month, x.day)) == (2, 29)].index)
