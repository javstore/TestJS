import random
import re, asyncio, time, shutil, psutil, os, sys
import base64
from pyrogram import Client, filters, enums
from pyrogram.types import *
from info import BOT_START_TIME, ADMINS
from utils import humanbytes  

CMD = ["/", "."]
db_channel_id = -1002071457616  # Replace with your actual DB Channel ID

@Client.on_message(filters.command("live", CMD))
async def check_alive(client, message):
    await message.reply_text("𝖡𝗎𝖾𝗍𝗒 𝖨𝖺𝗆 𝖠𝗅𝗂𝗏𝖾 :) 𝖧𝗂𝗍 /start \n\n𝖧𝗂𝗍 /help 𝖥𝗈𝗋 𝖧𝖾𝗹𝗉 ;)\n\n\n𝖧𝗂𝗍 /ping 𝖳𝗈 𝖢𝗁𝖾𝖼𝗄 𝖡𝗈𝗍 𝖯𝗂𝗇𝗀 ")
    await client.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgIAAxkBAAELEzdlkq3YLomvHK4QAXUdHKwhqpmH6gADGgACFLvwSLdQCDPPbD-TNAQ"
    )
    await message.delete()

@Client.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(text="Forward Message from the DB Channel (with Quotes)..\nor Send the DB Channel Post link", chat_id=message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        msg_id = await get_message_id(client, channel_message, db_channel_id)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is not taken from DB Channel", quote=True)
            continue

    base64_string = await encode(f"get-{msg_id * abs(db_channel_id)}")
    link = f"https://t.me/jav_store_robot?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)

async def get_message_id(client, message, db_channel_id):
    if message.forward_from_chat:
        if message.forward_from_chat.id == db_channel_id:
            return message.forward_from_message_id
        else:
            return 0

    elif message.forward_sender_name:
        return 0

    elif message.text:
        pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)

        if matches:
            channel_id = matches.group(1)
            msg_id = int(matches.group(2))

            if channel_id.isdigit():
                if f"-100{channel_id}" == str(db_channel_id):
                    return msg_id
            else:
                if channel_id == str(db_channel_id)[1:]:
                    return msg_id

    return 0

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string
