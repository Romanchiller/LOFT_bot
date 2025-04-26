import datetime

from sqlalchemy import select, or_, desc

from sqlalchemy.orm import Session
from models import Table, Booking, engine

session = Session(bind=engine)

# booking = Booking(table_number=18, date='2025-02-24', time='22:00', user_name='test', phone=1234567890, comments='test')
#
# with (Session(bind=engine) as session):
    # query = select(Booking).filter(Booking.date == '2025-04-19')
    # bookings = session.execute(query).scalars().all()
    # for booking in bookings:
    #     print(booking.table_number)
#     session.add(booking)

