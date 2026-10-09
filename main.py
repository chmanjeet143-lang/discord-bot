import os
import time
import json
import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# 1. Flask server to keep bot alive on Render 24/7
app = Flask('')

@app.route('/')
def home():
    return "🤖 Moonlight Heaven is Alive and Running!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()

# 2. Bot Intents & Configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="&", intents=intents)

@bot.event
async def on_ready():
    print(f'-----------------------------------')
    print(f'Logged in as: {bot.user.name} (ID: {bot.user.id})')
    print(f'Moonlight Heaven Bot is 100% Online!')
    print(f'-----------------------------------')

# Saare cogs ko load karne ka function (Crash prevention ke sath)
async def setup_hook():
    initial_cogs = [
        "cogs.help_menu",
        "cogs.info",
        "cogs.moderation",
        "cogs.support_tickets",
        "cogs.tickets",
        "cogs.utility"
    ]
    for cog in initial_cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded Cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load Cog {cog}: {e}")

bot.setup_hook = setup_hook

# 3. Main Execution
if __name__ == "__main__":
    # Flask Keep-Alive server ko sabse pehle start karte hain
    keep_alive()
    
    # Render Environment Variable se token utha kar bot run karna
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        raise ValueError("TOKEN environment variable is missing!")
    bot.run(TOKEN)
