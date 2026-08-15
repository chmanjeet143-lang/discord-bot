import os
from discord.ext import commands
import discord
from flask import Flask
from threading import Thread

# 1. Render ke liye Uptime Keep-Alive Server
app = Flask("")


@app.route("/")
def home():
  return "🤖 Bot is Alive and Running!"


def run():
  app.run(host="0.0.0.0", port=10000)


def keep_alive():
  t = Thread(target=run)
  t.start()


# 2. Bot Intents & Configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

# Bot ka prefix yahan '&' set hai
bot = commands.Bot(command_prefix="&", intents=intents)


# 3. Bot Ready Event, Status & Cogs Auto-Loader
@bot.event
async def on_ready():
  print(f"-----------------------------------")
  print(f"Logged in as: {bot.user.name} (ID: {bot.user.id})")
  print(f"Status: Online & Ready!")
  print(f"-----------------------------------")

  # Bot ka Rich Presence Status set karein
  activity = discord.Activity(
      type=discord.ActivityType.watching, name="&help | Managing Servers"
  )
  await bot.change_presence(status=discord.Status.online, activity=activity)

  # Cogs folder se saari files automatically load karega
  for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
      try:
        await bot.load_extension(f"cogs.{filename[:-3]}")
        print(f"✅ Loaded Cog Module: {filename[:-3]}")
      except Exception as e:
        print(f"❌ Failed to load {filename[:-3]}: {e}")


# 4. Quick Core Feature: Ping Command
@bot.command(name="ping")
async def ping(ctx):
  """Bot ki speed/latency check karne ke liye"""
  latency = round(bot.latency * 1000)
  embed = discord.Embed(
      title="🏓 Pong!",
      description=f"Bot ki speed **{latency}ms** hai.",
      color=discord.Color.green(),
  )
  await ctx.reply(embed=embed)


# Bot ko online rakhne ke liye server start karein
keep_alive()

# Yahan apna asli Discord Bot Token daal dein
bot.run("YOUR_BOT_TOKEN_HERE")

