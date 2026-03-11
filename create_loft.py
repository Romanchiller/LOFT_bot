
from models import Room, Table
from models import Session

room_1 = Room(name='big_hall', )
room_2 = Room(name='small_hall')
room_3 = Room(name='vip_1')
room_4 = Room(name='vip_2')
room_5 = Room(name='big_vip')


table_1 = Table(number=1, capacity=2, room_name=room_1.name)
table_2 = Table(number=2, capacity=2, room_name=room_1.name)
table_3 = Table(number=3, capacity=2, room_name=room_1.name)
table_4 = Table(number=4, capacity=4, room_name=room_1.name)
table_5 = Table(number=5, capacity=4, room_name=room_1.name)
table_6 = Table(number=6, capacity=7, room_name=room_3.name)
table_7 = Table(number=7, capacity=7, room_name=room_4.name)
table_8 = Table(number=8, capacity=7, room_name=room_1.name)
table_9 = Table(number=9, capacity=7, room_name=room_1.name)
table_10 = Table(number=10, capacity=4, room_name=room_1.name)
table_11 = Table(number=11, capacity=4, room_name=room_1.name)
table_12 = Table(number=12, capacity=9, room_name=room_5.name)
table_13 = Table(number=13, capacity=3, room_name=room_2.name)
table_14 = Table(number=14, capacity=3, room_name=room_2.name)
table_15 = Table(number=15, capacity=3, room_name=room_2.name)
table_16 = Table(number=16, capacity=4, room_name=room_2.name)
table_17 = Table(number=17, capacity=6, room_name=room_2.name)
table_18 = Table(number=18, capacity=6, room_name=room_2.name)


rooms = [room_1, room_2, room_3, room_4, room_5]
tables = [table_1, table_2, table_3, table_4, table_5, table_6, table_7, table_8, table_9, table_10, table_11, table_12, table_13, table_14, table_15, table_16, table_17, table_18]

session = Session()
def create_loft(session, rooms, tables):
    with session:
        session.add_all(rooms)

        session.add_all(tables)
        session.commit()
    return


create_loft(session, rooms, tables)
