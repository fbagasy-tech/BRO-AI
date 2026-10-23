import discord
import os
from threading import Thread
from flask import Flask

# عشان Render ما يفصل
app = Flask('')
@app.route('/')
def home(): return "BRO-AI is Online!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
Thread(target=run, daemon=True).start()

# كود البوت
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user: return
    if message.content.lower() == "ping":
        await message.channel.send("Pong! BRO-AI Online!")

token = os.environ.get("DISCORD_TOKEN")
if token:
    client.run(token)
else:
    print("No Token! Add DISCORD_TOKEN in Render Environment")
    
