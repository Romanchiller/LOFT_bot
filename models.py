import datetime
import os
from sqlalchemy import create_engine, DateTime, Column, Boolean, String, func, Date, ForeignKey, Time, Integer, BigInteger
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from dotenv import load_dotenv

load_dotenv()


POSTGRES_PASSWORD = os.getenv('DB_PASSWORD', '111')
POSTGRES_USER = os.getenv('DB_USER', '111')
POSTGRES_DB = os.getenv('DB_NAME', 'telegram_bot')
POSTGRES_HOST = os.getenv('DB_HOST', '127.0.0.1')
POSTGRES_PORT = os.getenv('DB_PORT', '5432')


PG_DSN = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

engine = create_engine(PG_DSN)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass



class Booking(Base):
    __tablename__ = 'booking'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    time: Mapped[datetime.time] = mapped_column(Time, nullable=False, )
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[int] = mapped_column(BigInteger, nullable=False)
    table_number: Mapped[int] = mapped_column(Integer, ForeignKey('table.number'), nullable=False)
    comments: Mapped[str] = mapped_column(String(500), nullable=True)
    date_of_create: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    guests_quantity: Mapped[int] = mapped_column(Integer, nullable=True, default=1)

    table = relationship('Table', back_populates='bookings')

    @property
    def dict(self):
        return {
            'id': self.id,
            'количество гостей': self.guests_quantity,
            'дата создания': self.date_of_create,
            'дата бронирования': self.date,
            'время бронирования': self.time,
            'имя': self.user_name,
            'телефон': self.phone,
            'номер стола': self.table_number,
            'комментарии': self.comments,
            'статус': self.is_active
        }

class Table(Base):
    __tablename__ = 'table'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[int] = mapped_column(Integer,unique=True, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    room_name: Mapped[int] = Column(ForeignKey('room.name', ondelete='CASCADE'), nullable=False,)

    bookings = relationship('Booking', back_populates='table')
    room = relationship('Room', back_populates='tables')

    @property
    def dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'capacity': self.capacity,
            'bookings': self.bookings,
            'room': self.room
        }


class Room(Base):
    __tablename__ = 'room'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100),unique=True, nullable=False)

    tables = relationship('Table', back_populates='room')

    @property
    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'tables': self.tables
        }


# Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
