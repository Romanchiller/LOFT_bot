import holidays
import datetime

from sqlalchemy import select, desc

from models import Table, Booking

ru_holidays = holidays.RU()


def get_free_table(booking_date, time_close, room_list, session, guests_quantity = 1):

    """
    get free table number

    Args:
        table_capacity (int): table capacity
        booking_date (date): booking date
        session (Session): session

    Returns:
        int: free table number
        False: if all tables are busy
        """

    with session:
        query = select(Table.number).where(Table.capacity >= guests_quantity).filter(Table.room_name.in_(room_list)).order_by(Table.number)
        tables = session.execute(query).scalars().all()
        print(tables)
        query = select(Table.number).join(Booking).filter(Booking.date == booking_date, Table.number.in_(tables)).order_by(Table.number).distinct()
        busy_tables = session.execute(query).scalars().all()

        if room_list == ['vip_1', 'vip_2'] and tables == busy_tables or room_list == ['big_vip'] and tables == busy_tables:
            return False
        if room_list == ['small_hall', 'big_hall'] and tables == busy_tables:
            if time_close == '2:00':
                booking_time = '22:00'
            else:
                booking_time = '21:00'
            query = select(Table.number, Booking.time).join(Booking).filter(Booking.date == booking_date, Table.number.in_(tables), Booking.time >= booking_time).order_by(desc(Booking.time)).distinct()
            part_busy_table = session.execute(query).first()
            if part_busy_table is not None:
                return False, part_busy_table
            else:
                return False
        else:
            free_tables = sorted(list(set(tables) - set(busy_tables)))
            return free_tables[0]

def time_open_close(date : datetime.date) -> bool:
    res = date.weekday()
    if res == 4 or res == 5 or date in ru_holidays:
        start_time = datetime.time(17, 0)
        end_time = datetime.time(2, 0)
    else:
        start_time = datetime.time(17, 0)
        end_time = datetime.time(0, 0)
    return [start_time, end_time]




def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
