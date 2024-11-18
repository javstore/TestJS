import random
import base64
from Script import script
import re, asyncio, time, shutil, psutil, os, sys
from pyrogram import Client, filters, enums
from pyrogram.types import *
from info import BOT_START_TIME, ADMINS, PICS
from utils import humanbytes
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
#from html_telegraph_poster import TelegraphPoster
from telegraph import Telegraph
import requests
from bs4 import BeautifulSoup
import json
from html import escape


def post_to_telegraph_with_message(message):
    text_content = f"<blockquote>Provided by JAV STORE</blockquote>{message}"
    response = telegraph.create_page('Telegram Files', html_content=text_content)
    return response['url']

def post_to_telegraph_as_img(image_urls, dvd):
    text_content = f"<blockquote>Provided by JAV STORE</blockquote>"
    for url in image_urls:
        text_content += f'<img src="{url}">'

    response = telegraph.create_page(f'Screenshots of {dvd}', html_content=text_content)
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
from pyrogram.types import Message
import requests
import re
from bs4 import BeautifulSoup
import json

CMD = ["/", "."]
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def fetch_json_data(query):
    """Fetch JSON data from the webpage."""
    url = f"https://javtrailers.com/video/{query}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    script_tag = soup.find("script", {"type": "application/json", "id": "__NUXT_DATA__"})
    if not script_tag:
        return None
    return json.loads(script_tag.string)

def extract_video_details(query):
    """Extract video details from the page."""
    url = f"https://javtrailers.com/video/{query}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    try:
        details = {
            "title": soup.find('h1', class_='lead').text.strip(),
            "dvd_id": soup.find('span', string='DVD ID:').find_next_sibling(string=True).strip(),
            "content_id": soup.find('span', string='Content ID:').find_next_sibling(string=True).strip(),
            "release_date": soup.find('span', string='Release Date:').find_next_sibling(string=True).strip(),
            "duration": soup.find('span', string='Duration:').find_next_sibling(string=True).strip(),
            "studio": soup.find('span', string='Studio:').find_next('a').text.strip(),
            "categories": ' '.join(f"#{a.text.strip().replace(' ', '_')}" for a in soup.find('span', string='Categories:').parent.find_all('a')),
            "casts": ', '.join(a.text.strip() for a in soup.find('span', string='Cast(s):').parent.find_all('a')).strip()
        }
        details["casts"] = re.sub(r'[^\x00-\x7F]+', '', details["casts"])
        return details
    except AttributeError:
        return None

def classify_urls(data, query):
    """Classify URLs into posters, previews, and screenshots."""
    posters, previews, screenshots = [], [], []

    def classify(item):
        if isinstance(item, str) and item.startswith('https://'):
            if query in item or item.endswith('.mp4'):
                if item.endswith('.mp4'):
                    previews.append(item)
                elif item.endswith('pl.jpg'):
                    posters.append(item)
                elif item.endswith('.jpg'):
                    screenshots.append(item)
        elif isinstance(item, (dict, list)):
            for sub_item in item.values() if isinstance(item, dict) else item:
                classify(sub_item)

    classify(data)
    return posters, previews, screenshots

def modify_screenshots(screenshots):
    """Modify screenshot URLs."""
    return [re.sub(r'(?<=\w)-', 'jp-', url) for url in screenshots]

@Client.on_message(filters.command(["avinfo", "av"], CMD))
async def av_command(client: Client, message: Message):
    # Check if the user is an admin
    if message.from_user is None or message.from_user.id not in ADMINS:
        await message.reply("Admin features not allowed!")
        return

    query = None
    command = message.text.split(maxsplit=1)
    if len(command) == 2:
        query = command[1]
    elif message.reply_to_message and message.reply_to_message.text:
        query = message.reply_to_message.text.strip()

    if not query:
        await message.reply("Please provide a valid query after the command.")
        return

    # Fetch JSON data
    json_data = fetch_json_data(query)
    if not json_data:
        await message.reply("Failed to fetch JSON data. The video might not exist.")
        return

    # Classify URLs
    posters, previews, screenshots = classify_urls(json_data, query)

    # Modify screenshots
    screenshots = modify_screenshots(screenshots)

    # Extract video details
    video_details = extract_video_details(query)
    if not video_details:
        await message.reply("Failed to extract video details.")
        return

    # Build message
    message_text = f"""<code>{video_details['dvd_id']}</code> | {video_details['title']}
<i>DVD ID: {video_details['dvd_id']}</i>
<i>Release Date: {video_details['release_date']}</i>
<i>Duration: {video_details['duration']}</i>
<i>Studio: {video_details['studio']}</i>
<i>Categories: {video_details['categories']}</i>
<i>Cast(s): {video_details['casts']}</i>

<b>Posters:</b>
{', '.join(posters) if posters else 'No posters found'}

<b>Previews:</b>
{', '.join(previews) if previews else 'No previews found'}

<b>Screenshots:</b>
{', '.join(screenshots) if screenshots else 'No screenshots found'}

<b>⚠️ Info by JAV Store</b>
"""

    # Send the message
    await message.reply(message_text, parse_mode="HTML")

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

@Client.on_message(filters.command("premium", CMD))
async def premium(_, message):
    await message.reply_photo(
        photo="https://te.legra.ph/file/4ce1bd1b630e31a5b9ee3.png", 
        caption=script.PAYMENT_TXT, 
        parse_mode=enums.ParseMode.HTML
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
