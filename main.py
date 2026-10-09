import os
import json
import asyncio
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "🤖 Moonlight Heaven Mega Bot 1000+ Edition is Online!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.presences = True
intents.invites = True

DATA_FILE = "bot_database.json"

def get_prefix(bot, message):
    if not message.guild:
        return "&"
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                return data.get("prefixes", {}).get(str(message.guild.id), "&")
        except:
            pass
    return "&"

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

@bot.event
async def on_ready():
    print("----------------------------------------")
    print(f"Bot Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print("Status: Ultimate Mega Bot 1000+ Active!")
    print("----------------------------------------")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Sync Error: {e}")

async def load_extensions():
    if not os.path.exists("cogs"):
        os.makedirs("cogs")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"📂 Loaded Cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

async def main():
    async with bot:
        await load_extensions()
        TOKEN = os.getenv("TOKEN")
        if TOKEN:
            await bot.start(TOKEN)
        else:
            print("❌ Error: TOKEN environment variable nahi mila!")

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
