import random
from Script import script
import re, asyncio, time, shutil, psutil, os, sys
from pyrogram import Client, filters, enums
from pyrogram.types import *
from info import BOT_START_TIME, ADMINS, PICS
from utils import humanbytes
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from html_telegraph_poster import TelegraphPoster
import requests


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

CMD = ["/", "."]

@Client.on_message(filters.command("avinfo" , CMD))
async def av_command(_, message):
    command = message.text.split(maxsplit=1)
    if len(command) == 2:
        dvd_id = command[1]
        
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
                dvd = combined_data['dvd_id']
                title = combined_data['title_en']
                preview = combined_data['sample_url']
                poster = combined_data['jacket_full_url']
                release_date = combined_data['release_date']
                runtime = combined_data['runtime_mins']
                studio = combined_data['maker_name_en']
                director = combined_data['directors'][0]['name_romaji'] if 'directors' in combined_data and len(combined_data['directors']) > 0 else 'N/A'
                actresses = ', '.join([actress['name_romaji'] for actress in combined_data['actresses']]) if 'actresses' in combined_data and len(combined_data['actresses']) > 0 else 'N/A'
                series_name_en = combined_data['series_name_en'] if 'series_name_en' in combined_data else 'N/A'
                tags = ', '.join([category['name_en'] for category in combined_data['categories']]) if 'categories' in combined_data else 'N/A'
                screenshots = [image['image_full'] for image in combined_data['gallery']] if 'gallery' in combined_data else []
                # Loop through the screenshots and modify the URLs
                for i, screenshot in enumerate(screenshots):
                    if 'jp-' not in screenshot:
                        screenshots[i] = screenshot.replace('-', 'jp-', 1)

                # Posting screenshots to Telegraph and getting the URL
                telegraph_url = post_to_telegraph(screenshots, dvd)
                
                # Send the poster as a photo
                # Create inline buttons
                buttons = [[
                            InlineKeyboardButton('𝖯𝗋𝖾𝗏𝗂𝖾𝗐', url=f"https://t.me")
                            InlineKeyboardButton('𝖲𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍𝗌', url=f"https://t.me")
                ]]
                reply_markup = InlineKeyboardMarkup(buttons)

                # Send the photo with caption and inline button              
                await message.reply_photo(photo=poster, caption=f"𝖳𝗂𝗍𝗅𝖾: {title}\n𝖣𝖵𝖣 𝖨𝖣: {dvd}\n𝖦𝖾𝗇𝗋𝖾: {tags}\n𝖱𝖾𝗅𝖾𝖺𝗌𝖾 𝖣𝖺𝗍𝖾: {release_date}\n𝖱𝗎𝗇𝗍𝗂𝗆𝖾: {runtime} Minutes\n𝖠𝖼𝗍𝗋𝖾𝗌𝗌: {actresses}\n𝖣𝗂𝗋𝖾𝖼𝗍𝗈𝗋: {director}\n𝖲𝖾𝗋𝗂𝖾𝗌: {series_name_en}\n𝖲𝗍𝗎𝖽𝗂𝗈: {studio}\nTelegraph URL: {telegraph_url}\nPreview: {preview}\n\n⚠️ 𝗂𝖭𝖥𝖮 𝖻𝗒 𝖩𝖠𝖵 𝖲𝖳𝖮𝖱𝖤", reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            else:
                await message.reply_text("No content ID found for the provided DVD ID")

        except requests.RequestException as e:
            await message.reply_text(f"Error fetching data: {e}")
    else:
        await message.reply_text("Please provide a valid DVD ID after the command.")


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

@Client.on_message(filters.command("moviessss", CMD))
async def movie(_, message):
    await message.reply_text("⚠️❗️ 𝗠𝗼𝘃𝗶𝗲 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗙𝗼𝗿𝗺𝗮𝘁 ❗️⚠️\n\n📝 𝖬𝗈𝗏𝗂𝖾 𝖭𝖺𝗆𝖾, 𝖸𝖾𝖺𝗋,(𝖨𝖿 𝗒𝗈𝗎 𝖪𝗇𝗈𝗐) 𝖶𝗂𝗍𝗁 𝖢𝗈𝗋𝗋𝖾𝖼𝗍 𝖲𝗉𝖾𝗅𝗅𝗂𝗇𝗀 📚\n\n🗣 𝖨𝖿 𝖨𝗍 𝗂𝗌 𝖺 𝖥𝗂𝗅𝗆 𝖲𝖾𝗋𝗂𝖾𝗌. 𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖮𝗇𝖾 𝖡𝗒 𝖮𝗇𝖾 𝖶𝗂𝗍𝗁 𝖯𝗋𝗈𝗉𝖾𝗋 𝖭𝖺𝗆𝖾 🧠\n\n🖇𝐄𝐱𝐚𝐦𝐩𝐥𝐞:\n\n• Robin Hood ✅\n• Robin Hood 2010✅\n• Kurup 2021 Kan✅ \n• Harry Potter and the Philosophers Stone✅\n• Harry Potter and the Prisoner of Azkaban✅\n\n🥱 𝖥𝗈𝗋 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾 𝖠𝗎𝖽𝗂𝗈𝗌 - 𝖪𝖺𝗇 𝖿𝗈𝗋 𝖪𝖺𝗇𝗇𝖺𝖽𝖺, 𝖬𝖺𝗅 - 𝖬𝖺𝗅𝖺𝗒𝖺𝗅𝖺𝗆, 𝖳𝖺𝗆 - 𝖳𝖺𝗆𝗂𝗅\n\n🔎 𝖴𝗌𝖾 𝖥𝗂𝗋𝗌𝗍 3 𝖫𝖾𝗍𝗍𝖾𝗋𝗌 𝖮𝖿 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾 𝖥𝗈𝗋 𝖠𝗎𝖽𝗂𝗈𝗌 [𝖪𝖺𝗇 𝖳𝖺𝗆 𝖳𝖾𝗅 𝖬𝖺𝗅 𝖧𝗂𝗇 𝖲𝗉𝖺 𝖤𝗇𝗀 𝖪𝗈𝗋 𝖾𝗍𝖼...]\n\n❌ [𝗗𝗼𝗻𝘁 𝗨𝘀𝗲 𝘄𝗼𝗿𝗱𝘀 𝗟𝗶𝗸𝗲 𝗗𝘂𝗯𝗯𝗲𝗱/𝗠𝗼𝘃𝗶𝗲𝘀/𝗦𝗲𝗻𝗱/𝗛𝗗 , . : - 𝗲𝘁𝗰] ❌")

@Client.on_message(filters.command("seriessss", CMD))
async def series(_, message):
    await message.reply_text("⚠️❗️ 𝗦𝗲𝗿𝗶𝗲𝘀 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗙𝗼𝗿𝗺𝗮𝘁 ❗️⚠️\n\n🗣 𝖲𝖾𝗋𝗂𝖾𝗌 𝖭𝖺𝗆𝖾,𝖲𝖾𝖺𝗌𝗈𝗇 (𝖶𝗁𝗂𝖼𝗁 𝖲𝖾𝖺𝗌𝗈𝗇 𝗒𝗈𝗎 𝗐𝖺𝗇𝗍) 🧠\n\n🖇𝐄𝐱𝐚𝐦𝐩𝐥𝐞: \n\n• Game Of Thrones S03𝖤02 720𝗉✅\n• Sex Education S02 720p✅ \n• Breaking Bad S01E05✅ \n• Prison Break 1080p✅ \n• Witcher S02✅\n\n🥱 𝖥𝗈𝗋 𝖲𝖾𝖺𝗌𝗈𝗇 𝖬𝖾𝗇𝗍𝗂𝗈𝗇 𝖠𝗌 𝖲01 𝖥𝗈𝗋 𝖲𝖾𝖺𝗌𝗈𝗇 1, 𝖲02 𝖥𝗈𝗋 𝖲𝖾𝖺𝗌𝗈𝗇 2 𝖾𝗍𝖼 [𝖲03,𝖲04 ,𝖲06,𝖲10,𝖲17] 𝖦𝗈𝖾𝗌 𝖫𝗂𝗄𝖾 𝖳𝗁𝖺𝗍\n\n🔎 𝖥𝗈𝗋 𝖤𝗉𝗂𝗌𝗈𝖽𝖾 𝖬𝖾𝗇𝗍𝗂𝗈𝗇 𝖠𝗌 𝖤𝗉01 𝖥𝗈𝗋 𝖤𝗉𝗂𝗌𝗈𝖽𝖾 1, 𝖤𝗉02 𝖥𝗈𝗋 𝖤𝗉𝗂𝗌𝗈𝖽𝖾 2 𝖾𝗍𝖼 [𝖤𝗉03,𝖤𝗉07,𝖤𝗉17,𝖤𝗉21] 𝖦𝗈'𝗌 𝖫𝗂𝗄𝖾 𝖳𝗁𝖺𝗍 \n\n❌ [𝗗𝗼𝗻𝘁 𝗨𝘀𝗲 𝘄𝗼𝗿𝗱𝘀 𝗟𝗶𝗸𝗲 𝗦𝗲𝗮𝘀𝗼𝗻/𝗘𝗽𝗶𝘀𝗼𝗱𝗲/𝗦𝗲𝗿𝗶𝗲𝘀 , . : - 𝗲𝘁𝗰] ❌")

@Client.on_message(filters.command("tutorialllll", CMD))
async def tutorial(_, message):
    await message.reply_text("𝖢𝗁𝖾𝖼𝗄𝗈𝗎𝗍 @piro_tuts 𝖥𝗈𝗋 𝖳𝗎𝗍𝗈𝗋𝗂𝖺𝗅𝗌 😎")

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
