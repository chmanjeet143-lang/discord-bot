import os
import time
import json
import random
import aiohttp
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
        "tickets": {}, "confessions": {}
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
        "confessions": guild_confessions
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
guild_confessions = {int(k): v for k, v in db.get("confessions", {}).items()}

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
    print(f"----------------------------------------")
    print(f"Bot Name: Moonlight Heaven")
    print(f"Developer: Zeus")
    print(f"Status: Online & Ready (Extended Features Loaded)!")
    print(f"----------------------------------------")


# --- GLOBAL ERROR HANDLER ---
@bot.event
async def on_command_error(ctx, error):
    p = ctx.prefix
    
    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="⚠️ Missing Argument",
            description=f"• **Error** : Kuch zaroori details gayab hain!\n• **Usage** : Is command ko use karne ka sahi tarika dekhein ya `{p}menu` check karein.",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)

    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="🚫 Access Denied",
            description="• **Error** : Aapke paas yeh command chalane ki permission nahi hai!",
            color=discord.Color.red()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)

    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            title="❌ Bot Missing Permissions",
            description="• **Error** : Mere paas yeh action lene ke liye zaroori permissions nahi hain!",
            color=discord.Color.red()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)

    else:
        embed = discord.Embed(
            title="❌ Command Error",
            description=f"• **Details** : `{error}`",
            color=discord.Color.red()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)


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
                        description=f"• **User** : {member.mention}\n• **Status** : Wishing you a wonderful birthday today! 🥳✨\n\n*Developed by Zeus*",
                        color=discord.Color.from_rgb(255, 105, 180)
                    )
                    embed.set_footer(text="Moonlight Heaven • Birthday Special")
                    await channel.send(content="@everyone", embed=embed)

@tasks.loop(hours=6)
async def auto_backup_task():
    for guild in bot.guilds:
        try:
            backup_data = {
                "categories": [],
                "channels_without_category": []
            }
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


# --- DROPDOWN SELECT MENU VIEW FOR &MENU ---

class MenuSelect(discord.ui.Select):
    def __init__(self, prefix):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Command Center", description="Overview and quick-start guide", emoji="📊"),
            discord.SelectOption(label="Setups & Configuration", description="Server logs, backup, autorole & tickets", emoji="⚙️"),
            discord.SelectOption(label="Statistics & Tracking", description="Messages, invites, voice time & resets", emoji="📈"),
            discord.SelectOption(label="Moderation / Admin", description="Warns, automod, massban & cleanup", emoji="🛡️"),
            discord.SelectOption(label="Utility & Tools", description="Weather, urban, translate, confessions", emoji="🛠️"),
            discord.SelectOption(label="Fun & Interaction", description="Coinflip, hug, slap, pat, giveaways", emoji="🎉")
        ]
        super().__init__(placeholder="Select a category to view commands...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        p = self.prefix
        if self.values[0] == "Command Center":
            embed = discord.Embed(
                title="Moonlight Heaven",
                description=(
                    "**Command Center**\n"
                    "Clean, reliable server management and interactive utility.\n\n"
                    "**Quick Start:**\n"
                    f"• **View Menu** : Type `{p}menu`\n"
                    f"• **Server Info** : Type `{p}si`\n"
                    f"• **Check Stats** : Type `{p}m`, `{p}i`, `{p}v`\n"
                    "• **Developer** : Created by **Zeus** ✨"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Setups & Configuration":
            embed = discord.Embed(
                title="⚙️ Setups & Configuration",
                description=(
                    "Manage server automation, autoroles, tickets, and configs.\n\n"
                    f"• `{p}setup` - Create all automated log channels\n"
                    f"• `{p}nicknamesetup` - Nickname change channel\n"
                    f"• `{p}birthdaysetup` - Birthday collection channel\n"
                    f"• `{p}autorole [role]` - Set automated welcome role\n"
                    f"• `{p}ticketsetup` - Setup ticket system\n"
                    f"• `{p}language [lang_code]` - Set server language\n"
                    f"• `{p}backup` & `{p}restore` - Server layout backup/restore"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Statistics & Tracking":
            embed = discord.Embed(
                title="📈 Statistics & Tracking",
                description=(
                    "Keep track of member activity in real time.\n\n"
                    f"• `{p}m [user]` - Check message count\n"
                    f"• `{p}i [user]` - Check invite count\n"
                    f"• `{p}v [user]` - Check voice channel time\n"
                    f"• `{p}rm [user/all]` - Reset messages\n"
                    f"• `{p}ri [user]` - Reset invites\n"
                    f"• `{p}rv [user/all]` - Reset voice time"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Moderation / Admin":
            embed = discord.Embed(
                title="🛡️ Moderation & Admin",
                description=(
                    "Advanced security, warnings, and protection tools.\n\n"
                    f"• `{p}warn [user] [reason]` - Warn a member\n"
                    f"• `{p}warnings [user]` - Check user warnings\n"
                    f"• `{p}clearwarn [user]` - Clear warnings\n"
                    f"• `{p}massban [user1] [user2] ...` - Ban multiple users\n"
                    f"• `{p}automod [on/off]` - Toggle automated protection\n"
                    f"• `{p}timeout`, `{p}kick`, `{p}ban`, `{p}clear`"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Utility & Tools":
            embed = discord.Embed(
                title="🛠️ Utility & Tools",
                description=(
                    "Useful utilities, lookups, translations, and confessions.\n\n"
                    f"• `{p}translate [lang] [text]` - Translate text between languages\n"
                    f"• `{p}weather [city]` - Check live weather updates\n"
                    f"• `{p}urban [term]` - Search Urban Dictionary\n"
                    f"• `{p}confessionsetup` - Setup anonymous confessions\n"
                    f"• `{p}confess [message]` - Send anonymous confession\n"
                    f"• `{p}afk`, `{p}say`, `{p}reply`, `{p}si`"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Fun & Interaction":
            embed = discord.Embed(
                title="🎉 Fun & Interaction",
                description=(
                    "Interactive commands, coinflips, and giveaways.\n\n"
                    f"• `{p}coinflip` - Flip a coin\n"
                    f"• `{p}hug` / `{p}slap` / `{p}pat` / `{p}kiss` [user]\n"
                    f"• `{p}gcreate [time] [winners] [prize]` - Host giveaway\n"
                    f"• `{p}boosters` - List server booster details"
                ),
                color=discord.Color.blurple()
            )

        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await interaction.response.edit_message(embed=embed)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))


# --- TICKET & CONFESSION VIEWS ---

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")
        
        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
        close_view = TicketCloseView()
        embed = discord.Embed(title="🎫 Support Ticket", description=f"Welcome {interaction.user.mention}!\nSupport team will be with you shortly.\nClick below to close the ticket.", color=discord.Color.blurple())
        embed.set_footer(text="Moonlight Heaven • Ticket System")
        await channel.send(content=interaction.user.mention, embed=embed, view=close_view)
        await interaction.response.send_message(f"✅ Your ticket has been created: {channel.mention}", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing ticket in 5 seconds...")
        await asyncio_sleep_wrapper(5)
        await interaction.channel.delete()

async def asyncio_sleep_wrapper(seconds):
    await asyncio.sleep(seconds)

import asyncio


# --- EVENTS & CHANNELS LOGIC ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else None

    # Automod Check
    if guild_id and guild_automod.get(guild_id, False):
        bad_words = ["discord.gg/", "http://", "https://", "spam"]
        if any(word in message.content.lower() for word in bad_words):
            try:
                await message.delete()
                warning_msg = await message.channel.send(f"⚠️ {message.author.mention}, your message was removed by Automod!")
                await asyncio.sleep(3)
                await warning_msg.delete()
                return
            except:
                pass

    # Confession channel check
    if guild_id and guild_id in guild_confessions and guild_confessions[guild_id].get('channel') == message.channel.id:
        try:
            await message.delete()
            conf_channel = message.channel
            embed = discord.Embed(title="💬 Anonymous Confession", description=f"• **Confession** : `{message.content}`\n• **Status** : Shared securely ✨", color=discord.Color.purple())
            embed.set_footer(text="Moonlight Heaven • Confessions")
            await conf_channel.send(embed=embed)
            return
        except:
            pass

    # Nickname change channel logic
    if guild_id and guild_id in guild_logs and 'nickname' in guild_logs[guild_id]:
        if message.channel.id == guild_logs[guild_id]['nickname']:
            try:
                new_nick = message.content
                await message.author.edit(nick=new_nick)
                embed = discord.Embed(
                    title="✨ Nickname Updated",
                    description=(
                        f"• **User** : {message.author.mention}\n"
                        f"• **New Nickname** : `{new_nick}`\n"
                        f"• **Status** : Successfully Changed 🌟"
                    ),
                    color=discord.Color.blurple()
                )
                embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
                await message.reply(embed=embed)
                return
            except Exception as e:
                embed = discord.Embed(
                    title="⚠️ Nickname Update Failed",
                    description=f"• **Reason** : `{e}`",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
                await message.reply(embed=embed)
                return

    # Birthday channel logic
    if guild_id and guild_id in guild_birthdays and guild_birthdays[guild_id]['channel'] == message.channel.id:
        content = message.content.strip().replace('/', '-')
        parts = content.split('-')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            day, month = parts[0].zfill(2), parts[1].zfill(2)
            formatted_bday = f"{day}-{month}"
            if guild_id not in guild_birthdays:
                guild_birthdays[guild_id] = {'channel': message.channel.id, 'users': {}}
            guild_birthdays[guild_id]['users'][message.author.id] = formatted_bday
            save_data()
            
            embed = discord.Embed(
                title="🎂 Birthday Saved",
                description=f"• **User** : {message.author.mention}\n• **Birthday** : `{formatted_bday}`\n• **Status** : I have remembered your birthday! 🎉",
                color=discord.Color.from_rgb(255, 105, 180)
            )
            embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
            await message.reply(embed=embed)
            return

    author_id = message.author.id
    user_messages[author_id] = user_messages.get(author_id, 0) + 1

    # AFK Logic
    if author_id in afk_users:
        del afk_users[author_id]
        welcome_embed = discord.Embed(
            title="✨ AFK Status Removed",
            description=f"• **Welcome Back** : {message.author.mention}\n• **Status** : AFK mode deactivated.",
            color=discord.Color.blurple()
        )
        welcome_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await message.channel.send(embed=welcome_embed, delete_after=5)

    for user in message.mentions:
        if user.id in afk_users:
            embed = discord.Embed(
                title="💤 User is AFK",
                description=f"• **User** : {user.mention}\n• **Reason** : {afk_users[user.id]}",
                color=discord.Color.blurple()
            )
            embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
            await message.reply(embed=embed)

    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return
    channel = get_log_channel(message.guild.id, 'message')
    if channel:
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            description=f"• **Author** : {message.author.mention}\n• **Channel** : {message.channel.mention}\n• **Content** : {message.content or '[Embed/Attachment]'}",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    if guild_id in guild_autoroles:
        role_id = guild_autoroles[guild_id]
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except:
                pass

    channel = get_log_channel(member.guild.id, 'member')
    if channel:
        embed = discord.Embed(
            title="📥 Member Joined",
            description=f"• **User** : {member.mention}\n• **Name** : `{member.name}`",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = get_log_channel(member.guild.id, 'member')
    if channel:
        embed = discord.Embed(
            title="📤 Member Left",
            description=f"• **User** : {member.mention}\n• **Name** : `{member.name}`",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    user_id = member.id
    guild = member.guild
    channel = get_log_channel(guild.id, 'voice')

    if before.channel is None and after.channel is not None:
        voice_join_timestamps[user_id] = time.time()
        if channel:
            embed = discord.Embed(title="🔊 Voice Join", description=f"• **User** : {member.mention}\n• **Channel** : `{after.channel.name}`", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
            embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
            await channel.send(embed=embed)
    elif before.channel is not None and after.channel is None:
        if user_id in voice_join_timestamps:
            duration = int(time.time() - voice_join_timestamps[user_id])
            user_voice_time[user_id] = user_voice_time.get(user_id, 0) + duration
            del voice_join_timestamps[user_id]
        if channel:
            embed = discord.Embed(title="🔇 Voice Leave", description=f"• **User** : {member.mention}\n• **Channel** : `{before.channel.name}`", color=discord.Color.orange(), timestamp=discord.utils.utcnow())
            embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
            await channel.send(embed=embed)


# --- SETUP & CONFIG COMMANDS ---

@bot.command(name='setup')
@commands.has_permissions(administrator=True)
async def setup(ctx):
    guild = ctx.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }

    try:
        member_ch = await guild.create_text_channel('member-logs', overwrites=overwrites)
        msg_ch = await guild.create_text_channel('message-logs', overwrites=overwrites)
        mod_ch = await guild.create_text_channel('moderation-logs', overwrites=overwrites)
        channel_ch = await guild.create_text_channel('channel-logs', overwrites=overwrites)
        role_ch = await guild.create_text_channel('role-logs', overwrites=overwrites)
        voice_ch = await guild.create_text_channel('voice-logs', overwrites=overwrites)
        logs_ch = await guild.create_text_channel('logs', overwrites=overwrites)
        
        nick_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_nicknames=True)
        }
        nick_ch = await guild.create_text_channel('nickname-change', overwrites=nick_overwrites)

        guild_logs[guild.id] = {
            'member': member_ch.id,
            'message': msg_ch.id,
            'mod': mod_ch.id,
            'channel': channel_ch.id,
            'role': role_ch.id,
            'voice': voice_ch.id,
            'logs': logs_ch.id,
            'nickname': nick_ch.id
        }
        save_data()

        embed = discord.Embed(
            title="⚡ Setup Complete",
            description=(
                f"• **Status** : All log channels created successfully.\n"
                f"• **Channels** : {member_ch.mention}, {msg_ch.mention}, {mod_ch.mention}, {channel_ch.mention}, {role_ch.mention}, {voice_ch.mention}, {logs_ch.mention}, {nick_ch.mention}"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=err_embed)


@bot.command(name='nicknamesetup')
@commands.has_permissions(administrator=True)
async def nicknamesetup(ctx):
    guild = ctx.guild
    nick_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_nicknames=True)
    }
    try:
        nick_ch = await guild.create_text_channel('nickname-change', overwrites=nick_overwrites)
        if guild.id not in guild_logs:
            guild_logs[guild.id] = {}
        guild_logs[guild.id]['nickname'] = nick_ch.id
        save_data()

        embed = discord.Embed(
            title="✨ Nickname Setup Complete",
            description=f"• **Channel Created** : {nick_ch.mention}\n• **Usage** : Type your new nickname here directly.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=err_embed)


@bot.command(name='birthdaysetup')
@commands.has_permissions(administrator=True)
async def birthdaysetup(ctx):
    guild = ctx.guild
    bday_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    try:
        bday_ch = await guild.create_text_channel('birthday-wishes', overwrites=bday_overwrites)
        if guild.id not in guild_birthdays:
            guild_birthdays[guild.id] = {}
        guild_birthdays[guild.id]['channel'] = bday_ch.id
        if 'users' not in guild_birthdays[guild.id]:
            guild_birthdays[guild.id]['users'] = {}
        save_data()

        embed = discord.Embed(
            title="🎂 Birthday Setup Complete",
            description=f"• **Channel Created** : {bday_ch.mention}\n• **Usage** : Type your Date of Birth here (e.g. `15-08` or `15/08`) to save it!",
            color=discord.Color.from_rgb(255, 105, 180)
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=err_embed)


@bot.command(name='autorole')
@commands.has_permissions(administrator=True)
async def autorole(ctx, role: discord.Role):
    guild_autoroles[ctx.guild.id] = role.id
    save_data()
    embed = discord.Embed(title="✅ Autorole Set", description=f"• **Role** : {role.mention}\n• **Status** : Assigned automatically to new members.", color=discord.Color.green())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)


@bot.command(name='ticketsetup')
@commands.has_permissions(administrator=True)
async def ticketsetup(ctx):
    embed = discord.Embed(title="🎫 Support Tickets", description="Click the button below to create a support ticket.", color=discord.Color.blurple())
    embed.set_footer(text="Moonlight Heaven • Ticket System")
    view = TicketView()
    await ctx.send(embed=embed, view=view)


@bot.command(name='confessionsetup')
@commands.has_permissions(administrator=True)
async def confessionsetup(ctx, channel: discord.TextChannel):
    guild_confessions[ctx.guild.id] = {"channel": channel.id}
    save_data()
    embed = discord.Embed(title="💬 Confessions Setup", description=f"• **Channel** : {channel.mention}\n• **Status** : Users can now use `{ctx.prefix}confess [msg]` to confess anonymously.", color=discord.Color.purple())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)


@bot.command(name='confess')
async def confess(ctx, *, message: str):
    try:
        await ctx.message.delete()
    except:
        pass
    guild_id = ctx.guild.id
    if guild_id in guild_confessions and 'channel' in guild_confessions[guild_id]:
        ch_id = guild_confessions[guild_id]['channel']
        ch = ctx.guild.get_channel(ch_id)
        if ch:
            embed = discord.Embed(title="💬 Anonymous Confession", description=f"• **Confession** : `{message}`\n• **Status** : Shared securely ✨", color=discord.Color.purple())
            embed.set_footer(text="Moonlight Heaven • Confessions")
            await ch.send(embed=embed)
            await ctx.author.send("✅ Your confession has been posted successfully!")
            return
    await ctx.reply("⚠️ Confessions channel is not setup in this server yet!", delete_after=5)


@bot.command(name='language')
@commands.has_permissions(administrator=True)
async def set_language(ctx, lang_code: str):
    guild_languages[ctx.guild.id] = lang_code.lower()
    save_data()
    embed = discord.Embed(title="🌐 Language Updated", description=f"• **Language** : `{lang_code.upper()}`\n• **Status** : Server language preference updated.", color=discord.Color.green())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)


@bot.command(name='translate')
async def translate_text(ctx, target_lang: str, *, text: str):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.mymemory.translated.net/get?q={text}&langpair=en|{target_lang}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    translated = res_json['responseData']['translatedText']
                    embed = discord.Embed(title="🌐 Translation", description=f"• **Original** : `{text}`\n• **Translated ({target_lang})** : `{translated}`", color=discord.Color.blue())
                    embed.set_footer(text="Moonlight Heaven • Translation")
                    await ctx.reply(embed=embed)
                    return
    except Exception as e:
        await ctx.reply(f"❌ Translation failed: {e}")


@bot.command(name='backup')
@commands.has_permissions(administrator=True)
async def backup_server(ctx):
    guild = ctx.guild
    try:
        backup_data = {
            "categories": [],
            "channels_without_category": []
        }
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
        
        embed = discord.Embed(title="💾 Backup Successful", description="• **Status** : Server layout backup saved successfully! (Also runs automatically every 6 hours).", color=discord.Color.green())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=err_embed)


@bot.command(name='restore')
@commands.has_permissions(administrator=True)
async def restore_server(ctx):
    guild = ctx.guild
    if guild.id not in server_backups:
        embed = discord.Embed(title="⚠️ No Backup Found", description="• **Status** : Please run `&backup` first or wait for the automatic 6-hour backup.", color=discord.Color.orange())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
        return

    backup = server_backups[guild.id]
    msg = await ctx.reply("🔄 Restoring server categories and channels from backup...")

    try:
        for cat_data in backup["categories"]:
            category = await guild.create_category(cat_data["name"])
            for ch_name in cat_data["channels"]:
                await guild.create_text_channel(ch_name, category=category)
        
        for ch_name in backup["channels_without_category"]:
            await guild.create_text_channel(ch_name)

        await msg.edit(content=None, embed=discord.Embed(title="✅ Restore Complete", description="• **Status** : Server categories and channels have been restored from backup structure!", color=discord.Color.green()).set_footer(text="Moonlight Heaven • Developed by Zeus"))
    except Exception as e:
        await msg.edit(content=None, embed=discord.Embed(title="❌ Restore Failed", description=f"• **Details** : `{e}`", color=discord.Color.red()).set_footer(text="Moonlight Heaven • Developed by Zeus"))


@bot.command(name='setprefix')
@commands.has_permissions(administrator=True)
async def setprefix(ctx, new_prefix: str):
    if len(new_prefix) > 5:
        embed = discord.Embed(title="❌ Error", description="• **Details** : Prefix 5 characters se lamba nahi ho sakta.", color=discord.Color.red())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
        return
        
    guild_prefixes[ctx.guild.id] = new_prefix
    save_data()
    
    embed = discord.Embed(
        title="✨ Prefix Updated",
        description=f"• **New Prefix** : `{new_prefix}`\n• **Status** : Ab aap is server mein `{new_prefix}` use kar sakte hain!",
        color=discord.Color.green()
    )
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)


# --- MENU & SERVERINFO & BOOSTERS COMMANDS ---

@bot.command(name='menu', aliases=['help'])
async def menu(ctx):
    p = guild_prefixes.get(ctx.guild.id, "&") if ctx.guild else "&"
    embed = discord.Embed(
        title="Moonlight Heaven",
        description=(
            "**Command Center**\n"
            "Clean, reliable server management and interactive utility.\n\n"
            "**Quick Start:**\n"
            f"• **View Menu** : Type `{p}menu`\n"
            f"• **Server Info** : Type `{p}si`\n"
            f"• **Check Stats** : Type `{p}m`, `{p}i`, `{p}v`\n"
            "• **Developer** : Created by **Zeus** ✨\n\n"
            "*Select a category below to explore specific commands and permissions.*"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Moonlight Heaven • Command Center")
    view = MenuView(p)
    await ctx.reply(embed=embed, view=view)

@bot.command(name='si')
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 {guild.name}'s Information",
        description=(
            f"• **Server Name** : `{guild.name}`\n"
            f"• **Server ID** : `{guild.id}`\n"
            f"• **Owner** : {guild.owner.mention if guild.owner else 'Unknown'}\n"
            f"• **Total Members** : `{guild.member_count}`\n"
            f"• **Verification Level** : `{str(guild.verification_level).capitalize()}`"
        ),
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)

@bot.command(name='boosters')
async def boosters(ctx):
    guild = ctx.guild
    boosters_list = guild.premium_subscribers
    if not boosters_list:
        await ctx.reply("✨ There are currently no active server boosters.")
        return
    mentions = ", ".join([b.mention for b in boosters_list])
    embed = discord.Embed(title="💎 Server Boosters", description=f"• **Boosters Count** : `{len(boosters_list)}`\n• **Members** : {mentions}", color=discord.Color.from_rgb(255, 114, 215))
    embed.set_footer(text="Moonlight Heaven • Boosters")
    await ctx.reply(embed=embed)


# --- STATS COMMANDS ---

@bot.command(name='m')
async def check_messages(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = user_messages.get(target.id, 0)
    embed = discord.Embed(
        title=f"💬 {target.name}'s Messages",
        description=(
            f"• **User** : {target.mention}\n"
            f"• **Total Messages** : `{count}` messages in this server !\n"
            f"• **Status** : Active & tracked in real-time ✨"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)

@bot.command(name='i')
async def check_invites(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = user_invites.get(target.id, 0)
    embed = discord.Embed(
        title=f"✉️ {target.name}'s Invites",
        description=(
            f"• **User** : {target.mention}\n"
            f"• **Total Invites** : `{count}` invites tracked !\n"
            f"• **Status** : Active & updated live 🚀"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)

@bot.command(name='v')
async def check_voice(ctx, member: discord.Member = None):
    target = member or ctx.author
    secs = user_voice_time.get(target.id, 0)
    if target.id in voice_join_timestamps:
        secs += int(time.time() - voice_join_timestamps[target.id])
    hours, minutes = secs // 3600, (secs % 3600) // 60
    embed = discord.Embed(
        title=f"🎧 {target.name}'s Voice Stats",
        description=(
            f"• **User** : {target.mention}\n"
            f"• **Time Spent** : `{hours}h {minutes}m` in voice channels !\n"
            f"• **Status** : Real-time tracking active 🎙️"
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)


# --- UTILITIES (WEATHER, URBAN, COINFLIP, INTERACTIVE ACTIONS) ---

@bot.command(name='coinflip')
async def coinflip(ctx):
    result = random.choice(["Heads 🪙", "Tails 🪙"])
    embed = discord.Embed(title="🪙 Coin Flip", description=f"• **Result** : **{result}**", color=discord.Color.gold())
    embed.set_footer(text="Moonlight Heaven • Fun")
    await ctx.reply(embed=embed)

@bot.command(name='weather')
async def weather(ctx, *, city: str):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://wttr.in/{city}?format=3"
            async with session.get(url) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    embed = discord.Embed(title=f"🌤️ Weather in {city.capitalize()}", description=f"• **Forecast** : `{text.strip()}`", color=discord.Color.blue())
                    embed.set_footer(text="Moonlight Heaven • Utility")
                    await ctx.reply(embed=embed)
                    return
    except Exception as e:
        await ctx.reply(f"❌ Could not fetch weather: {e}")

@bot.command(name='urban')
async def urban(ctx, *, term: str):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.urbandictionary.com/v0/define?term={term}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data['list']:
                        def_text = data['list'][0]['definition'].replace('[', '').replace(']', '')
                        example = data['list'][0]['example'].replace('[', '').replace(']', '')
                        embed = discord.Embed(title=f"📖 Urban Dictionary: {term}", description=f"• **Definition** : {def_text}\n\n• **Example** : *{example}*", color=discord.Color.blurple())
                        embed.set_footer(text="Moonlight Heaven • Utility")
                        await ctx.reply(embed=embed)
                        return
    except Exception as e:
        await ctx.reply(f"❌ Urban search failed: {e}")

@bot.command(name='hug')
async def hug(ctx, member: discord.Member):
    embed = discord.Embed(title="🤗 Hug!", description=f"{ctx.author.mention} hugs {member.mention} warmly! ❤️", color=discord.Color.from_rgb(255, 105, 180))
    embed.set_footer(text="Moonlight Heaven • Interaction")
    await ctx.reply(embed=embed)

@bot.command(name='slap')
async def slap(ctx, member: discord.Member):
    embed = discord.Embed(title="👋 Slap!", description=f"{ctx.author.mention} slaps {member.mention}!", color=discord.Color.red())
    embed.set_footer(text="Moonlight Heaven • Interaction")
    await ctx.reply(embed=embed)

@bot.command(name='pat')
async def pat(ctx, member: discord.Member):
    embed = discord.Embed(title="✋ Headpat!", description=f"{ctx.author.mention} pats {member.mention} gently. 🌸", color=discord.Color.gold())
    embed.set_footer(text="Moonlight Heaven • Interaction")
    await ctx.reply(embed=embed)

@bot.command(name='kiss')
async def kiss(ctx, member: discord.Member):
    embed = discord.Embed(title="💋 Kiss!", description=f"{ctx.author.mention} kisses {member.mention}! 😘", color=discord.Color.from_rgb(255, 105, 180))
    embed.set_footer(text="Moonlight Heaven • Interaction")
    await ctx.reply(embed=embed)


# --- GIVEAWAY ---

@bot.command(name='gcreate')
@commands.has_permissions(administrator=True)
async def gcreate(ctx, duration: str, winners: int, *, prize: str):
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = duration[-1].lower()
    if unit not in time_units:
        await ctx.reply("❌ Invalid time unit! Use s, m, h, or d.")
        return
    try:
        val = int(duration[:-1])
    except:
        await ctx.reply("❌ Invalid duration format!")
        return
    
    secs = val * time_units[unit]
    embed = discord.Embed(title="🎉 GIVEAWAY 🎉", description=f"• **Prize** : **{prize}**\n• **Winners** : `{winners}`\n• **Hosted by** : {ctx.author.mention}\n\nReact with 🎉 to enter!", color=discord.Color.gold())
    embed.set_footer(text=f"Ends in {duration}")
    msg = await ctx.reply(embed=embed)
    await msg.add_reaction("🎉")

    await asyncio.sleep(secs)
    new_msg = await ctx.channel.fetch_message(msg.id)
    users = []
    for reaction in new_msg.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)
    
    if users:
        chosen = random.sample(users, min(winners, len(users)))
        mentions = ", ".join([u.mention for u in chosen])
        await ctx.send(f"🎊 Congratulations {mentions}! You won **{prize}**!")
    else:
        await ctx.send("😢 Giveaway ended with no valid entries.")


# --- RESET COMMANDS ---

@bot.command(name='rm')
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, target: str):
    if target.lower() == "all":
        user_messages.clear()
        embed = discord.Embed(title="🔄 All Messages Reset", description="• **Status** : Message count for all members has been reset to 0.", color=discord.Color.orange())
    else:
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            user_messages[member.id] = 0
            embed = discord.Embed(title="🔄 Message Reset", description=f"• **User** : {member.mention}\n• **Status** : Count successfully reset to 0.", color=discord.Color.orange())
        except Exception:
            embed = discord.Embed(title="❌ Error", description="• **Details** : Please specify a valid member or type `all`.", color=discord.Color.red())
    
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)

@bot.command(name='ri')
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, member: discord.Member):
    user_invites[member.id] = 0
    embed = discord.Embed(title="🔄 Invite Reset", description=f"• **User** : {member.mention}\n• **Status** : Count successfully reset to 0.", color=discord.Color.orange())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)

@bot.command(name='rv')
@commands.has_permissions(administrator=True)
async def reset_voice(ctx, target: str):
    if target.lower() == "all":
        user_voice_time.clear()
        voice_join_timestamps.clear()
        for vc_channel in ctx.guild.voice_channels:
            for member in vc_channel.members:
                if not member.bot:
                    voice_join_timestamps[member.id] = time.time()
        embed = discord.Embed(title="🔄 All Voice Time Reset", description="• **Status** : Voice time for all members has been reset to 0.", color=discord.Color.orange())
    else:
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            user_voice_time[member.id] = 0
            if member.id in voice_join_timestamps:
                voice_join_timestamps[member.id] = time.time()
            embed = discord.Embed(title="🔄 Voice Time Reset", description=f"• **User** : {member.mention}\n• **Status** : Time successfully reset to 0.", color=discord.Color.orange())
        except Exception:
            embed = discord.Embed(title="❌ Error", description="• **Details** : Please specify a valid member or type `all`.", color=discord.Color.red())
            
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)


# --- MODERATION (WARN, MASSBAN, AUTOMOD TOGGLE, ETC.) ---

@bot.command(name='warn')
@commands.has_permissions(kick_members=True)
async def warn_member(ctx, member: discord.Member, *, reason="No reason provided"):
    guild_id = ctx.guild.id
    if guild_id not in guild_warns:
        guild_warns[guild_id] = {}
    if str(member.id) not in guild_warns[guild_id]:
        guild_warns[guild_id][str(member.id)] = []
    
    guild_warns[guild_id][str(member.id)].append(reason)
    save_data()
    embed = discord.Embed(title="⚠️ Member Warned", description=f"• **User** : {member.mention}\n• **Reason** : `{reason}`\n• **Total Warns** : `{len(guild_warns[guild_id][str(member.id)])}`", color=discord.Color.orange())
    embed.set_footer(text="Moonlight Heaven • Moderation")
    await ctx.reply(embed=embed)

@bot.command(name='warnings')
async def check_warnings(ctx, member: discord.Member):
    guild_id = ctx.guild.id
    warns = guild_warns.get(guild_id, {}).get(str(member.id), [])
    reasons = "\n".join([f"{i+1}. {w}" for i, w in enumerate(warns)]) if warns else "No warnings found."
    embed = discord.Embed(title=f"⚠️ Warnings for {member.name}", description=reasons, color=discord.Color.orange())
    embed.set_footer(text="Moonlight Heaven • Moderation")
    await ctx.reply(embed=embed)

@bot.command(name='clearwarn')
@commands.has_permissions(kick_members=True)
async def clear_warnings(ctx, member: discord.Member):
    guild_id = ctx.guild.id
    if guild_id in guild_warns and str(member.id) in guild_warns[guild_id]:
        guild_warns[guild_id][str(member.id)] = []
        save_data()
    embed = discord.Embed(title="✅ Warnings Cleared", description=f"• **User** : {member.mention}\n• **Status** : All warnings have been wiped.", color=discord.Color.green())
    embed.set_footer(text="Moonlight Heaven • Moderation")
    await ctx.reply(embed=embed)

@bot.command(name='massban')
@commands.has_permissions(ban_members=True)
async def massban(ctx, members: commands.Greedy[discord.Member], *, reason="Massban executed"):
    if not members:
        await ctx.reply("❌ Please mention valid members to massban.")
        return
    banned_count = 0
    for member in members:
        try:
            await member.ban(reason=reason)
            banned_count += 1
        except:
            pass
    embed = discord.Embed(title="🔨 Massban Complete", description=f"• **Banned Members** : `{banned_count}`\n• **Reason** : `{reason}`", color=discord.Color.dark_red())
    embed.set_footer(text="Moonlight Heaven • Moderation")
    await ctx.reply(embed=embed)

@bot.command(name='automod')
@commands.has_permissions(administrator=True)
async def automod(ctx, status: str):
    guild_id = ctx.guild.id
    if status.lower() == "on":
        guild_automod[guild_id] = True
        save_data()
        await ctx.reply("🛡️ Automod has been enabled!")
    elif status.lower() == "off":
        guild_automod[guild_id] = False
        save_data()
        await ctx.reply("🛡️ Automod has been disabled!")
    else:
        await ctx.reply("❌ Please specify `on` or `off`.")


# --- UTILITY & MODERATION COMMANDS ---

@bot.command(name='say')
async def say(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command(name='reply')
async def reply_msg(ctx, message_link: str, *, message: str):
    try:
        parts = message_link.split('/')
        channel = bot.get_channel(int(parts[-2])) or await bot.fetch_channel(int(parts[-2]))
        target_message = await channel.fetch_message(int(parts[-1]))
        await target_message.reply(message)
        await ctx.message.delete()
    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)

@bot.command(name='timeout')
@commands.has_permissions(moderate_members=True)
async def timeout_member(ctx, member: discord.Member, time_str: str, *, reason="No reason provided"):
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = time_str[-1].lower()
    
    if unit not in time_units:
        await ctx.reply("❌ Invalid time format! Use `s`, `m`, `h`, or `d`. Example: `1m`")
        return
    
    try:
        val = int(time_str[:-1])
    except ValueError:
        await ctx.reply("❌ Invalid time value! Example: `1m`, `30m`, `1h`")
        return
    
    total_seconds = val * time_units[unit]
    duration = discord.utils.utcnow() + timedelta(seconds=total_seconds)
    
    try:
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(
            title="⏳ Member Timed Out", 
            description=f"• **User** : {member.mention}\n• **Duration** : `{time_str}`\n• **Reason** : `{reason}`", 
            color=discord.Color.red()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        await ctx.reply(f"❌ Timeout failed: `{e}`. Make sure my role is higher than the target user's role!")

@bot.command(name='afk')
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    embed = discord.Embed(title="💤 AFK Mode Activated", description=f"• **User** : {ctx.author.mention}\n• **Reason** : `{reason}`", color=discord.Color.blue())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    embed = discord.Embed(title="👢 Member Kicked", description=f"• **User** : {member.mention}\n• **Reason** : `{reason or 'None'}`", color=discord.Color.orange())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 Member Banned", description=f"• **User** : {member.mention}\n• **Reason** : `{reason or 'None'}`", color=discord.Color.dark_red())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        embed = discord.Embed(title="🔓 Member Unbanned", description=f"• **User** : {user.mention}", color=discord.Color.green())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="⚠️ Warning", description=f"• **Status** : User not found or invalid ID. ({e})", color=discord.Color.orange())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    embed = discord.Embed(title="🧹 Messages Cleared", description=f"• **Deleted** : `{amount}` messages successfully.", color=discord.Color.green())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed, delete_after=5)


# 4. Run Bot
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("TOKEN"))
