import datetime
import pytz


def current_datetime(timezone=pytz.utc):
    dt_utc = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    return dt_utc.astimezone(timezone)


def current_date(timezone=pytz.utc):
    return current_datetime(timezone).date()


def current_time(timezone=pytz.utc):
    return current_datetime(timezone).time()


def convert_datetime(dt, source=pytz.utc, target=pytz.utc):
    if dt.tzinfo is not None:
        source = dt.tzinfo
    return dt.replace(tzinfo=source).astimezone(target)

def get_date_range(start_date, end_date, step=datetime.timedelta(1), inclusive=False):
    out = []

    if step.seconds > 0 or step.microseconds > 0:
        if type(start_date) == datetime.date:
            start_date = datetime.datetime.combine(start_date, datetime.time())
        if type(end_date) == datetime.date:
            end_date = datetime.datetime.combine(end_date, datetime.time())

    date = start_date
    while date < end_date:
        out.append(date)
        date += step
    if inclusive and date == end_date:
        out.append(date)
    return out
