import holidays
import datetime


ru_holidays = holidays.RU()


def time_open_close(date : datetime.date) -> bool:
    res = date.weekday()
    if res == 4 or res == 5 or date in ru_holidays:
        start_time = datetime.time(17, 0)
        end_time = datetime.time(2, 0)
    else:
        start_time = datetime.time(17, 0)
        end_time = datetime.time(0, 0)
    return [start_time, end_time]


# time_open_close(datetime.date(2025, 6, 13))

def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end


# x = time_open_close(datetime.datetime.now())
# print(x)
#
# y = datetime.datetime(year=2025, month=6, day=13, hour=x[1].hour, minute=x[1].minute) - datetime.timedelta(hours=3)
#
# print(y.time())
