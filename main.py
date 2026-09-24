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

afk_users = {}
voice_join_timestamps = {}
snipe_data = {}

def emb(title="", description="", color=discord.Color.blue()):
    embed = discord.Embed(title=f"┌─── ❖ {title} ❖ ───┐", description=f"```yaml\n{description}\n
