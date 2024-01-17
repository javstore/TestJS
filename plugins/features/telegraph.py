import re, asyncio, time, shutil, psutil, os, sys
from pyrogram import Client, filters, enums
from pyrogram.types import *
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from telegraph import Telegraph

# Initialize Telegraph
telegraph = Telegraph(domain='telegra.ph')
telegraph.create_account(short_name='JAV STORE', author_name='JAV STORE', author_url='https://telegram.me/javsub_english')

# Function to post to Telegraph
def post_to_telegraph_with_message(message):
    text_content = f"<blockquote>Provided by JAV STORE</blockquote>"
    text_content += f"{message}"
    response = telegraph.create_page('Telegram Files', html_content=text_content)
    return response['url']

# Command handler for /telegraph
@Client.on_message(filters.command("telegraph", CMD) & filters.user(ADMINS))
async def telegraph_command(_, message):
    # Check if there's a message attached or if there's additional text after the command
    if message.reply_to_message and message.reply_to_message.text:
        user_message = message.reply_to_message.text
    elif len(message.text.split(maxsplit=1)) == 2:
        user_message = message.text.split(maxsplit=1)[1]
    else:
        await message.reply_text("Please provide a message to post on Telegraph.")
        return

    # Post to Telegraph and get the URL
    telegraph_url = post_to_telegraph_with_message(user_message)

    # Send the Telegraph URL to the user
    await message.reply_text(f"Your message has been posted on Telegraph. Here's the link: {telegraph_url}")
