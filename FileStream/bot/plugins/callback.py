import datetime
import math
from FileStream import version
from FileStream.bot import FileStream
from FileStream.config import Telegram, Server
from FileStream.utils.translation import LANG, BUTTON
from FileStream.utils.bot_utils import gen_link
from FileStream.utils.database_redis import DatabaseRedis  # Cambiado
from FileStream.utils.human_readable import humanbytes
from FileStream.server.exceptions import FIleNotFound
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.file_id import FileId, FileType, PHOTO_TYPES
from pyrogram.enums.parse_mode import ParseMode

db = DatabaseRedis(Telegram.DATABASE_URL)
# Se debe conectar a Redis (fuera del handler, por ejemplo al inicio del bot)
# await db.connect() --> Esta línea se ejecuta en el arranque del bot

@FileStream.on_callback_query()
async def cb_data(bot, update: CallbackQuery):
    usr_cmd = update.data.split("_")
    if usr_cmd[0] == "home":
        await update.message.edit_text(
            text=LANG.START_TEXT.format(update.from_user.mention, FileStream.username),
            disable_web_page_preview=True,
            reply_markup=BUTTON.START_BUTTONS
        )
    elif usr_cmd[0] == "help":
        await update.message.edit_text(
            text=LANG.HELP_TEXT.format(Telegram.OWNER_ID),
            disable_web_page_preview=True,
            reply_markup=BUTTON.HELP_BUTTONS
        )
    elif usr_cmd[0] == "about":
        await update.message.edit_text(
            text=LANG.ABOUT_TEXT.format(FileStream.fname, version),
            disable_web_page_preview=True,
            reply_markup=BUTTON.ABOUT_BUTTONS
        )
    elif usr_cmd[0] == "N/A":
        await update.answer("N/A", True)
    elif usr_cmd[0] == "close":
        await update.message.delete()
    elif usr_cmd[0] == "msgdelete":
        await update.message.edit_caption(
            caption="**Cᴏɴғɪʀᴍ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜᴇ Fɪʟᴇ**\n\n",
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("ʏᴇs", callback_data=f"msgdelyes_{usr_cmd[1]}_{usr_cmd[2]}"),
                    InlineKeyboardButton("ɴᴏ", callback_data=f"myfile_{usr_cmd[1]}_{usr_cmd[2]}")
                ]]
            )
        )
    elif usr_cmd[0] == "msgdelyes":
        await delete_user_file(usr_cmd[1], int(usr_cmd[2]), update)
        return
    elif usr_cmd[0] == "msgdelpvt":
        await update.message.edit_caption(
            caption="**Cᴏɴғɪʀᴍ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜᴇ Fɪʟᴇ**\n\n",
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("ʏᴇs", callback_data=f"msgdelpvtyes_{usr_cmd[1]}"),
                    InlineKeyboardButton("ɴᴏ", callback_data=f"mainstream_{usr_cmd[1]}")
                ]]
            )
        )
    elif usr_cmd[0] == "msgdelpvtyes":
        await delete_user_filex(usr_cmd[1], update)
        return
    elif usr_cmd[0] == "mainstream":
        _id = usr_cmd[1]
        reply_markup, stream_text = await gen_link(_id=_id)
        await update.message.edit_text(
            text=stream_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )
    elif usr_cmd[0] == "userfiles":
        file_list, total_files = await gen_file_list_button(int(usr_cmd[1]), update.from_user.id)
        await update.message.edit_caption(
            caption="Total files: {}".format(total_files),
            reply_markup=InlineKeyboardMarkup(file_list)
        )
    elif usr_cmd[0] == "myfile":
        await gen_file_menu(usr_cmd[1], usr_cmd[2], update)
        return
    elif usr_cmd[0] == "sendfile":
        myfile = await db.get_file(usr_cmd[1])
        file_name = myfile['file_name']
        await update.answer(f"Sending File {file_name}")
        await update.message.reply_cached_media(myfile['file_id'], caption=f'**{file_name}**')
    else:
        await update.message.delete()

# Resto de funciones `gen_file_list_button`, `gen_file_menu`, `delete_user_file`, `delete_user_filex` igual,
# sólo asegurarse que usan `await` y `db` asíncrono.
