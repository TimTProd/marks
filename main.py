from pyrogram import Client, enums
from handlers import handlers
from callbacks import callbacks
from config import *
import numpy as np

api_id = API_ID
api_hash = API_HASH
bot_token = BOT_TOKEN

app = Client(
    "my_bot",
    api_id=api_id, api_hash=api_hash,
    bot_token=bot_token
)

app.set_parse_mode(enums.ParseMode.HTML)

handlers(app)
callbacks(app)
app.run()