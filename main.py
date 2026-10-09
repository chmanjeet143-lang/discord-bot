import os
import discord
from discord.ext import commands
from flask import Flask
import threading

# Flask app taaki Render ka Web Service port active rahe
app = Flask('')

@app.route('/')
def home():
    return "Moonlight Heaven Bot is active!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Flask server ko background thread mein start karna
threading.Thread(target=run_flask, daemon=True).start()

# Intents Setup
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

async def setup_hook():
    initial_cogs = [
        "cogs.tickets",          # Staff Recruitment Button Panel
        "cogs.support_tickets"   # Support Center Dropdown Panel
    ]
    for cog in initial_cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded Cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load Cog {cog}: {e}")

# Render ke environment variable se 'TOKEN' uthana
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
