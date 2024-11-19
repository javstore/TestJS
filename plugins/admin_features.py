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



# Headers for the requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

CMD = ["/", "."]

@Client.on_message(filters.command(["avinfo", "av"], CMD))
async def av_command(client: Client, message: Message):
    # Check if the user is an admin
    if message.from_user is None or message.from_user.id not in ADMINS:
        await message.reply("𝖠𝖽𝗆𝗂𝗇 𝖥𝖾𝖺𝗍𝗎𝗋𝖾𝗌 𝖭𝗈𝗍 𝖠𝗅𝗅𝗈𝗐𝖾𝗉!")
        return

    query = None
    command = message.text.split(maxsplit=1)
    if len(command) == 2:
        query = command[1]
    elif message.reply_to_message and message.reply_to_message.text:
        query = message.reply_to_message.text.strip()

    if not query:
        await message.reply_text("𝖯𝗅𝖾𝖺𝗌𝖾 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖺 𝗏𝖺𝗅𝗂𝖽 Query 𝖺𝖿𝗍𝖾𝗋 𝗍𝗁𝖾 𝖼𝗈𝗆𝗆𝖺𝗇𝖽.")
        return

    # Step 1: Fetch the first video URL from the search results
    search_url = f"https://javtrailers.com/search/{query}"
    search_response = requests.get(search_url, headers=headers)

    if search_response.status_code != 200:
        await message.reply_text("Failed to retrieve the search page.")
        return

    search_soup = BeautifulSoup(search_response.content, 'html.parser')
    card_container = search_soup.find("div", class_="card-container")
    if not card_container:
        await message.reply_text("No card container found.")
        return

    a_tag = card_container.find("a", href=True)
    if not a_tag:
        await message.reply_text("No valid video link found.")
        return

    video_url = "https://javtrailers.com" + a_tag['href']

    # Step 2: Fetch the video details from the video URL
    video_response = requests.get(video_url, headers=headers)
    if video_response.status_code != 200:
        await message.reply_text("Failed to retrieve the video page.")
        return

    video_soup = BeautifulSoup(video_response.content, 'html.parser')
    content_id = video_soup.find('span', string='Content ID:').find_next_sibling(string=True).strip()

    # Step 3: Use the provided script for image extraction
    video_details_url = f"https://javtrailers.com/video/{content_id}"
    details_response = requests.get(video_details_url, headers=headers)
    soup = BeautifulSoup(details_response.text, 'html.parser')
    script_tag = soup.find('script', id="__NUXT_DATA__")

    if not script_tag:
        await message.reply_text("Script with id='__NUXT_DATA__' not found.")
        return

    json_data = json.loads(script_tag.string)
    json_string = json.dumps(json_data)
    urlz = re.findall(r'https?://[^\s"]+', json_string)

    # Categorize URLs
    poster_url = None
    preview_urls = []
    screenshot_urls = []

    for url in urlz:
        if url.endswith("pl.jpg"):  # Poster URL
            poster_url = url
        elif url.endswith((".mp4", ".m3u8")):  # Preview URL
            preview_urls.append(url)
        elif re.search(r'\d+\.jpg$', url):  # Screenshot URL
            modified_url = re.sub(r'(\d+)-', r'\1jp-', url)
            screenshot_urls.append(modified_url)

    # Debug: Print extracted URLs
    print("Extracted URLs:", urlz)
    print("Poster URL:", poster_url)
    print("Preview URLs:", preview_urls)
    print("Screenshot URLs:", screenshot_urls)

    # If no valid URLs found
    if not poster_url and not preview_urls and not screenshot_urls:
        await message.reply_text("No valid URLs found for this video.")
        return

    # Create InlineKeyboard buttons
    buttons = []

    if preview_urls:
        buttons.append([
            InlineKeyboardButton('𝖯𝗋𝖾𝗏𝗂𝖾𝗐', url=preview_urls[0]),
            InlineKeyboardButton('𝖲𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍𝗌', url=f"{screenshot_urls[0]}" if screenshot_urls else "N/A")
        ])
    if poster_url:
        buttons.append([
            InlineKeyboardButton('𝖯𝗈𝗌𝗍𝖾𝗋', url=poster_url)
        ])

    reply_markup = InlineKeyboardMarkup(buttons)

    # Step 4: Reply to the user with results
    caption = f"""<code>{content_id}</code>
<b>⚠️ ɪɴꜰᴏ ʙʏ Jᴀᴠ Sᴛᴏʀᴇ</b>"""

    await message.reply_photo(photo=poster_url if poster_url else None, caption=caption, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)

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
