import os
import discord
from discord.ext import commands

# Intents setUp
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="&", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# Token from Environment Variable
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
