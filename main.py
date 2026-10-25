Import os
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

# Default help command ko remove karte hain taaki hamara custom help menu chale
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'-----------------------------------')
    print(f'Logged in as: {bot.user.name} (ID: {bot.user.id})')
    print(f'Moonlight Heaven Bot is 100% Online!')
    print(f'-----------------------------------')

# AUTOMATIC COG LOADER: Ab cogs/ folder ki har nayi file apne aap load hogi!
async def setup_hook():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                print(f"✅ Automatically Loaded Cog: {cog_name}")
            except Exception as e:
                print(f"❌ Failed to load Cog {cog_name}: {e}")

bot.setup_hook = setup_hook

# 3. Main Execution
if __name__ == "__main__":
    keep_alive()
    
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        raise ValueError("TOKEN environment variable is missing!")
    bot.run(TOKEN)
