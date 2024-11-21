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
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, urlunparse, urljoin
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
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}min"

async def get_video_details(url):
    """Fetch and parse video details page."""
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")

async def extract_search_result(query):
    """Search for videos and return the first video URL."""
    search_url = f"https://javtrailers.com/search/{query}"
    response = requests.get(search_url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    video_link = soup.find("a", href=lambda x: x and "/video/" in x)
    if not video_link:
        return None
    return "https://javtrailers.com" + video_link["href"]

async def parse_video_metadata(soup):
    """Extract metadata from the video page."""
    def extract_text(label):
        element = soup.find("span", string=label)
        return element.find_next_sibling(string=True).strip() if element else "N/A"

    lead_title = soup.find("h1", class_="lead")
    title = ' '.join(lead_title.text.split()[1:]) if lead_title else "N/A"

    metadata = {
        "dvd_id": extract_text("DVD ID:"),
        "content_id": extract_text("Content ID:"),
        "release_date": extract_text("Release Date:"),
        "duration": extract_text("Duration:"),
        "studio": soup.find("span", string="Studio:").find_next("a").text.strip() if soup.find("span", string="Studio:") else "N/A",
        "categories": " ".join(
            f"#{a.text.strip().replace(' ', '_')}"
            for a in soup.find("span", string="Categories:").parent.find_all("a")
        ) if soup.find("span", string="Categories:") else "N/A",
        "cast": ", ".join(
            a.text.strip()
            for a in soup.find("span", string="Cast(s):").parent.find_all("a")
        ) if soup.find("span", string="Cast(s):") else "N/A",
    }

    metadata["runtime"] = mins_to_hms(int(metadata["duration"].replace(" mins", ""))) if metadata["duration"] != "N/A" else "N/A"
    return title, metadata

async def fetch_urls_from_json(content_id):
    """Fetch JSON data for additional URLs."""
    url = f"https://javtrailers.com/video/{content_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    script_tag = soup.find("script", id="__NUXT_DATA__")
    if not script_tag:
        raise ValueError("JSON data not found in the script tag.")
    
    json_data = json.loads(script_tag.string)
    return re.findall(r"https?://[^\s\"]+", json.dumps(json_data))

async def download_poster(poster_url, content_id):
    """Download and save poster locally."""
    if not poster_url:
        return None
    response = requests.get(poster_url, headers=HEADERS)
    poster_path = f"{content_id}_poster.jpg"
    with open(poster_path, "wb") as file:
        file.write(response.content)
    return poster_path

# Constants
CMD = ["/", "."]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

@Client.on_message(filters.command(["avinfo", "av"], CMD))
async def av_command(client: Client, message: Message):
    if not message.from_user or message.from_user.id not in ADMINS:
        await message.reply("𝖠𝖽𝗆𝗂𝗇 𝖥𝖾𝖺𝗍𝗎𝗋𝖾𝗌 𝖭𝗈𝗍 𝖠𝗅𝗅𝗈𝗐𝖾𝖽!")
        return

    query = None
    if len(message.command) > 1:
        query = message.text.split(maxsplit=1)[1]
    elif message.reply_to_message and message.reply_to_message.text:
        query = message.reply_to_message.text.strip()

    if not query:
        await message.reply_text("𝖯𝗅𝖾𝖺𝗌𝖾 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖺 𝗏𝖺𝗅𝗂𝖽 𝗊𝗎𝖾𝗋𝗒.")
        return

    try:
        video_url = await extract_search_result(query)
        if not video_url:
            await message.reply_text("No video found.")
            return

        video_soup = await get_video_details(video_url)
        title, metadata = await parse_video_metadata(video_soup)

        urls = await fetch_urls_from_json(metadata["content_id"])
        poster_url = next((url for url in urls if "pl.jpg" in url), None)
        screenshot_urls = [
            url for url in urls if re.search(r"\d+\.jpg$", url) and "video" in url
        ]
        poster_path = await download_poster(poster_url, metadata["content_id"])

        # Buttons remain unchanged
        buttons = []
        preview = urls[0] if urls else None
        if preview and preview.endswith(".m3u8"):
            response = requests.get(preview)
            response.raise_for_status()
            lines = response.text.splitlines()
            m3u8_urls = [line for line in lines if line.endswith(".m3u8")]
            second_url = m3u8_urls[1]
            full_url = urljoin(preview, second_url)
            modified_url = full_url.replace("hlsvideo", "litevideo").replace(".m3u8", ".mp4")
            preview = modified_url

        if screenshot_urls and screenshot_urls:
            buttons.append([
                InlineKeyboardButton('𝖯𝗋𝖾𝗏𝗂𝖾𝗐', url=f"{preview}"),
                InlineKeyboardButton('𝖲𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍𝗌', url=f"{screenshot_urls[0]}")
            ])
            buttons.append([
                InlineKeyboardButton(f'{metadata["dvd_id"]}', url=f"{video_url}")
            ])
        else:
            buttons.append([
                InlineKeyboardButton('𝖯𝗋𝖾𝗏𝗂𝖾𝗐', url=f"{preview}")
            ])
            buttons.append([
                InlineKeyboardButton(f'{metadata["dvd_id"]}', url=f"{video_url}")
            ])
        
        reply_markup = InlineKeyboardMarkup(buttons)

        # Caption
        caption = f"""<code>{metadata['dvd_id']}</code> | {title}
<b>Categories:</b> {metadata['categories']}
<b>Release Date:</b> {metadata['release_date']}
<b>Runtime:</b> {metadata['runtime']}
<b>Studio:</b> {metadata['studio']}
<b>Cast:</b> {metadata['cast']}
"""

        if poster_path:
            await message.reply_photo(photo=poster_path, caption=caption, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            os.remove(poster_path)
        else:
            await message.reply_text(caption, reply_markup=reply_markup)

    except Exception as e:
        await message.reply_text(f"Error: {e}")

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
        photo="https://te.legra.ph/file/8df3c516a5863a8e36fc2.png", 
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
