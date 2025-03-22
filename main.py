import os
from models import Session, Booking, engine, Table
import telebot
from dotenv import load_dotenv
from telebot import types
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date, datetime, time, timedelta
from tools import time_open_close, time_in_range
from sqlrequests import get_free_table
from time import sleep

session = Session(bind=engine)

load_dotenv()

token = os.getenv('BOT_TOKEN')

bot = telebot.TeleBot(token)

START = '''
Здравствуйте! На данный момент бот находится в разработке и не функционирует.
/admin админка
'''

booking_data = {}




@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, START)
    keyboard = types.InlineKeyboardMarkup()
    key_booking = types.InlineKeyboardButton(text='Забронировать стол', callback_data='booking')
    keyboard.row(key_booking)
    key_booking_small_vip = types.InlineKeyboardButton(text='Малую VIPку (5к)', callback_data='booking_small_vip')
    # keyboard.add(key_booking_small_vip,)
    key_booking_big_vip = types.InlineKeyboardButton(text='Большую VIPку  (7к)', callback_data='booking_big_vip')
    # keyboard.add(key_booking_big_vip)
    keyboard.row(key_booking_small_vip, key_booking_big_vip)
    bot.send_message(message.chat.id, 'Выберите что хотите забронировать', reply_markup=keyboard)


@bot.message_handler(commands=['admin'])
def admin(message):
    bot.send_message(message.from_user.id, 'Админка')
    keyboard = types.InlineKeyboardMarkup()
    key_booking = types.InlineKeyboardButton(text='Посмотреть все бронирования', callback_data='see_all_booking')
    keyboard.add(key_booking)
    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    chat_id = call.message.chat.id
    if call.data == 'booking':
        booking_data['комнаты'] = ['small_hall', 'big_hall']
        bot.send_message(chat_id, 'Введите количество гостей. Не более 7');
        bot.register_next_step_handler(call.message, get_guests_quantity)
    if call.data == 'booking_small_vip':
        booking_data['комнаты'] = ['vip_1', 'vip_2']
        bot.send_message(chat_id, 'Введите количество гостей. Не более 7');
        bot.register_next_step_handler(call.message, get_guests_quantity)
    if call.data == 'booking_big_vip':
        booking_data['комнаты'] = ['big_vip']
        bot.send_message(chat_id, 'Введите количество гостей. Не более 9');
        bot.register_next_step_handler(call.message, get_guests_quantity)


def get_guests_quantity(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        try:
            guest_quantity = int(data)
            max_guests_quantity = 7
            if booking_data['комнаты'] == ['big_vip']:
                max_guests_quantity = 9
            if guest_quantity > max_guests_quantity or guest_quantity < 1:
                bot.send_message(message.from_user.id, f'Максимальное количество гостей за одним столом {max_guests_quantity}, минимальное 1. Попробуйте ещё раз. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, get_guests_quantity)
            else:
                booking_data['количество гостей'] = guest_quantity
                bot.send_message(message.from_user.id, 'Введите дату в формате ДД.ММ.ГГГГ? Для выхода в меню введите /start');
                bot.register_next_step_handler(message, get_date)
        except ValueError:
            bot.send_message(message.from_user.id, 'Неверные данные.\n Попробуйте ещё раз. Введите число.\n Для выхода в меню введите /start')
            bot.register_next_step_handler(message, get_guests_quantity)


def get_date(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        try:
            date_booking = datetime.strptime(data, '%d.%m.%Y').date()
            if date_booking < date.today():
                bot.send_message(message.from_user.id, 'Неверная дата. Попробуйте ещё раз. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, get_date)
            else:
                time_for_booking = time_open_close(date_booking)
                print(time_for_booking[1], type(time_for_booking[1]))
                booking_data['время открытия'] = time_for_booking[0]
                booking_data['время закрытия'] = time_for_booking[1]
                if booking_data['комнаты'] == ['vip_1', 'vip_2'] or booking_data['комнаты'] == ['big_vip']:
                    booking_data['время закрытия'] = time_for_booking[1] - timedelta(hours=3)
                booking_data['строка с датой'] = data

                free_table = get_free_table(booking_date= date_booking.strftime("%m.%d.%Y"),
                                            time_close=booking_data['время закрытия'],
                                            room_list=booking_data['комнаты'],
                                            session=session,
                                            guests_quantity=booking_data['количество гостей'])
                print(free_table)

                booking_data['комментарий'] = ''
                booking_data['дата бронирования'] = date_booking
                if isinstance(free_table, tuple):
                    booking_data['частично забронированный'] = free_table[1][0]
                    print(booking_data['частично забронированный'])
                    booking_data['ограничение по времени'] = free_table[1][1]
                    print(booking_data['ограничение по времени'])
                    booking_data['комментарий'] += f'ограничение по времени {free_table[1][1].strftime("%H.%M")}'
                    bot.send_message(message.from_user.id, f'К сожалению на эту дату свободных столов нет. Но есть столы, забронированные на {booking_data["ограничение по времени"].strftime("%H.%M")}.При таком бронировании вам необходимо будет освободить стол до указанного времени. Хотите забронировать стол? Для подтверждения введите "Да". Для отмены введите "Нет". Для выхода в меню введите /start')
                    bot.register_next_step_handler(message, get_answer)
                if not free_table:
                    bot.send_message(message.from_user.id, f'К сожалению на эту дату свободных столов нет. Вы можете связаться с нами по телефону +7 (950) 529-22-09. Для выхода в меню введите /start')
                if isinstance(free_table, int) and free_table > 0:
                    booking_data['номер стола'] = free_table
                    bot.send_message(message.from_user.id, f'Введите время в формате ЧЧ:ММ, на эту дату возможно бронирование с {time_for_booking[0].strftime("%H:%M")} до {booking_data["время закрытия"].strftime("%H:%M")}. Для выхода в меню введите /start');
                    bot.register_next_step_handler(message, get_time)
        except ValueError:
            bot.send_message(message.from_user.id, 'Неверный формат даты.\n Попробуйте ещё раз.\n  Образец: 12.12.2024.Для выхода в меню введите /start')
            bot.register_next_step_handler(message, get_date)


def get_answer(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        if data == 'Да' or data == 'да':
            booking_data['номер стола'] = booking_data['частично забронированный']
            bot.send_message(message.from_user.id, 'Введите время в формате ЧЧ:ММ');
            bot.register_next_step_handler(message, get_time)
        else:
            start(message)


def get_time(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        try:
            time_booking = datetime.strptime(data, '%H:%M').time()
            time_constraint = booking_data.get('ограничение по времени')
            if booking_data['комнаты'] == ['vip_1', 'vip_2'] or booking_data == ['big_vip']:
                time_constraint = datetime.time(22, 0)
            if time_constraint is not None:
                print(time_constraint, type(time_constraint))
                print(booking_data['время открытия'], type(booking_data['время открытия']))
                print(booking_data['время закрытия'], type(booking_data['время закрытия']))
                booking_data['время закрытия'] = time_constraint

                print(time_in_range(booking_data['время открытия'], booking_data['время закрытия'], time_booking))

            if not time_in_range(booking_data['время открытия'], booking_data['время закрытия'], time_booking):
                bot.send_message(message.from_user.id, f'На эту дату возможно бронирование с {booking_data["время открытия"].strftime("%H:%M")} до {booking_data["время закрытия"].strftime("%H:%M")}.Попробуйте ещё раз. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, get_time)
            else:
                booking_data['строка с временем'] = data
                booking_data['время бронирования'] = str(time_booking)
                print(booking_data['время бронирования'])
                bot.send_message(message.from_user.id, 'Введите номер телефона?');
                bot.register_next_step_handler(message, get_phone)
        except ValueError:
            bot.send_message(message.from_user.id, 'Неверный формат времени.\n Попробуйте еще раз.\n Для выхода в меню введите /start\n  Образец: 20:00')
            bot.register_next_step_handler(message, get_time)

def get_phone(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        try:
            phone = int(data)
            booking_data['телефон'] = phone
            bot.send_message(message.from_user.id, 'Введите имя?');
            bot.register_next_step_handler(message, get_name)
        except ValueError:
            bot.send_message(message.from_user.id, 'Неверный формат телефона.\n Попробуйте ещё раз.\n Введите число. Образец: 81234567890\nДля выхода в меню введите /start')
            bot.register_next_step_handler(message, get_phone)

def get_name(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        booking_data['имя'] = data
        bot.send_message(message.from_user.id, 'Введите комментарий. Можно поставить любой знак')
        bot.register_next_step_handler(message, get_comments)


def get_comments(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        booking_data['комментарий'] += data
        info = {
            'дата бронирования': booking_data['строка с датой'],
            'время бронирования': booking_data['строка с временем'],
            'имя': booking_data['имя'],
            'телефон': booking_data['телефон'],
            'комментарий': booking_data['комментарий'],}

        print(info)
        bot.send_message(message.from_user.id, f'Ваше бронирование принято! Данные бронирования: \n {info}.\n Мы свяжемся с вами для подтверждения брони по указанному номеру либо в telegram. Неподтвержденная бронь будет снята за час до начала. Подтвержденная бронь будет снята, если вы не пришли в течение 15 минут на момент начала бронирования . Для отмены бронирования свяжитесь с нами по телефону  +7 (950) 529-22-09 в часы работы')
        with session:
            booking = Booking(date=booking_data['дата бронирования'],
                              time=booking_data['время бронирования'],
                              user_name=booking_data['имя'],
                              phone=booking_data['телефон'],
                              table_number=booking_data['номер стола'],
                              comments=booking_data['комментарий'])

            session.add(booking)
            session.commit()
        start(message)


while True:
    try:
        bot.polling(none_stop=True)
    except Exception as _ex:
        print(_ex)
        sleep(1)
