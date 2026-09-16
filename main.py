import os
import time
import json
import random
import aiohttp
import asyncio
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
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Bot Intents & Configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.bans = True
intents.invites = True

# Dynamic prefix function
def get_prefix(bot, message):
    if not message.guild:
        return "&"
    return guild_prefixes.get(message.guild.id, "&")

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

# --- Persistent Storage Functions (JSON Based) ---
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
        "warns": {}, "automod": {}, "language": {}, "autorole": {},
        "tickets": {}, "welcome": {}
    }

def save_data():
    data = {
        "logs": guild_logs,
        "birthdays": guild_birthdays,
        "backups": server_backups,
        "prefixes": guild_prefixes,
        "warns": guild_warns,
        "automod": guild_automod,
        "language": guild_languages,
        "autorole": guild_autoroles,
        "tickets": guild_tickets,
        "welcome": guild_welcomes
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load data into memory on startup
db = load_data()
guild_logs = {int(k): v for k, v in db.get("logs", {}).items()}
guild_birthdays = {int(k): v for k, v in db.get("birthdays", {}).items()}
server_backups = {int(k): v for k, v in db.get("backups", {}).items()}
guild_prefixes = {int(k): v for k, v in db.get("prefixes", {}).items()}
guild_warns = {int(k): v for k, v in db.get("warns", {}).items()}
guild_automod = {int(k): v for k, v in db.get("automod", {}).items()}
guild_languages = {int(k): v for k, v in db.get("language", {}).items()}
guild_autoroles = {int(k): v for k, v in db.get("autorole", {}).items()}
guild_tickets = {int(k): v for k, v in db.get("tickets", {}).items()}
guild_welcomes = {int(k): v for k, v in db.get("welcome", {}).items()}

# Data Storage for runtime
user_messages = {}
user_invites = {}
user_voice_time = {}
voice_join_timestamps = {}
afk_users = {}

def get_log_channel(guild_id, log_type):
    if guild_id in guild_logs and log_type in guild_logs[guild_id]:
        guild = bot.get_guild(guild_id)
        if guild:
            return guild.get_channel(guild_logs[guild_id][log_type])
    return None

@bot.event
async def on_ready():
    if not daily_birthday_check.is_running():
        daily_birthday_check.start()
    if not auto_backup_task.is_running():
        auto_backup_task.start()
    print("----------------------------------------")
    print("Bot Name: Moonlight Heaven")
    print("Developer: Zeus")
    print("Status: Online & Ready!")
    print("----------------------------------------")

# --- GLOBAL ERROR HANDLER ---
@bot.event
async def on_command_error(ctx, error):
    p = ctx.prefix
    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        embed = discord.Embed(
            title="⚠️ Invalid Command Usage",
            description=(
                f"```ansi\n\u001b[0;31mRequired arguments are missing or invalid.\u001b[0m\n```\n"
                f"• **Proper Usage** : `{p}{ctx.command.name} [arguments]`\n"
                f"• **Help Reference** : Type `{p}menu` for assistance."
            ),
            color=discord.Color.orange()
        )

    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="🚫 Access Denied",
            description="```ansi\n\u001b[0;31mYou lack the required permissions to run this command.\u001b[0m\n```",
            color=discord.Color.red()
        )

    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            title="❌ Bot Missing Permissions",
            description="```ansi\n\u001b[0;31mI do not have the required permissions to execute this action.\u001b[0m\n```",
            color=discord.Color.red()
        )

    else:
        embed = discord.Embed(
            title="❌ Command Error",
            description=f"• **Details** : `{error}`\n• **Tip** : Use `{p}menu` to check valid command syntax.",
            color=discord.Color.red()
        )

    embed.set_footer(text="Moonlight Heaven • Developed by Zeus", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
    await ctx.send(embed=embed)

# --- BACKGROUND TASKS ---
@tasks.loop(hours=24)
async def daily_birthday_check():
    today = datetime.now().strftime("%d-%m")
    for guild_id, data in guild_birthdays.items():
        channel_id = data.get('channel')
        users_bday = data.get('users', {})
        guild = bot.get_guild(guild_id)
        if not guild or not channel_id:
            continue
        channel = guild.get_channel(channel_id)
        if not channel:
            continue
        
        for user_id_str, bday in users_bday.items():
            if bday == today:
                user_id = int(user_id_str)
                member = guild.get_member(user_id) or await guild.fetch_member(user_id)
                if member:
                    embed = discord.Embed(
                        title="🎉 Happy Birthday! 🎂",
                        description=(
                            f"```ansi\n\u001b[0;32mSpecial Birthday Celebration\u001b[0m\n```\n"
                            f"• **User** : {member.mention}\n"
                            f"• **Status** : Wishing you an incredible and joyous birthday today! 🥳✨"
                        ),
                        color=discord.Color.from_rgb(255, 105, 180)
                    )
                    embed.set_footer(text="Moonlight Heaven • Birthday Special")
                    await channel.send(content="@everyone", embed=embed)

@tasks.loop(hours=6)
async def auto_backup_task():
    for guild in bot.guilds:
        try:
            backup_data = {"categories": [], "channels_without_category": []}
            for category in guild.categories:
                cat_info = {
                    "name": category.name,
                    "position": category.position,
                    "channels": [ch.name for ch in category.channels]
                }
                backup_data["categories"].append(cat_info)
            for channel in guild.text_channels:
                if channel.category is None:
                    backup_data["channels_without_category"].append(channel.name)
            for channel in guild.voice_channels:
                if channel.category is None:
                    backup_data["channels_without_category"].append(channel.name)

            server_backups[guild.id] = backup_data
            save_data()
        except Exception as e:
            print(f"Auto backup failed for {guild.name}: {e}")

# --- WELCOME SYSTEM SETUP & EVENT ---
@bot.command(name="welcomesetup")
@commands.has_permissions(administrator=True)
async def welcomesetup(ctx, main_channel: discord.TextChannel, rules_channel: discord.TextChannel):
    """Setup dual welcome and rules channels for the server"""
    guild_welcomes[ctx.guild.id] = {
        "main_channel": main_channel.id,
        "rules_channel": rules_channel.id
    }
    save_data()
    embed = discord.Embed(
        title="✅ Welcome Setup Successful",
        description=(
            "```ansi\n\u001b[0;32mDual Welcome Channels Configured\u001b[0m\n```\n"
            f"• **Main Welcome Channel** : {main_channel.mention}\n"
            f"• **Rules / Info Channel** : {rules_channel.mention}"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="Moonlight Heaven • Welcome System", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
    await ctx.send(embed=embed)

@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    if guild_id in guild_welcomes:
        data = guild_welcomes[guild_id]
        main_ch_id = data.get("main_channel")
        rules_ch_id = data.get("rules_channel")
        
        main_channel = member.guild.get_channel(main_ch_id)
        rules_channel = member.guild.get_channel(rules_ch_id)
        
        if main_channel:
            welcome_embed = discord.Embed(
                title="✨ Welcome to Moonlight Heaven! ✨",
                description=(
                    f"Hello {member.mention}, welcome to **{member.guild.name}**! 🎉\n\n"
                    f"• Please check out {rules_channel.mention if rules_channel else 'the rules channel'} to stay safe.\n"
                    f"• Enjoy your stay and have a wonderful time with us!"
                ),
                color=discord.Color.blurple()
            )
            welcome_embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            welcome_embed.set_footer(text=f"Member #{member.guild.member_count}", icon_url=member.guild.icon.url if member.guild.icon else None)
            await main_channel.send(content=member.mention, embed=welcome_embed)

# --- UTILITY COMMANDS ---
@bot.command(name="ping")
async def ping_command(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"```ansi\n\u001b[0;36mBot Latency : {latency}ms\u001b[0m\n```",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Moonlight Heaven • Utility", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
    await ctx.send(embed=embed)

# --- DROPDOWN MENU VIEW FOR &MENU ---
class MenuSelect(discord.ui.Select):
    def __init__(self, prefix):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Command Center", description="Overview and quick-start guide", emoji="📊"),
            discord.SelectOption(label="Setups & Configuration", description="Server logs, backup, welcomes & tickets", emoji="⚙️"),
            discord.SelectOption(label="Statistics & Tracking", description="Messages, invites, voice time & resets", emoji="📈"),
            discord.SelectOption(label="Moderation / Admin", description="Warns, automod, massban & cleanup", emoji="🛡️"),
            discord.SelectOption(label="Utility & Tools", description="AFK & general tools", emoji="🛠️")
        ]
        super().__init__(placeholder="Select a category to view commands...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        p = self.prefix
        if self.values[0] == "Command Center":
            embed = discord.Embed(
                title="✨ Moonlight Heaven • Command Center",
                description=(
                    "```ansi\n\u001b[0;34mAdvanced Server Management & Utility\u001b[0m\n```\n"
                    "• **Quick Start Guide**\n"
                    f"  ‣ View Menu : `{p}menu`\n"
                    f"  ‣ Server Info : `{p}si`\n"
                    f"  ‣ Check Stats : `{p}m`, `{p}i`, `{p}v`\n\n"
                    "• **Developer** : Created by **Zeus** 🚀"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Setups & Configuration":
            embed = discord.Embed(
                title="⚙️ Setups & Configuration",
                description=(
                    "```ansi\n\u001b[0;33mAutomation & Server Management Tools\u001b[0m\n```\n"
                    f"• `{p}setup` - Generate standard log channels\n"
                    f"• `{p}welcomesetup [main_ch] [rules_ch]` - Setup dual welcome channels\n"
                    f"• `{p}nicknamesetup` - Setup interactive nickname channel\n"
                    f"• `{p}birthdaysetup` - Setup birthday collection channel\n"
                    f"• `{p}giveaway [time] [winners] [prize]` - Host an active giveaway\n"
                    f"• `{p}autorole [role]` - Set automated welcome role\n"
                    f"• `{p}ticketsetup` - Initialize support ticketing system\n"
                    f"• `{p}backup` / `{p}restore` - Server layout backup manager"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Statistics & Tracking":
            embed = discord.Embed(
                title="📈 Statistics & Tracking",
                description=(
                    "```ansi\n\u001b[0;32mReal-Time Member Activity Hub\u001b[0m\n```\n"
                    f"• `{p}m [user]` - View message activity\n"
                    f"• `{p}i [user]` - View invite statistics\n"
                    f"• `{p}v [user]` - View voice channel hours\n"
                    f"• `{p}rm [user/all]` - Reset message counter\n"
                    f"• `{p}ri [user]` - Reset invite metrics\n"
                    f"• `{p}rv [user/all]` - Reset voice duration tracking"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Moderation / Admin":
            embed = discord.Embed(
                title="🛡️ Moderation & Security",
                description=(
                    "```ansi\n\u001b[0;31mAdvanced Protection & Control Tools\u001b[0m\n```\n"
                    f"• `{p}warn [user] [reason]` - Issue a formal server warning\n"
                    f"• `{p}warns [user]` - View accumulated user warnings\n"
                    f"• `{p}automod` - Configure automated filter triggers\n"
                    f"• `{p}purge [count]` - Clear bulk chat messages\n"
                    f"• `{p}lock` / `{p}unlock` - Secure channel permissions"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Utility & Tools":
            embed = discord.Embed(
                title="🛠️ Utility & Tools",
                description=(
                    "```ansi\n\u001b[0;36mGeneral Utility Commands\u001b[0m\n```\n"
                    f"• `{p}afk [reason]` - Set your status to AFK\n"
                    f"• `{p}ping` - Check bot response latency"
                ),
                color=discord.Color.blurple()
            )
        
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus", icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None)
        await interaction.response.edit_message(embed=embed, view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="menu")
async def menu_command(ctx):
    p = ctx.prefix
    embed = discord.Embed(
        title="✨ Moonlight Heaven • Help Menu",
        description=(
            "```ansi\n\u001b[0;36mSelect a category from the dropdown menu below to view available commands.\u001b[0m\n```\n"
            "• **Developer** : Created by **Zeus** 🚀\n"
            "• **Prefix** : Use custom or default `&` prefix"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Moonlight Heaven • Interactive Menu", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
    await ctx.send(embed=embed, view=MenuView(p))

# --- RUN BOT ---
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Error: TOKEN environment variable not found!")
