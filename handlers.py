from pyrogram import Client, filters 
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from db import *
from functions import get_marks, get_hometask
from config import OWNER_ID, Q_NUM, START_FROM, PREV_Q_NUM, PREV_START_FROM, PARSE_PREVIOUS, LOG_CHAT_ID

def handlers(app):
    @app.on_message(filters.command("start"))
    async def start_handler(client, message):
        await message.reply("Привет! Я бот для получения оценок и д/з со schools.by")
        user_id = message.from_user.id
        await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{message.from_user.username}) send /start")

        if not user_exists(user_id):
            create_user(user_id)
            create_pastMarks(user_id)
            await message.reply("Сначала нужно залогиниться!")
            await message.reply("Введите логин:")
            set_state(user_id, "login")
            await app.send_message(LOG_CHAT_ID, f"Created new user {user_id} (@{message.from_user.username}), starting login process")

    @app.on_message(filters.command("login"))
    async def login_handler(client, message):
        await message.reply("Введите логин:", ReplyKeyboardRemove())
        set_state(message.from_user.id, "login")
        await app.send_message(LOG_CHAT_ID, f"User {message.from_user.id} (@{message.from_user.username}) started login process")

    @app.on_message(filters.command("get"))
    async def get_login_handler(client, message):
        user_id = message.from_user.id
        login = get_login(user_id)
        password = get_password(user_id)
        await message.reply(f'Логин: {login}. Пароль: {password}', reply_markup=ReplyKeyboardMarkup([["Д/З"], ["Получить оценки"]], resize_keyboard=True))
        await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{message.from_user.username}) got login and password")
    
    #admin commands
    @app.on_message(filters.command("getuser"))
    async def answer(client, message):
        if (message.from_user.id == OWNER_ID):
            userid = int(message.text.split(maxsplit=1)[1])
            info = await app.get_users(userid)
            await message.reply(info)
            await message.reply(info.username)
    
    @app.on_message(filters.command("getdict"))
    async def answer(client, message):
        if (message.from_user.id == OWNER_ID):
            await message.reply(get_dict())
    
    @app.on_message(filters.command("getmarks"))
    async def answer(client, message):
        if (message.from_user.id == OWNER_ID):
            user_id = int(message.text.split(maxsplit=1)[1])
            try:
                marks_out = await get_marks(get_login(user_id), get_password(user_id), Q_NUM, START_FROM, PREV_Q_NUM, PREV_START_FROM, PARSE_PREVIOUS, get_pastMarks(user_id))
            except Exception as e:
                await message.reply(f'Чет ошибка какая-то: {e}')
                return
            if type(marks_out) == str:
                await message.reply(f'Чет ошибка какая-то: {marks_out}')
                return
            marks = marks_out[:2]
            past_marks = marks_out[2]
            for mark_message in marks:
                await message.reply(mark_message, reply_markup=ReplyKeyboardMarkup([["Д/З"], ["Получить оценки"]], resize_keyboard=True))

    
    # keyboard answers
    @app.on_message(filters.text & filters.regex("^Д/З$"))
    async def answer(client, message):
        if get_login(message.from_user.id) != "None":
            info_message = await message.reply("Получение дз...")
            user_id = message.from_user.id
            try:
                hometask = await get_hometask(get_login(user_id), get_password(user_id), Q_NUM)
            except Exception as e:
                await message.reply(f'Чет ошибка какая-то: {e}')
                return
            inlineKeyboard = [
                [InlineKeyboardButton("<--", callback_data="previous_1"),
                InlineKeyboardButton("-->", callback_data="next_1")]
            ]
            await message.reply(hometask, reply_markup=InlineKeyboardMarkup(inlineKeyboard))
            await info_message.delete()
            await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{message.from_user.username}) got hometask")
        else:
            await message.reply("Логина и пароля нет... Надо залогиниться")
            await message.reply("Введите логин:", ReplyKeyboardRemove())
            set_state(user_id, "login")
            await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{message.from_user.username}) accesed hometask without login and password, starting login process")
    
    @app.on_message(filters.text & filters.regex("^Получить оценки$"))
    async def answer(client, message):
        if get_login(message.from_user.id) != "None":
            info_message = await message.reply("Получение отметок...")
            user_id = message.from_user.id
            try:
                marks_out = await get_marks(get_login(user_id), get_password(user_id), Q_NUM, START_FROM, PREV_Q_NUM, PREV_START_FROM, PARSE_PREVIOUS, get_pastMarks(user_id))
            except Exception as e:
                await message.reply(f'Чет ошибка какая-то: {e}')
                await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{message.from_user.username}) got exception '{e}' while getting hometask")
                return
            if type(marks_out) == str:
                await message.reply(marks_out)
                return
            marks = marks_out[:2]
            past_marks = marks_out[2]
            for mark_message in marks:
                await message.reply(mark_message, reply_markup=ReplyKeyboardMarkup([["Д/З"], ["Получить оценки"]], resize_keyboard=True))
            await info_message.delete()
            set_pastMarks(user_id, past_marks)
            update_marks_database()
            await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{message.from_user.username}) got marks")
        else:
            await message.reply("Логина и пароля нет... Надо залогиниться")
            await message.reply("Введите логин:", ReplyKeyboardRemove())
            set_state(user_id, "login")
            await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{message.from_user.username}) accesed hometask without login and password, starting login process")

    
    @app.on_message(filters.text)
    async def text_handler(client, message):
        """
        Handles input text messages received by the client.

        Args:
            client: The client object.
            message: The message object containing the text.

        Returns:
            None
        """
        user_id = message.from_user.id
        user_state = get_state(user_id)

        if user_state == "login":
            login = message.text
            set_login(user_id, login)
            await message.reply("Введите пароль:")
            set_state(user_id, "password")
        elif user_state == "password":
            password = message.text
            set_password(user_id, password)
            set_state(user_id, 0)
            update_database()
            await message.reply("Вы успешно залогинились!", reply_markup=ReplyKeyboardMarkup([["Д/З"], ["Получить оценки"]], resize_keyboard=True))
            await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{message.from_user.username}) logged in")
        elif user_state == 0:
            await message.reply("Не понял", reply_markup=ReplyKeyboardMarkup([["Д/З"], ["Получить оценки"]], resize_keyboard=True))


