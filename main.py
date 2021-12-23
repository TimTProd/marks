import telebot
from datetime import datetime, date, time, timedelta, timezone
from time import sleep
import math
import numpy as np
from config import *
from functions import *


'''Initialization'''

# telegram bot
bot = telebot.TeleBot(settings['token'])

# users database
# TODO: add sql
users_dict = np.load('bd.npy', allow_pickle=True).item()
users_dict = dict(users_dict)
def update_database():
    np.save('bd.npy', users_dict)


# templates
keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard1.row('Информация', 'Расписание')
keyboard1.row('Получить оценки', 'Прошлая четверть')
keyboard1.row('Ввести данные', 'Узнать свои данные')


''' Bot events '''
# any slash commands trigger buttons
@bot.message_handler(commands=['start'])
def info_message(message):
    s1 = 'Привет!'
    bot.send_message(message.chat.id, s1, reply_markup=keyboard1)


@bot.message_handler(commands=['help'])
def info_message(message):
    s1 = 'Привет!'
    bot.send_message(message.chat.id, s1, reply_markup=keyboard1)


@bot.message_handler(commands=['info'])
def info_message(message):
    s1 = 'Привет!'
    bot.send_message(message.chat.id, s1, reply_markup=keyboard1)


# main commands
to_send_logs = []
@bot.message_handler(content_types=['text'])
def repeat_all_messages(message):
    formatted_message = str(message.text).lower()

    # adding new users
    if message.from_user.id not in users_dict:
        users_dict.update({message.from_user.id: ['None', 'None', 0]})

    if message.from_user.id != message.chat.id:
        bot.send_message(message.chat.id, 'Бот не доступен для использования в чатах. Используйте личные сообщения')

    # logs
    global to_send_logs
    if to_send_logs:
        for log in to_send_logs:
            bot.send_message(LOG_CHAT_ID, str(log))
        to_send_logs = []

    # dev commands
    if message.from_user.id == OWNER_ID:
        if formatted_message == 'пользователи':
            # TODO: delete test user from db
            bot.send_message(message.chat.id, f'Использует {len(users_dict) - 1}')
            return
        elif formatted_message[:8] == 'рассылка':
            bot.send_message(message.chat.id, 'Делаю рассылку')
            correct_messages_counter = 0
            messages_counter = 0
            for i in users_dict:
                messages_counter += 1
                try:
                    bot.send_message(i, str(message.text).split('\n')[-1])
                    correct_messages_counter += 1
                except Exception as e:
                    print(e)
            bot.send_message(message.chat.id, f'Конец. Успешно {correct_messages_counter}/{messages_counter}')
            return
        elif formatted_message == 'бд':
            bot.send_message(message.chat.id, str(users_dict))
            return

    # default commands
    if formatted_message == 'информация':
        s1 = 'Привет! Я бот для получения и анализа оценок со schools.by. В данный момент я могу получать и отправлять списком твои оценки, а так же рассчитать твой средний балл. Я НЕ показываю, по каким предметам стоит н/з'
        s2 = 'По всем вопросам и предложениям: @irongun'
        bot.send_message(message.chat.id, s1)
        bot.send_message(message.chat.id, s2, reply_markup=keyboard1)
    elif formatted_message == 'получить оценки' or formatted_message == 'прошлая четверть':
        if users_dict[message.from_user.id][0] != 'None':
            bot.send_message(message.chat.id,
                             'Получение данных. Ожидайте до 20 секунд... Если бот долго не отвечает, попробуйте запросить оценки ещё раз')
            try:
                marks = get_marks(users_dict[message.from_user.id][0], users_dict[message.from_user.id][1],
                                  formatted_message == 'прошлая четверть')
            except Exception as e:
                print(e)
                bot.send_message(LOG_CHAT_ID, e)
                bot.send_message(message.chat.id, 'Ошибка EM. Проверьте введённые данные или напишите @irongun')
                return
            for mark_message in marks:
                bot.send_message(message.chat.id, mark_message)
            bot.send_message(message.chat.id,
                             'Оценки собраны за четверть. За триместр оценки могут отличаться.\nДля ИМ-ов. Триместры по следующим предметам(но это не точно): астрономия, бел. лит., бел. яз., география, дп/мп, рус. лит., рус. яз., черчение')
            bot.send_message(LOG_CHAT_ID, f'Использовал {message.from_user.id}')
        else:
            bot.send_message(message.chat.id, 'У нас нету логина и пароля :( Попробуйте ввести данные ещё раз',
                             reply_markup=keyboard1)
    elif formatted_message == 'расписание':
        if users_dict[message.from_user.id][0] != 'None':
            bot.send_message(message.chat.id,
                             'Получение расписания. Если бот долго не отвечает, попробуйте запросить расписание ещё раз')
            try:
                timetable = get_timetable(users_dict[message.from_user.id][0], users_dict[message.from_user.id][1])
            except Exception as e:
                print(e)
                bot.send_message(LOG_CHAT_ID, e)
                bot.send_message(message.chat.id, 'Ошибка ER. Проверьте введённые данные или напишите @irongun')
                return
            bot.send_message(message.chat.id, timetable)
            bot.send_message(LOG_CHAT_ID, f'Получил расписание {message.from_user.id}')
        else:
            bot.send_message(message.chat.id, 'У нас нету логина и пароля :( Попробуйте ввести данные ещё раз',
                             reply_markup=keyboard1)
    elif formatted_message == 'ввести данные':
        s1 = 'Введите логин и пароль через пробел(в логине и пароле нельзя использовать пробел)'
        bot.send_message(message.chat.id, s1, reply_markup=keyboard1)
        # next message will be login:password
        # noinspection PyTypeChecker
        users_dict[message.from_user.id][2] = 1
    elif formatted_message == 'узнать свои данные':
        login, password = users_dict[message.from_user.id][0], users_dict[message.from_user.id][1]
        bot.send_message(message.chat.id, f'Логин: {login}. Пароль:{password}', reply_markup=keyboard1)
    # login, password
    elif users_dict[message.from_user.id][2] == 1:
        if len(formatted_message.split(' ')) == 2:
            login, password = message.text.split(' ')
            users_dict.update({message.from_user.id: [login, password, 0]})
            log = '{} - {}:{} - {} {} - @{}'.format(str(get_time().strftime("%B %d, %Y. %H:%M")), login, password,
                                                    message.from_user.first_name, message.from_user.last_name,
                                                    message.from_user.username)
            bot.send_message(LOG_CHAT_ID, log)
            bot.send_message(LOG_CHAT_ID, 'Upd')
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, 'Данные успешно обновлены', reply_markup=keyboard1)
        else:
            bot.send_message(message.chat.id,
                             'Неверный формат. Попробуйте ещё-раз. Логин и пароль вводятся через пробел',
                             reply_markup=keyboard1)
            bot.delete_message(message.chat.id, message.message_id)
    else:
        bot.send_message(message.chat.id,
                         'Я тебя не понимаю :( Если ты считаешь, что я должен тебе отвечать на такие сообщения, напиши @irongun')

    update_database()


bot.polling(none_stop=True, interval=0)
# # loop
# while True:
#     try:
#         # loop
#         bot.polling(none_stop=True, interval=0)
#     except Exception as e:
#         to_send_logs.append(e)
