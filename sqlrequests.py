import datetime

from sqlalchemy import select, or_, desc

from sqlalchemy.orm import Session
from models import Table, Booking, engine

session = Session(bind=engine)

# booking = Booking(table_number=18, date='2025-02-24', time='22:00', user_name='test', phone=1234567890, comments='test')
#
# with (Session(bind=engine) as session):
#     session.add(booking)
#     session.commit()

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
        print("столы по вместимости")
        print(tables)
        query = select(Table.number).join(Booking).filter(Booking.date == booking_date, Table.number.in_(tables)).order_by(Table.number).distinct()
        busy_tables = session.execute(query).scalars().all()
        print("занятые столы")
        print(busy_tables)
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
            print(free_tables)
            print(free_tables[0])
            return free_tables[0]


# get_free_table(booking_date='02.24.2025',time_close='2:00' , room_list=['small_hall', 'big_hall'],session=session, guests_quantity=2)

