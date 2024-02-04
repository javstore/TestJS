import random
import base64
from Script import script
import re, asyncio, time, shutil, psutil, os, sys
from pyrogram import Client, filters, enums
from pyrogram.types import *
from info import BOT_START_TIME, ADMINS, PICS
from utils import humanbytes
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from html_telegraph_poster import TelegraphPoster
from telegraph import Telegraph
import requests
from html import escape


def post_to_telegraph_with_message(message):
    text_content = f"<blockquote>Provided by JAV STORE</blockquote>{message}"
    response = telegraph.create_page('Telegram Files', html_content=text_content)
    return response['url']


def post_to_telegraph(image_urls, dvd):
    t = TelegraphPoster(use_api=True)
    t.create_api_token('JAV STORE')

    # Create the text for the post
    text_content = "<blockquote>Provided by JAV STORE</blockquote>"
    for url in image_urls:
        text_content += f'<img src="{url}">'

    # Post to Telegra.ph
    telegraph_post = t.post(title=f'Screenshots of {dvd}', author='JAV STORE', text=text_content)
    return telegraph_post['url']

def mins_to_hms(minutes):
    h, m = divmod(minutes, 60)
    return f"{int(h):2d}h {int(m):02d}min"

from pyrogram import Client, filters

CMD_PREFIX = "/"

@Client.on_message(filters.command & filters.group)
async def delete_command_messages(client, message):
    # Check if the message starts with the specified command prefix
    if message.text.startswith(CMD_PREFIX):
        # Delete the command message
        await message.delete()


CMD = ["/", "."]

@Client.on_message(filters.command("avinfo" , CMD) & filters.user(ADMINS))
async def av_command(_, message):
    dvd_id = None
    command = message.text.split(maxsplit=1)
    if len(command) == 2:
        dvd_id = command[1]
    else:
        if message.reply_to_message and message.reply_to_message.text:
            dvd_id = message.reply_to_message.text.strip()
            
    if dvd_id: 
        url = f'https://r18.dev/videos/vod/movies/detail/-/dvd_id={dvd_id}/json'

        try:
            response = requests.get(url)
            data = response.json()
            
            if 'content_id' in data:
                content_id = data['content_id']
                combined_url = f"https://r18.dev/videos/vod/movies/detail/-/combined={content_id}/json"
                combined_response = requests.get(combined_url)
                combined_data = combined_response.json()

                # Extracting information from the JSON structure
                page = f"https://r18.dev/videos/vod/movies/detail/-/id={content_id}"
                dvd = combined_data['dvd_id']
                title = combined_data['title_en']
                preview = combined_data['sample_url']
                poster = combined_data['jacket_full_url']
                release_date = combined_data['release_date']
                runtime = combined_data['runtime_mins']
                runtime = mins_to_hms(runtime)
                studio = combined_data['maker_name_en']
                studio = studio.replace('\n', '')
                label = combined_data['label_name_en']
                director = combined_data['directors'][0]['name_romaji'] if 'directors' in combined_data and len(combined_data['directors']) > 0 else 'N/A'
                actresses = ', '.join([actress['name_romaji'] for actress in combined_data['actresses']]) if 'actresses' in combined_data and len(combined_data['actresses']) > 0 else 'N/A'
                series_name_en = combined_data['series_name_en'] if 'series_name_en' in combined_data else 'N/A'
                series_name_en = series_name_en.replace('\n', '')
                tags = ' '.join([f"#{category['name_en'].replace(' ', '').replace('-', '')}" for category in combined_data['categories'] if category.get('name_en') and '*' not in category['name_en']]) if 'categories' in combined_data else 'N/A'
                tags = tags.replace("'", "")
                screenshots = [image['image_full'] for image in combined_data['gallery']] if 'gallery' in combined_data else []
                # Loop through the screenshots and modify the URLs
                for i, screenshot in enumerate(screenshots):
                    if 'jp-' not in screenshot:
                        screenshots[i] = screenshot.replace('-', 'jp-', 1)

                # Posting screenshots to Telegraph and getting the URL
                telegraph_url = post_to_telegraph(screenshots, dvd)
                
                # Create inline buttons
                buttons = []

                if preview is not None:
                    buttons.append([
                        InlineKeyboardButton('𝖯𝗋𝖾𝗏𝗂𝖾𝗐', url=f"{preview}"),
                        InlineKeyboardButton('𝖲𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍𝗌', url=f"{telegraph_url}")
                    ])
                    buttons.append([
                        InlineKeyboardButton(f'{dvd}', url=f"{page}")
                    ])
                else:
                    buttons.append([
                        InlineKeyboardButton('𝖲𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍𝗌', url=f"{telegraph_url}")
                    ])
                    buttons.append([
                        InlineKeyboardButton(f'{dvd}', url=f"{page}")
                    ])

                reply_markup = InlineKeyboardMarkup(buttons)


                caption=f"""<code>{dvd}</code> | {title}
<i>𝖣𝖵𝖣 𝖨𝖣 : {dvd}</i>
<i>𝖦𝖾𝗇𝗋𝖾 : {tags}</i>
<i>𝖱𝖾𝗅𝖾𝖺𝗌𝖾 𝖣𝖺𝗍𝖾 : {release_date}</i>
<i>𝖱𝗎𝗇𝗍𝗂𝗆𝖾 : {runtime}</i>
<i>𝖠𝖼𝗍𝗋𝖾𝗌𝗌 : {actresses}</i>
<i>𝖣𝗂𝗋𝖾𝖼𝗍𝗈𝗋 : {director}</i>
<i>𝖲𝖾𝗋𝗂𝖾𝗌 : {series_name_en}</i>
<i>𝖲𝗍𝗎𝖽𝗂𝗈 : {studio}</i>
<i>𝖫𝖺𝖻𝖾𝗅 : {label}</i>

<b>⚠️ ɪɴꜰᴏ ʙʏ Jᴀᴠ Sᴛᴏʀᴇ</b>
"""

                # Send the photo with caption and inline button              
                await message.reply_photo(photo=poster, caption=caption, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            else:
                await message.reply_text("No content ID found for the provided DVD ID")

        except requests.RequestException as e:
            await message.reply_text(f"Error fetching data: {e}")
    else:
        await message.reply_text("𝖯𝗅𝖾𝖺𝗌𝖾 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖺 𝗏𝖺𝗅𝗂𝖽 𝖣𝖵𝖣 𝖨𝖣 𝖺𝖿𝗍𝖾𝗋 𝗍𝗁𝖾 𝖼𝗈𝗆𝗆𝖺𝗇𝖽.")


@Client.on_message(filters.command("alive", CMD))
async def check_alive(client, message):
    await client.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgIAAxkBAAELEzdlkq3YLomvHK4QAXUdHKwhqpmH6gADGgACFLvwSLdQCDPPbD-TNAQ"
    )
    await message.delete()


@Client.on_message(filters.command("help", CMD))
async def help(_, message):
    await message.reply_text("𝖦𝖾𝗍𝗍𝗂𝗇𝗀 𝖳𝗋𝗈𝗎𝖻𝗅𝖾 𝗂𝗇 𝖲𝗈𝗆𝖾𝗍𝗂𝗆𝖾?\n𝖱𝖾𝗉𝗈𝗋𝗍 𝖧𝖾𝗋𝖾 𝗐𝗂𝗍𝗁 #𝖺𝖽𝗆𝗂𝗇\n\n⚠️ @jav_sub_movies")

@Client.on_message(filters.command("admin", CMD) & filters.user(ADMINS))
async def admin_panel(client, message):
    oii = await client.send_photo(
        chat_id=message.from_user.id,
        photo=random.choice(PICS),
        caption=script.ADMIN_TXT
    )

@Client.on_message(filters.command("ping", CMD))
async def ping(_, message):
    start_t = time.time()
    rm = await message.reply_text("...........")
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await rm.edit(f"𝖯𝗂𝗇𝗀!\n{time_taken_s:.3f} ms")

@Client.on_message(filters.command("status"))          
async def stats(bot, update):
    currentTime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - BOT_START_TIME))
    total, used, free = shutil.disk_usage(".")
    total = humanbytes(total)
    used = humanbytes(used)
    free = humanbytes(free)
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent

    ms_g = f"""<b>⚙️ 𝖡𝗈𝗍 𝖲𝗍𝖺𝗍𝗎𝗌</b>

🕔 𝖴𝗉𝗍𝗂𝗆𝖾: <code>{currentTime}</code>
🛠 𝖢𝖯𝖴 𝖴𝗌𝖺𝗀𝖾: <code>{cpu_usage}%</code>
🗜 𝖱𝖠𝖬 𝖴𝗌𝖺𝗀𝖾: <code>{ram_usage}%</code>
🗂 𝖳𝗈𝗍𝖺𝗅 𝖣𝗂𝗌𝗄 𝖲𝗉𝖺𝖼𝖾: <code>{total}</code>
🗳 𝖴𝗌𝖾𝖽 𝖲𝗉𝖺𝖼𝖾: <code>{used} ({disk_usage}%)</code>
📝 𝖥𝗋𝖾𝖾 𝖲𝗉𝖺𝖼𝖾: <code>{free}</code> """

    msg = await bot.send_message(chat_id=update.chat.id, text="__𝖯𝗋𝗈𝖼𝖾𝗌𝗌𝗂𝗇𝗀...__", parse_mode=enums.ParseMode.MARKDOWN)         
    await msg.edit_text(text=ms_g, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def stop_button(bot, message):
    msg = await bot.send_message(text="**𝖡𝗈𝗍 𝖨𝗌 𝖱𝖾𝗌𝗍𝖺𝗋𝗍𝗂𝗇𝗀...🪄**", chat_id=message.chat.id)       
    await asyncio.sleep(3)
    await msg.edit("**𝖡𝗈𝗍 𝖱𝖾𝗌𝗍𝖺𝗋𝗍𝖾𝖽 𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒 ! 𝖱𝖾𝖺𝖽𝗒 𝖳𝗈 𝖬𝗈𝗏𝖾 𝖮𝗇 💯**")
    os.execl(sys.executable, sys.executable, *sys.argv)
    

# Initialize Telegraph
telegraph = Telegraph(domain='graph.org')
telegraph.create_account(short_name='JAV STORE', author_name='JAV STORE', author_url='https://telegram.me/javsub_english')
template = escape("""<br><br>
🔰 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗟𝗶𝗻𝗸: <a href="dddddd">https://javstore.in/video/protected-link</a>

<br><br>
🔐 𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱: <a href="pppppp">https://teraboxapp.com/v/unlock-password-link</a>

<br><br>
<i>Note: Password Given in Video! Watch Carefully</i>
""")

# Command handler for /telegraph
@Client.on_message(filters.command("telegraph", CMD) & filters.user(ADMINS))
async def telegraph_command(_, message):
    # Check if there's a message attached or if there's additional text after the command
    if message.reply_to_message and message.reply_to_message.text:
        user_message = message.reply_to_message.text
    elif len(message.text.split(maxsplit=1)) == 2:
        user_message = message.text.split(maxsplit=1)[1]
    else:
        await message.reply_text(f"`{template}`")
        return

    # Post to Telegraph and get the URL
    telegraph_link = post_to_telegraph_with_message(user_message)

    # Send the Telegraph URL to the user
    await message.reply_text(f"Your message has been posted on Telegraph, Here's the link: {telegraph_link}")
