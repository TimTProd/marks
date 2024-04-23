from functions import get_hometask
from db import get_login, get_password
from config import Q_NUM, START_FROM, LOG_CHAT_ID
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def callbacks(app):

    @app.on_callback_query()
    async def callback_query(app, CallbackQuery):
        data = CallbackQuery.data
        user_id = CallbackQuery.from_user.id

        if data.startswith('next_'):
            n = int(data.split("_")[1])
            info_message = await CallbackQuery.edit_message_text("Получение дз...")
            try:
                hometask = await get_hometask(get_login(user_id), get_password(user_id), Q_NUM, data)
            except Exception as e:
                await CallbackQuery.edit_message_text(f'Чет ошибка какая-то: {e}')
                return
            inlineKeyboard = [
                [InlineKeyboardButton("на эту неделю", callback_data=f"start"),
                InlineKeyboardButton("-->", callback_data=f"next_{n+1}")]
            ]
            await CallbackQuery.edit_message_text(hometask, reply_markup=InlineKeyboardMarkup(inlineKeyboard))
            await CallbackQuery.answer()
            await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{CallbackQuery.from_user.username}) got {data} hometask")
        elif data.startswith('previous_'):
            n = int(data.split("_")[1])
            info_message = await CallbackQuery.edit_message_text("Получение дз...")
            try:
                hometask = await get_hometask(get_login(user_id), get_password(user_id), Q_NUM, data)
            except Exception as e:
                await CallbackQuery.edit_message_text(f'Чет ошибка какая-то: {e}')
                return
            inlineKeyboard = [
                [InlineKeyboardButton("<--", callback_data=f"previous_{n+1}"),
                InlineKeyboardButton("на эту неделю", callback_data=f"start")]
            ]
            await CallbackQuery.edit_message_text(hometask, reply_markup=InlineKeyboardMarkup(inlineKeyboard))
            await CallbackQuery.answer()
            await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{CallbackQuery.from_user.username}) got {data} hometask")
        elif data == 'start':
            info_message = await CallbackQuery.edit_message_text("Получение дз...")
            try:
                hometask = await get_hometask(get_login(user_id), get_password(user_id), Q_NUM, data)
            except Exception as e:
                await CallbackQuery.edit_message_text(f'Чет ошибка какая-то: {e}')
                return
            inlineKeyboard = [
                [InlineKeyboardButton("<--", callback_data=f"previous_1"),
                InlineKeyboardButton("-->", callback_data=f"next_1")]
            ]
            await CallbackQuery.edit_message_text(hometask, reply_markup=InlineKeyboardMarkup(inlineKeyboard))
            await CallbackQuery.answer()
            await app.send_message(LOG_CHAT_ID, f"User {user_id} (@{CallbackQuery.from_user.username}) got hometask")
            