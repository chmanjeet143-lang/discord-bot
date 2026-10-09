import os
import discord
from discord.ext import commands
from flask import Flask
import threading

# Flask server for Render uptime
app = Flask('')

@app.route('/')
def home():
    return "Moonlight Heaven Bot is online!"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Flask Server Error: {e}")

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
        "cogs.tickets",
        "cogs.support_tickets"
    ]
    for cog in initial_cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded Cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load Cog {cog}: {e}")

# Main execution using Render Environment Variable
if __name__ == "__main__":
    try:
        TOKEN = os.getenv("TOKEN")
        if not TOKEN:
            raise ValueError("TOKEN environment variable not found!")
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Critical Error starting bot: {e}")
