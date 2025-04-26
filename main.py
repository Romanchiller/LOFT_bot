import os

from sqlalchemy import select, update, delete

from models import Booking, engine
import telebot
from dotenv import load_dotenv
from telebot import types
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from tools import time_open_close, time_in_range, get_free_table

from time import sleep

session = Session(bind=engine)

load_dotenv()

token = os.getenv('BOT_TOKEN')

bot = telebot.TeleBot(token)

START = '''
Здравствуйте! Я бот, который поможет вам забронировать стол. Напоминаем, что при бронировании большой и малой VIP комнат, минимальный счет будет составлять 7000 рублей и 5000 рублей соответсвенно.
'''

booking_data = {}


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, START)
    keyboard = types.InlineKeyboardMarkup()
    key_booking = types.InlineKeyboardButton(text='Забронировать стол', callback_data='booking')
    keyboard.row(key_booking)
    key_booking_small_vip = types.InlineKeyboardButton(text='Малую VIPку (5к)', callback_data='booking_small_vip')
    key_booking_big_vip = types.InlineKeyboardButton(text='Большую VIPку  (7к)', callback_data='booking_big_vip')
    keyboard.row(key_booking_small_vip, key_booking_big_vip)
    bot.send_message(message.chat.id, 'Выберите что хотите забронировать', reply_markup=keyboard)


@bot.message_handler(commands=['ad'])
def admin(message):
    bot.send_message(message.from_user.id, 'Админка')
    keyboard = types.InlineKeyboardMarkup()
    key_see_all_false_status_booking = types.InlineKeyboardButton(text='Посмотреть все  неподтвержденные бронирования',
                                                                  callback_data='see_all_false_status_booking')
    keyboard.add(key_see_all_false_status_booking)
    key_change_status_booking = types.InlineKeyboardButton(text='Изменить статус бронирования',
                                                           callback_data='change_status_booking')
    keyboard.add(key_change_status_booking)
    key_delete_booking = types.InlineKeyboardButton(text='Удалить бронирование', callback_data='delete_booking')
    keyboard.add(key_delete_booking)
    key_see_booking_on_date = types.InlineKeyboardButton(text='Посмотреть бронирования на дату',
                                                         callback_data='see_booking_on_date')
    keyboard.add(key_see_booking_on_date)
    key_change_booking = types.InlineKeyboardButton(text='Изменить бронирование', callback_data='change_booking')
    keyboard.add(key_change_booking)
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
    if call.data == 'see_all_false_status_booking':
        query = select(Booking).filter(Booking.is_active == False)
        result = session.execute(query).scalars().all()
        for booking in result:
            str_from_dict = ''.join('{}: {}, '.format(key, val) for key, val in booking.dict.items())
            bot.send_message(chat_id, str_from_dict)
    if call.data == 'change_status_booking':
        bot.send_message(chat_id, 'Введите id бронирования')
        bot.register_next_step_handler(call.message, change_status_booking)
    if call.data == 'delete_booking':
        bot.send_message(chat_id, 'Введите id бронирования')
        bot.register_next_step_handler(call.message, delete_booking)
    if call.data == 'see_booking_on_date':
        bot.send_message(chat_id, 'Введите дату в формате ДД.ММ.ГГГГ')
        bot.register_next_step_handler(call.message, see_booking_on_date)
    if call.data == 'change_booking':
        bot.send_message(chat_id, 'Введите id бронирования')
        bot.register_next_step_handler(call.message, change_booking)


def change_booking(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        try:
            id_booking = int(data)
            result = get_booking_by_id(message, id_booking)
            if result is not None:
                bot.send_message(message.from_user.id, 'Введите номер параметра, который хотите изменить: \n1 - количество гостей\n 2 - дата бронирования\n 3 - время бронирования\n 4 - имя\n 5 - телефон\n 6 - комментарий\n 7 - стол')
                bot.register_next_step_handler(message, get_change_parameter, result)
            else:
                bot.send_message(message.from_user.id, 'Бронирования с таким id не было найдено. Попробуте еще раз Для выхода в меню введите /start')
                bot.register_next_step_handler(message, change_booking)
        except ValueError:
            bot.send_message(message.from_user.id, 'Неверное значение. Введите число. Для выхода в меню введите /start')
            bot.register_next_step_handler(message, change_booking)


def get_change_parameter(message, booking):
    data = message.text
    if data == '/start':
        start(message)
    else:
        try:
            parameter = int(data)

            bot.send_message(message.from_user.id, 'Введите значение.')
            bot.register_next_step_handler(message, change_item, booking, parameter)
        except ValueError:
            bot.send_message(message.from_user.id, 'Неверное значение. Введите число. Для выхода в меню введите /start')
            bot.register_next_step_handler(message, get_change_parameter, booking)




def change_item(message, booking, parameter):
    data = message.text
    if data == '/start':
        start(message)
    else:
        change_dict = {}
        if parameter == 1:
            try:
                print(data)
                guests_quantity = int(data)
                change_dict = {'guests_quantity': guests_quantity}

            except ValueError:
                bot.send_message(message.from_user.id, 'Неверное значение. Введите число. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, change_item, booking, parameter)
        if parameter == 2:
            try:
                date_booking = datetime.strptime(data, '%d.%m.%Y').date()
                change_dict = {'date': date_booking}
            except ValueError:
                bot.send_message(message.from_user.id, 'Неверное значение. Введите дату в формате ДД.ММ.ГГГГ. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, change_item, booking, parameter)
        if parameter == 3:
            try:
                time_booking = datetime.strptime(data, '%H:%M').time()
                change_dict = {'time': time_booking}
            except ValueError:
                bot.send_message(message.from_user.id, 'Неверное значение. Введите время в формате ЧЧ:ММ. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, change_item, booking,parameter)
        if parameter == 4:
            change_dict = {'user_name': data}
        if parameter == 5:
            try:
                phone = int(data)
                change_dict = {'phone': phone}
            except ValueError:
                bot.send_message(message.from_user.id, 'Неверное значение. Введите число. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, change_item, booking, parameter)
        if parameter == 6:
            change_dict = {'comments': data}
        if parameter == 7:
            try:
                table = int(data)
                change_dict = {'table_number': table}
            except ValueError:
                bot.send_message(message.from_user.id, 'Неверное значение. Введите число. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, change_item, booking, parameter)
        if change_dict:
            with session:
                update_booking = update(Booking).where(Booking.id == booking.id).values(**change_dict)
                session.execute(update_booking)
                session.commit()
                bot.send_message(message.from_user.id, f'Параметр бронирования {change_dict.keys()} изменен на {change_dict.values()}')


def see_booking_on_date(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        try:
            date = datetime.strptime(data, '%d.%m.%Y').date()
            query = select(Booking).filter(Booking.date == date)
            result = session.execute(query).scalars().all()
            for booking in result:
                str_from_dict = ''.join('{}: {}, '.format(key, val) for key, val in booking.dict.items())
                bot.send_message(message.from_user.id, str_from_dict)
        except ValueError:
            bot.send_message(message.from_user.id, 'Введите дату в формате ДД.ММ.ГГГГ')


def get_booking_by_id(message, id_booking):
    with session:
        query = select(Booking).filter(Booking.id == id_booking)
        result = session.execute(query).scalar()
        if result is None:
            bot.send_message(message.from_user.id,
                             'Брони с таким id не существует. Попробуйте ещё раз. Для выхода в меню введите /start')
            bot.register_next_step_handler(message, get_booking_by_id)
    return result


def change_status_booking(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        try:
            id_booking = int(data)
            result = get_booking_by_id(message, id_booking)
            if result.is_active:
                update_booking = update(Booking).where(Booking.id == id_booking).values(is_active=False)
                session.execute(update_booking)
                session.commit()
                bot.send_message(message.from_user.id, f'Cтатус брони  с id {id_booking} изменен на НЕПОДТВЕРЖДЕННАЯ')
            else:
                update_booking = update(Booking).where(Booking.id == id_booking).values(is_active=True)
                session.execute(update_booking)
                session.commit()
                bot.send_message(message.from_user.id, f'Cтатус брони  с id {id_booking} изменен на ПОДТВЕРЖДЕННАЯ')

        except ValueError:
            bot.send_message(message.from_user.id, 'Неверное значение. Введите число. Для выхода в меню введите /start')
            bot.register_next_step_handler(message, get_booking_by_id)


def delete_booking(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        try:
            id_booking = int(data)
            result = get_booking_by_id(message, id_booking)
            del_booking = delete(Booking).where(Booking.id == result.id)
            session.execute(del_booking)
            session.commit()
            bot.send_message(message.from_user.id, f'Бронирование с id {id_booking} удалено')
        except ValueError:
            bot.send_message(message.from_user.id, 'Неверное значение. Введите число. Для выхода в меню введите /start')
            bot.register_next_step_handler(message, delete_booking)


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
                bot.send_message(message.from_user.id,
                                 f'Максимальное количество гостей за одним столом {max_guests_quantity}, минимальное 1. Попробуйте ещё раз. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, get_guests_quantity)
            else:
                booking_data['количество гостей'] = guest_quantity
                bot.send_message(message.from_user.id,
                                 'Введите дату в формате ДД.ММ.ГГГГ? Для выхода в меню введите /start');
                bot.register_next_step_handler(message, get_date)
        except ValueError:
            bot.send_message(message.from_user.id,
                             'Неверные данные.\n Попробуйте ещё раз. Введите число.\n Для выхода в меню введите /start')
            bot.register_next_step_handler(message, get_guests_quantity)


def get_date(message):
    data = message.text
    if data == '/start':
        start(message)
    else:
        try:
            date_booking = datetime.strptime(data, '%d.%m.%Y').date()
            if date_booking < date.today():
                bot.send_message(message.from_user.id,
                                 'Неверная дата. Попробуйте ещё раз. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, get_date)
            else:
                time_for_booking = time_open_close(date_booking)
                booking_data['время открытия'] = time_for_booking[0]
                booking_data['время закрытия'] = time_for_booking[1]

                free_table = get_free_table(booking_date=date_booking.strftime("%m.%d.%Y"),
                                            time_close=booking_data['время закрытия'],
                                            room_list=booking_data['комнаты'],
                                            session=session,
                                            guests_quantity=booking_data['количество гостей'])
                print(free_table)
                booking_data['комментарий'] = ''
                booking_data['дата бронирования'] = date_booking
                booking_data['строка с датой'] = date_booking.strftime("%d.%m.%Y")
                if booking_data['комнаты'] == ['vip_1', 'vip_2'] or booking_data == ['big_vip']:
                    result = datetime(year=booking_data['дата бронирования'].year,
                                      month=booking_data['дата бронирования'].month,
                                      day=booking_data['дата бронирования'].day,
                                      hour=booking_data['время закрытия'].hour,
                                      minute=booking_data['время закрытия'].minute) - timedelta(hours=2)
                    time_constraint = result.time()
                    booking_data['время закрытия'] = time_constraint
                if isinstance(free_table, tuple) and booking_data['комнаты'] == ['small_hall', 'big_hall']:
                    booking_data['частично забронированный'] = free_table[1][0]
                    booking_data['время закрытия'] = free_table[1][1]
                    booking_data['комментарий'] += f'ограничение по времени {free_table[1][1].strftime("%H.%M")}'
                    bot.send_message(message.from_user.id,
                                     f'К сожалению на эту дату свободных столов нет. Но есть столы, забронированные на {booking_data["ограничение по времени"].strftime("%H.%M")}.При таком бронировании вам необходимо будет освободить стол до указанного времени. Хотите забронировать стол? Для подтверждения введите "Да". Для отмены введите "Нет". Для выхода в меню введите /start')
                    bot.register_next_step_handler(message, get_answer)
                if not free_table or isinstance(free_table, tuple) and (
                        booking_data['комнаты'] == ['vip_1', 'vip_2'] or booking_data['комнаты'] == ['big_vip']):
                    bot.send_message(message.from_user.id,
                                     f'К сожалению на эту дату свободных столов нет. Вы можете связаться с нами по телефону +7 (950) 529-22-09. Для выхода в меню введите /start')
                if isinstance(free_table, int) and free_table > 0:
                    booking_data['номер стола'] = free_table
                    bot.send_message(message.from_user.id,
                                     f'Введите время в формате ЧЧ:ММ. На эту дату возможно бронирование с {booking_data["время открытия"].strftime("%H.%M")} до {booking_data["время закрытия"].strftime("%H.%M")}Для выхода в меню введите /start');
                    bot.register_next_step_handler(message, get_time)
        except ValueError:
            bot.send_message(message.from_user.id,
                             'Неверный формат даты.\n Попробуйте ещё раз.\n  Образец: 12.12.2024.Для выхода в меню введите /start')
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

            if not time_in_range(booking_data['время открытия'], booking_data['время закрытия'], time_booking):
                bot.send_message(message.from_user.id,
                                 f'На эту дату возможно бронирование с {booking_data["время открытия"].strftime("%H:%M")} до {booking_data["время закрытия"].strftime("%H:%M")}.Попробуйте ещё раз. Для выхода в меню введите /start')
                bot.register_next_step_handler(message, get_time)
            else:
                booking_data['время бронирования'] = data
                booking_data[('строка с временем')] = str(time_booking)
                bot.send_message(message.from_user.id, 'Введите номер телефона?');
                bot.register_next_step_handler(message, get_phone)
        except ValueError:
            bot.send_message(message.from_user.id,
                             'Неверный формат времени.\n Попробуйте еще раз.\n Для выхода в меню введите /start\n  Образец: 20:00')
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
            bot.send_message(message.from_user.id,
                             'Неверный формат телефона.\n Попробуйте ещё раз.\n Введите число. Образец: 81234567890\nДля выхода в меню введите /start')
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
            'количество гостей': booking_data['количество гостей'],
            'имя': booking_data['имя'],
            'телефон': booking_data['телефон'],
            'комментарий': booking_data['комментарий'], }

        bot.send_message(message.from_user.id,
                         f'Ваше бронирование принято! Данные бронирования: \n {info}.\n Мы свяжемся с вами для подтверждения брони по указанному номеру либо в telegram. Неподтвержденная бронь будет снята за час до начала. Подтвержденная бронь будет снята, если вы не пришли в течение 15 минут на момент начала бронирования . Для отмены бронирования свяжитесь с нами по телефону  +7 (950) 529-22-09 в часы работы')
        with session:
            booking = Booking(date=booking_data['дата бронирования'],
                              time=booking_data['время бронирования'],
                              guests_quantity=booking_data['количество гостей'],
                              user_name=booking_data['имя'],
                              phone=booking_data['телефон'],
                              table_number=booking_data['номер стола'],
                              comments=booking_data['комментарий'])

            session.add(booking)
            session.commit()
        start(message)

def main():
    while True:
        # bot.polling(none_stop=True)
        try:
            bot.polling(none_stop=True)
        except Exception as _ex:
            with open('log.txt', 'a') as file:
                file.write(f'{datetime.now()}: {_ex}\n')
            # print(_ex)
            sleep(1)
            continue

if __name__ == '__main__':
    main()
