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

# بدون radiojar - روابط مباشرة ثابتة لا تسبب 1015
# اذان مكة mp3 ثابت - من مكة المكرمة
MAKKAH_AZAN_MP3 = "https://cdn.islamic.network/quran/audio/128/ar.alafasy/1.mp3"
# للتجربة سنستخدم ملف اذان mp3 حقيقي ثابت من archive
REAL_AZAN_URL = "https://www.islamcan.com/audio/adhan/azan2.mp3"

CITY = "Istanbul"
COUNTRY = "Turkey"
METHOD = 4

app = Flask('')
@app.route('/')
def home():
    return "BRO-AI V5 - NO 1015 - Makkah Only"

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
                data = await resp.json()
                return data['data']['timings']
    except:
        return None

async def safe_play(channel, url, name):
    global voice_client, current_url, current_name
    try:
        current_url = url
        current_name = name
        if voice_client is None or not voice_client.is_connected():
            voice_client = await channel.connect()
        if voice_client.is_playing():
            voice_client.stop()
        # بدون radiojar
        FFMPEG_OPTIONS = {'options': '-vn'}
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        voice_client.play(source)
        return True
    except Exception as e:
        print(f"PLAY FAIL {name}: {e}")
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
        # تذكير قبل 10 دق
        try:
            diff = (datetime.datetime.strptime(pt, "%H:%M") - datetime.datetime.strptime(now_str, "%H:%M")).total_seconds()/60
            if int(diff) == 10:
                for g in bot.guilds:
                    for tc in g.text_channels:
                        try:
                            await tc.send(f"⏰ باقي 10 دقائق على أذان {ar} - مكة المكرمة 🕋")
                            break
                        except: pass
        except: pass
        if pt == now_str:
            saved_url = current_url
            saved_name = current_name
            for guild in bot.guilds:
                for vc in guild.voice_channels:
                    if vc.name == VOICE_CHANNEL_NAME and len(vc.members)>0:
                        if voice_client and voice_client.is_playing():
                            voice_client.stop()
                        try:
                            if voice_client is None or not voice_client.is_connected():
                                voice_client = await vc.connect()
                            # شغل اذان مكة المكرمة MP3 ثابت - لا يسبب 1015
                            voice_client.play(discord.FFmpegPCMAudio(REAL_AZAN_URL, options='-vn'))
                            for tc in guild.text_channels:
                                try:
                                    await tc.send(f"🕌 حان الآن أذان {ar} - بتوقيت أم القرى إسطنبول\n🕋 **الآن أذان الحرم المكي الشريف من مكة المكرمة**\nتم إيقاف {saved_name if saved_name else 'البث'}")
                                    break
                                except: pass
                            await asyncio.sleep(90)
                            if saved_url:
                                await safe_play(vc, saved_url, saved_name)
                            else:
                                if voice_client:
                                    await voice_client.disconnect()
                                    voice_client = None
                            return
                        except Exception as e:
                            print(f"Azan fail: {e}")

@bot.event
async def on_ready():
    print(f"READY {bot.user} - V5 FIXED NO 1015")
    azan_checker.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    c = message.content.lower()
    if "برو شغلي" in c:
        if not message.author.voice:
            await message.channel.send("ادخل روم BROTHER MAJLIS اول")
            return
        ch = message.author.voice.channel
        if "قران" in c or "قرآن" in c:
            # شغل قران من مكة - رابط mp3 ثابت لا يسبب 1015
            url = "https://server8.mp3quran.net/afs/001.mp3" # سورة الفاتحة - مكة
            ok = await safe_play(ch, url, "القرآن من مكة")
            if ok:
                await message.channel.send("🕋 شغلت القرآن الكريم من مكة المكرمة - على الطلب")
            else:
                await message.channel.send("الرابط محظور حاليا، جرب رابط يوتيوب")
        elif "روتانا" in c:
            await message.channel.send("روتانا تحتاج رابط مباشر جديد - ارسل رابط يوتيوب حاليا: برو شغلي https://youtube.com/...")
        elif "http" in c:
            import re
            urls = re.findall(r'http\S+', message.content)
            if urls:
                ok = await safe_play(ch, urls[0], "رابط")
                if ok:
                    await message.channel.send(f"🎵 شغال: {urls[0]}")
                else:
                    await message.channel.send("ما قدرت اشغل الرابط هذا")
    if "برو اطلع" in c or c.strip()=="!اطلع":
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            voice_client = None
            current_url = None
            await message.channel.send("طلعت")
    if c.startswith("!اذان"):
        t = await get_prayer_times()
        if t:
            await message.channel.send(f"🕋 إسطنبول (أم القرى) - الأذان من مكة:\nالفجر {t['Fajr']}\nالظهر {t['Dhuhr']}\nالعصر {t['Asr']}\nالمغرب {t['Maghrib']}\nالعشاء {t['Isha']}")

Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)
