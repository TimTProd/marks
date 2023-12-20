# noinspection PyPackageRequirements
import telebot
import numpy as np
from config import *
from functions import *
from datetime import datetime, date, time, timedelta, timezone
import schedule


'''Initialization'''

# telegram bot
bot = telebot.TeleBot(TOKEN, threaded=False)

bot.parse_mode = "HTML"

# users database
# TODO: add SQL/dumps
# users_dict = {ADMIN ID: ['None', 'None', 0]}
# np.save('bd.npy', users_dict)
users_dict = np.load('./bd/bd.npy', allow_pickle=True).item()
users_dict = dict(users_dict)
def update_database():
    np.save('./bd/bd.npy', users_dict)

pastMarks_dict = np.load('./bd/marks.npy', allow_pickle=True).item()
pastMarks_dict = dict(pastMarks_dict)
def update_marks_database():
    np.save('./bd/marks.npy', pastMarks_dict)


# cooldown info
cooldown = {}
requests_count = {}
def clear_cooldown():
    global cooldown, requests_count
    cooldown = {}
    requests_count = {}
schedule.every().day.at("00:00").do(clear_cooldown)


# templates
keyboard1 = telebot.types.ReplyKeyboardMarkup(True, False)
keyboard1.row('Д/З')
keyboard1.row('Получить оценки')
keyboard1.row('Узнать свои данные', 'Прошлая четверть')



''' Bot events '''
# any slash command triggers Keyboard
@bot.message_handler(commands=['start'])
def info_message(message):
    bot.send_message(message.chat.id, 'Привет! Я бот для получения и анализа оценок со schools.by. Я НЕ могу отправить текст песни моргенштерна "Я когда ни-будь уйду", но если очень захочу, то смогу. Если ты тут первый раз, то надо залогиниться (если само не начало – /login).', reply_markup=keyboard1)
    if message.from_user.id not in users_dict:
        users_dict.update({message.from_user.id: ['None', 'None', 0]})
        s1 = 'Введите логин и пароль через пробел(в логине и пароле нельзя использовать пробел)'
        bot.send_message(message.chat.id, s1, reply_markup=keyboard1)
        users_dict[message.from_user.id][2] = 1
@bot.message_handler(commands=['login'])
def login_message(message):
    if message.from_user.id not in users_dict:
        users_dict.update({message.from_user.id: ['None', 'None', 0]})
    s1 = 'Введите логин и пароль через пробел(в логине и пароле нельзя использовать пробел)'
    bot.send_message(message.chat.id, s1, reply_markup=keyboard1)
    users_dict[message.from_user.id][2] = 1

@bot.message_handler(commands=["getuser"])
def answer(message):
    if (message.from_user.id == OWNER_ID):
        bot.send_message(OWNER_ID, "amogus")
        userid = int(message.text.split(maxsplit=1)[1])
        UsrInfo = bot.get_chat_member(userid, userid).user
        bot.send_message(OWNER_ID, "Id: " + str(UsrInfo.id) + "\nFirst Name: " + str(UsrInfo.first_name) + "\nLast Name: " + str(UsrInfo.last_name) +
                            "\nUsername: @" + str(UsrInfo.username))
@bot.message_handler(commands=["getdict"])
def answer(message):
    if (message.from_user.id == OWNER_ID):
        bot.send_message(OWNER_ID, str(users_dict))
@bot.message_handler(commands=["getmarks"])
def answer(message):
    if (message.from_user.id == OWNER_ID):
        userid = int(message.text.split(maxsplit=1)[1])
        try:
            marks_out = get_marks(users_dict[userid][0], users_dict[userid][1], pastMarks_dict[userid],
                            PREVIOUS_QUARTER)
            marks = marks_out[:2]
        except Exception as e:
            print(e)
            bot.send_message(OWNER_ID, 'Чет ошибка какая-то (№69)')
            return
        for mark_message in marks:
            bot.send_message(OWNER_ID, mark_message, reply_markup=keyboard1)



# main commands
to_send_logs = []  # list of logs
@bot.message_handler(content_types=['text'])
def repeat_all_messages(message):
    formatted_message = str(message.text).lower()

    # adding new users
    if message.from_user.id not in users_dict:
        users_dict.update({message.from_user.id: ['None', 'None', 0]})
    
    # adding past marks for a new user
    if message.from_user.id not in pastMarks_dict:
        pastMarks_dict.update({message.from_user.id: {}})

    # chat checking
    if message.from_user.id != message.chat.id:
        bot.send_message(message.chat.id, 'Бот не доступен для использования в чатах. Используйте личные сообщения')

    # logs
    global to_send_logs
    if to_send_logs:
        for log in to_send_logs:
            if str(log):
                bot.send_message(LOG_CHAT_ID, str(log))
        to_send_logs = []

    # cooldown and requests count
    if message.from_user.id in cooldown:
        if datetime.now() < cooldown[message.from_user.id] and (formatted_message == 'расписание' or formatted_message == 'получить оценки' or formatted_message == 'прошлая четверть'):
            seconds = (cooldown[message.from_user.id] - datetime.now()).total_seconds()
            bot.send_message(message.chat.id, f'Подождите {round(seconds)} секунд перед повторным запросом')
            return
    if message.from_user.id not in requests_count:
        requests_count[message.from_user.id] = 0

    # dev commands
    if message.from_user.id == OWNER_ID:
        if formatted_message == 'пользователи':
            c = 0
            for id, data in users_dict.items():
                if data[2] == 0:
                    c += 1
            bot.send_message(message.chat.id, f'Использует {len(users_dict) - 1}: залогиненых {c - 1}')
            return
        elif formatted_message[:8] == 'рассылка':
            bot.send_message(message.chat.id, 'Делаю рассылку')
            correct_messages_counter = 0
            messages_counter = 0
            for i in users_dict:
                messages_counter += 1
                try:
                    bot.send_message(i, str(message.text[9:]).split('\n')[-1])
                    correct_messages_counter += 1
                except Exception as e:
                    print(e)
            bot.send_message(message.chat.id, f'Конец. Успешно {correct_messages_counter}/{messages_counter}')
            return
        elif formatted_message[:3] == 'бан':
            if len(formatted_message.split(' ')) == 2:
                ban_id = formatted_message[formatted_message.find(' ')+1:]
                if ban_id.isdigit():
                    if int(ban_id) in users_dict:
                        users_dict[int(ban_id)][2] = -1
                        update_database()
                        bot.send_message(message.chat.id, f'Забанен {ban_id}')
                        return
        elif formatted_message[:5] == 'анбан':
            if len(formatted_message.split(' ')) == 2:
                ban_id = formatted_message[formatted_message.find(' ')+1:]
                if ban_id.isdigit():
                    if int(ban_id) in users_dict:
                        users_dict[int(ban_id)][2] = 0
                        update_database()
                        bot.send_message(message.chat.id, f'Разбанен {ban_id}')
                        return
        elif formatted_message[:5] == 'сброс':
            if len(formatted_message.split(' ')) == 2:
                reset_id = formatted_message[formatted_message.find(' ')+1:]
                if reset_id.isdigit():
                    if int(reset_id) in users_dict:
                        requests_count[int(reset_id)] = 0
                        bot.send_message(message.chat.id, f'Сброшен {reset_id}')
                        return
        
            

    # bans
    if users_dict[message.from_user.id][2] == -1:
        bot.send_message(message.chat.id, 'Вы были заблокированы')
        return

    # default commands
    if formatted_message == 'получить оценки' or formatted_message == 'прошлая четверть':
        if users_dict[message.from_user.id][0] != 'None':
            message_id = bot.send_message(message.chat.id,
                             'Получение данных. Ожидайте до 20 секунд... Если бот долго не отвечает, попробуйте запросить оценки ещё раз', reply_markup=keyboard1).message_id
            try:
                marks_out = get_marks(users_dict[message.from_user.id][0], users_dict[message.from_user.id][1], pastMarks_dict[message.from_user.id],
                                  PREVIOUS_QUARTER)
                marks = marks_out[:2]
                past_marks = marks_out[2]
                pastMarks_dict.update({message.from_user.id: past_marks})
                cooldown[message.from_user.id] = datetime.now() + timedelta(seconds=30)
                requests_count[message.from_user.id] += 1
            except Exception as e:
                print(e)
                if str(e):
                    bot.send_message(LOG_CHAT_ID, str(e))
                bot.send_message(message.chat.id, 'Ошибка №69. Проверьте введённые данные или напишите в компанию TimTProd.')
                return
            for mark_message in marks:
                bot.send_message(message.chat.id, mark_message, reply_markup=keyboard1)
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(LOG_CHAT_ID, f'Использовал {message.from_user.id}, {message.from_user.username}')
        else:
            bot.send_message(message.chat.id, 'У нас нету логина и пароля :( Попробуйте ввести данные ещё раз',
                             reply_markup=keyboard1)

    elif formatted_message == 'узнать свои данные':
        login, password = users_dict[message.from_user.id][0], users_dict[message.from_user.id][1]
        bot.send_message(message.chat.id, f'Логин: {login}. Пароль:{password}', reply_markup=keyboard1)

    elif formatted_message == 'д/з':
        if users_dict[message.from_user.id][0] != 'None':
            message_id = bot.send_message(message.chat.id,
                             'Получение дз. Если бот долго не отвечает, попробуйте запросить дз ещё раз').message_id
            try:
                hometask = get_hometask(users_dict[message.from_user.id][0], users_dict[message.from_user.id][1])
                cooldown[message.from_user.id] = datetime.now() + timedelta(seconds=10)
                requests_count[message.from_user.id] += 1
            except Exception as e:
                print(e)
                if str(e):
                    bot.send_message(LOG_CHAT_ID, str(e))
                bot.send_message(message.chat.id, 'Ошибка ER (прям как у стиральной машины). Проверьте введённые данные или напишите в компанию TimTProd.')
                return
            bot.send_message(message.chat.id, hometask, reply_markup=keyboard1)
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(LOG_CHAT_ID, f'Получил дз {message.from_user.id}, {message.from_user.username}')
        else:
            bot.send_message(message.chat.id, 'У нас нету логина и пароля :( Попробуйте ввести данные ещё раз',
                             reply_markup=keyboard1)

    elif users_dict[message.from_user.id][2] == 1: # login, password
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
                             'Неверный формат. Попробуйте ещё раз. Логин и пароль вводятся через пробел',
                             reply_markup=keyboard1)
            bot.delete_message(message.chat.id, message.message_id)
            
    else:
        bot.send_message(message.chat.id,
                         'Понял.', reply_markup=keyboard1)
        bot.send_message(LOG_CHAT_ID, f'Приколюха от {message.from_user.id}, {message.from_user.username}: "{message.text}"')

    update_database()
    update_marks_database()


bot.infinity_polling(timeout=10, long_polling_timeout = 5)
