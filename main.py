import discord, os
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"BRO AI ONLINE {bot.user}")

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return
    if "برو" in msg.content.lower() or bot.user in msg.mentions:
        await msg.channel.send(f"هلا {msg.author.display_name} 👋 أنا BRO AI شغال")
    await bot.process_commands(msg)

bot.run(os.getenv("TOKEN"))
