import discord
import asyncio
import datetime
import os
from discord.ext import tasks
from flask import Flask
from threading import Thread
import aiohttp

TOKEN = os.getenv("DISCORD_TOKEN")
VOICE_CHANNEL_NAME = "BROTHER MAJLIS"

# روابط ثابتة - من مكة المكرمة - بدون توكن
RADIO_STATIONS = {
    "روتانا": "http://rotana.ae:8088/;stream.mp3",
    "قران_makkah": "https://qurango.net/radio/makkah",
    "اذان_makkah": "https://qurango.net/radio/makkah"
}

CITY = "Istanbul"
COUNTRY = "Turkey"
METHOD = 4

app = Flask('')
@app.route('/')
def home():
    return "BRO-AI V4.1 FIXED - Makkah Azan - Working"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = discord.Client(intents=intents)
voice_client = None
current_url = None
current_name = None

async def get_prayer_times():
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://api.aladhan.com/v1/timingsByCity?city={CITY}&country={COUNTRY}&method={METHOD}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['data']['timings']
    except Exception as e:
        print(f"Prayer error: {e}")
    return None

async def play_url(channel, url, name):
    global voice_client, current_url, current_name
    try:
        current_url = url
        current_name = name
        if voice_client is None or not voice_client.is_connected():
            voice_client = await channel.connect()
        if voice_client.is_playing():
            voice_client.stop()
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -user_agent "Mozilla/5.0"',
            'options': '-vn'
        }
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        voice_client.play(source)
        print(f"Playing: {name}")
        return True
    except Exception as e:
        print(f"Play error {name}: {e}")
        return False

@tasks.loop(minutes=1)
async def azan_checker():
    global voice_client, current_url, current_name
    timings = await get_prayer_times()
    if not timings:
        return
    now_str = datetime.datetime.now().strftime("%H:%M")
    names = {"Fajr": "الفجر", "Dhuhr": "الظهر", "Asr": "العصر", "Maghrib": "المغرب", "Isha": "العشاء"}
    for en, ar in names.items():
        pt = timings[en][:5]
        try:
            fmt = "%H:%M"
            diff = (datetime.datetime.strptime(pt, fmt) - datetime.datetime.strptime(now_str, fmt)).total_seconds() / 60
            if int(diff) == 10:
                for g in bot.guilds:
                    for tc in g.text_channels:
                        if tc.permissions_for(g.me).send_messages:
                            try:
                                await tc.send(f"⏰ تذكير: باقي 10 دقائق على أذان {ar} - مكة المكرمة\nاللهم رب هذه الدعوة التامة 🤲")
                                break
                            except: pass
                    break
        except: pass
        if pt == now_str:
            saved_url = current_url
            saved_name = current_name
            for guild in bot.guilds:
                for vc in guild.voice_channels:
                    if vc.name == VOICE_CHANNEL_NAME and len(vc.members) > 0:
                        if voice_client and voice_client.is_playing():
                            voice_client.stop()
                        try:
                            if voice_client is None or not voice_client.is_connected():
                                voice_client = await vc.connect()
                            azan_radio = "https://qurango.net/radio/makkah"
                            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
                            voice_client.play(discord.FFmpegPCMAudio(azan_radio, **FFMPEG_OPTIONS))
                            for tc in guild.text_channels:
                                try:
                                    await tc.send(f"🕌 نذكركم بحلول أذان صلاة {ar} حسب تقويم أم القرى - توقيت إسطنبول\n🕋 الآن: أذان الحرم المكي الشريف من مكة المكرمة\nتم إيقاف {saved_name if saved_name else 'البث'} مؤقتاً")
                                    break
                                except: pass
                            await asyncio.sleep(180)
                            if saved_url:
                                await play_url(vc, saved_url, saved_name)
                            else:
                                if voice_client:
                                    await voice_client.disconnect()
                                    voice_client = None
                            return
                        except Exception as e:
                            print(f"Azan error: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} - FIXED VERSION')
    azan_checker.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.lower()
    if "برو شغلي" in content or "برو شغل" in content:
        if not message.author.voice:
            await message.channel.send("ادخل روم BROTHER MAJLIS اول")
            return
        ch = message.author.voice.channel
        if "قران" in content or "قرآن" in content:
            url = "https://qurango.net/radio/makkah"
            await play_url(ch, url, "القرآن الكريم - من مكة المكرمة")
            await message.channel.send("🕋 أبشر، شغلت القرآن الكريم من مكة المكرمة (على الطلب)")
        elif "روتانا" in content:
            await play_url(ch, RADIO_STATIONS["روتانا"], "روتانا")
            await message.channel.send("📻 شغلت روتانا")
        elif "mbc" in content:
            await play_url(ch, RADIO_STATIONS["روتانا"], "MBC")
            await message.channel.send("📻 شغلت MBC")
        elif "http" in content:
            import re
            urls = re.findall(r'http\S+', message.content)
            if urls:
                await play_url(ch, urls[0], "رابط")
                await message.channel.send(f"🎵 شغلت الرابط: {urls[0]}")
    
    if "برو اطلع" in content or "برو اسكت" in content or content.strip() == "!اطلع":
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            voice_client = None
            current_url = None
            await message.channel.send("طلعت 🙋‍♀️")
    
    if content.startswith("!اذان"):
        timings = await get_prayer_times()
        if timings:
            await message.channel.send(f"🕋 مواقيت إسطنبول (أم القرى):\nالفجر: {timings['Fajr']}\nالظهر: {timings['Dhuhr']}\nالعصر: {timings['Asr']}\nالمغرب: {timings['Maghrib']}\nالعشاء: {timings['Isha']}\n\nالأذان من: مكة المكرمة 🕋")

Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)
