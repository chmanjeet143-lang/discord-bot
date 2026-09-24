import os
import time
import json
import random
import asyncio
import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

app = Flask('')

@app.route('/')
def home():
    return "🤖 Moonlight Heaven Massive Monster Bot is Online!"

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

DATA_FILE = "bot_database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "logs": {}, "birthdays": {}, "backups": {}, "prefixes": {},
        "warns": {}, "automod": {}, "autorole": {}, "tickets": {}, 
        "welcome": {}, "messages": {}, "voice_time": {}, "invites": {},
        "nickname_setup": {}, "counting": {}, "autoresponder": {}, "antinuke": {}, "reaction_roles": {}
    }

def save_data():
    data = {
        "logs": guild_logs, "birthdays": guild_birthdays, "backups": server_backups,
        "prefixes": guild_prefixes, "warns": guild_warns, "automod": guild_automod,
        "autorole": guild_autoroles, "tickets": guild_tickets, "welcome": guild_welcomes,
        "messages": user_messages, "voice_time": user_voice_time, "invites": user_invites,
        "nickname_setup": guild_nicknames, "counting": guild_counting, "autoresponder": guild_autoresponder,
        "antinuke": guild_antinuke, "reaction_roles": guild_reaction_roles
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()
guild_logs = {int(k): v for k, v in db.get("logs", {}).items()}
guild_birthdays = {int(k): v for k, v in db.get("birthdays", {}).items()}
server_backups = {int(k): v for k, v in db.get("backups", {}).items()}
guild_prefixes = {int(k): v for k, v in db.get("prefixes", {}).items()}
guild_warns = {int(k): v for k, v in db.get("warns", {}).items()}
guild_automod = {int(k): v for k, v in db.get("automod", {}).items()}
guild_autoroles = {int(k): v for k, v in db.get("autorole", {}).items()}
guild_tickets = {int(k): v for k, v in db.get("tickets", {}).items()}
guild_welcomes = {int(k): v for k, v in db.get("welcome", {}).items()}
user_messages = {int(k): v for k, v in db.get("messages", {}).items()}
user_voice_time = {int(k): v for k, v in db.get("voice_time", {}).items()}
user_invites = {int(k): v for k, v in db.get("invites", {}).items()}
guild_nicknames = {int(k): v for k, v in db.get("nickname_setup", {}).items()}
guild_counting = {int(k): v for k, v in db.get("counting", {}).items()}
guild_autoresponder = {int(k): v for k, v in db.get("autoresponder", {}).items()}
guild_antinuke = {int(k): v for k, v in db.get("antinuke", {}).items()}
guild_reaction_roles = {int(k): v for k, v in db.get("reaction_roles", {}).items()}

def get_prefix(bot, message):
    if not message.guild:
        return "&"
    return guild_prefixes.get(message.guild.id, "&")

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

afk_users = {}
voice_join_timestamps = {}
snipe_data = {}

# Clean & Square Modern Embed Theme (Fixed & Error-Free)
def emb(title="", description="", color=0x5865F2):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="❖ Moonlight Heaven • Developed by Zeus")
    return embed

@bot.event
async def on_ready():
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            for member in channel.members:
                if not member.bot:
                    voice_join_timestamps[(guild.id, member.id)] = time.time()

    print("----------------------------------------")
    print("Bot Name: Moonlight Heaven (Massive Edition)")
    print("Developer: Zeus")
    print("Status: All Commands Online & Optimized!")
    print("----------------------------------------")

@bot.event
async def on_command_error(ctx, error):
    p = ctx.prefix
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=emb(title="Access Denied", description="```diff\n- You do not have the required permissions to use this command.\n```"))
    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name
        usage_dict = {
            "ban": f"`{p}ban @user [reason]`",
            "kick": f"`{p}kick @user [reason]`",
            "mute": f"`{p}mute @user [minutes] [reason]`",
            "warn": f"`{p}warn @user [reason]`",
            "purge": f"`{p}purge [amount]`",
            "setprefix": f"`{p}setprefix [new_prefix]`",
            "ar": f"`{p}ar [trigger] [response]`",
            "autorole": f"`{p}autorole [@role]`",
            "giveaway": f"`{p}giveaway [time] [winners] [prize]`",
            "poll": f"`{p}poll [question]`",
            "say": f"`{p}say [text]`",
            "reminder": f"`{p}reminder [minutes] [task]`",
            "addrole": f"`{p}addrole @user @role`",
            "removerole": f"`{p}removerole @user @role`",
            "cloneemoji": f"`{p}cloneemoji [emoji] [name]`",
            "clonesticker": f"`{p}clonesticker [name]`"
        }
        correct_usage = usage_dict.get(cmd_name, f"Check help menu: `{p}help`")
        await ctx.send(embed=emb(title="⚠️ Invalid Command Usage", description=f"```yaml\nProper Way:\n{correct_usage}\n```"))
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=emb(title="⚠️ Bad Argument", description="```diff\n- You provided an invalid value. Please check your input parameters.\n
