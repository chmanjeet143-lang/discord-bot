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
                    f"• `{p}welcomesetup` - Setup dual welcome channels\n"
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
                    "```ansi\n\u001b[0;31mAdvanced Security & Enforcement Suite\u001b[0m\n```\n"
                    f"• `{p}warn [user] [reason]` - Issue formal member warning\n"
                    f"• `{p}warnings [user]` - Review user warnings\n"
                    f"• `{p}clearwarn [user]` - Clear active warnings\n"
                    f"• `{p}massban [users...]` - Execute mass ban operation\n"
                    f"• `{p}automod [on/off]` - Toggle smart automod protection\n"
                    f"• `{p}timeout`, `{p}kick`, `{p}ban`, `{p}clear`"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Utility & Tools":
            embed = discord.Embed(
                title="🛠️ Utility & Tools",
                description=(
                    "```ansi\n\u001b[0;36mGeneral Utilities & Lookups\u001b[0m\n```\n"
                    f"• `{p}afk`, `{p}say`, `{p}reply`, `{p}si`"
                ),
                color=discord.Color.blurple()
            )

        embed.set_footer(text="Moonlight Heaven • Developed by Zeus", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        await interaction.response.edit_message(embed=embed)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

# --- GIVEAWAY SYSTEM ---
class GiveawayJoinView(discord.ui.View):
    def __init__(self, giveaway_data):
        super().__init__(timeout=None)
        self.giveaway_data = giveaway_data

    @discord.ui.button(label="🎉 Enter Giveaway", style=discord.ButtonStyle.green, custom_id="join_giveaway")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.giveaway_data["entries"]:
            await interaction.response.send_message("❌ You have already entered this giveaway!", ephemeral=True)
        else:
            self.giveaway_data["entries"].append(interaction.user.id)
            await interaction.response.send_message("✅ Success! You have entered the giveaway. Good luck! 🍀", ephemeral=True)

# --- TICKET SYSTEM VIEWS ---
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
        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=(
                f"Welcome {interaction.user.mention}!\n"
                "Our professional support team will be with you shortly.\n\n"
                "• Click the button below whenever you are ready to close this channel."
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Moonlight Heaven • Ticket Management System")
        await channel.send(content=interaction.user.mention, embed=embed, view=close_view)
        await interaction.response.send_message(f"✅ Your ticket channel has been created successfully: {channel.mention}", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing ticket channel in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

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
                warning_msg = await message.channel.send(f"⚠️ {message.author.mention}, your message was removed by Automod security!")
                await asyncio.sleep(3)
                await warning_msg.delete()
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
                        f"• **Status** : Successfully applied 🌟"
                    ),
                    color=discord.Color.blurple()
                )
                embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
                await message.channel.send(embed=embed)
                return
            except Exception as e:
                embed = discord.Embed(
                    title="⚠️ Nickname Update Failed",
                    description=f"• **Reason** : `{e}`",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
                await message.channel.send(embed=embed)
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
                description=f"• **User** : {message.author.mention}\n• **Birthday** : `{formatted_bday}`\n• **Status** : Successfully logged into the database! 🎉",
                color=discord.Color.from_rgb(255, 105, 180)
            )
            embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
            await message.channel.send(embed=embed)
            return

    author_id = message.author.id
    user_messages[author_id] = user_messages.get(author_id, 0) + 1

    # AFK Logic
    if author_id in afk_users:
        del afk_users[author_id]
        welcome_embed = discord.Embed(
            title="✨ AFK Status Removed",
            description=f"• **Welcome Back** : {message.author.mention}\n• **Status** : AFK mode has been automatically deactivated.",
            color=discord.Color.blurple()
        )
        welcome_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await message.channel.send(embed=welcome_embed, delete_after=5)

    for user in message.mentions:
        if user.id in afk_users:
            embed = discord.Embed(
                title="💤 User is Currently AFK",
                description=f"• **User** : {user.mention}\n• **Reason** : {afk_users[user.id]}",
                color=discord.Color.blurple()
            )
            embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
            await message.channel.send(embed=embed)

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

    # Dual-Channel Welcome Message logic
    if guild_id in guild_welcomes:
        data = guild_welcomes[guild_id]
        ch1 = member.guild.get_channel(data.get('channel1'))
        ch2 = member.guild.get_channel(data.get('channel2'))
        
        welcome_embed = discord.Embed(
            title="🎉 Welcome to Moonlight Heaven! ✨",
            description=(
                f"• **Member** : {member.mention}\n"
                f"• **Total Members** : `{member.guild.member_count}`\n"
                f"• **Status** : We are thrilled to have you here! Enjoy your stay. 🚀"
            ),
            color=discord.Color.from_rgb(138, 43, 226),
            timestamp=discord.utils.utcnow()
        )
        if member.avatar:
            welcome_embed.set_thumbnail(url=member.avatar.url)
        welcome_embed.set_footer(text=f"Moonlight Heaven • {member.guild.name}")

        if ch1:
            try:
                await ch1.send(content=member.mention, embed=welcome_embed)
            except:
                pass
        if ch2:
            try:
                await ch2.send(content=member.mention, embed=welcome_embed)
            except:
                pass

    channel = get_log_channel(member.guild.id, 'member')
    if channel:
        embed = discord.Embed(
            title="📥 Member Joined",
            description=f"• **User** : {member.mention}\n• **Username** : `{member.name}`",
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
            description=f"• **User** : {member.mention}\n• **Username** : `{member.name}`",
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
            embed = discord.Embed(title="🔊 Voice Channel Joined", description=f"• **User** : {member.mention}\n• **Channel** : `{after.channel.name}`", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
            embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
            await channel.send(embed=embed)
    elif before.channel is not None and after.channel is None:
        if user_id in voice_join_timestamps:
            duration = int(time.time() - voice_join_timestamps[user_id])
            user_voice_time[user_id] = user_voice_time.get(user_id, 0) + duration
            del voice_join_timestamps[user_id]
        if channel:
            embed = discord.Embed(title="🔇 Voice Channel Left", description=f"• **User** : {member.mention}\n• **Channel** : `{before.channel.name}`", color=discord.Color.orange(), timestamp=discord.utils.utcnow())
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
            'member': member_ch.id, 'message': msg_ch.id, 'mod': mod_ch.id,
            'channel': channel_ch.id, 'role': role_ch.id, 'voice': voice_ch.id,
            'logs': logs_ch.id, 'nickname': nick_ch.id
        }
        save_data()

        embed = discord.Embed(
            title="⚡ Setup Complete",
            description=(
                f"• **Status** : All automated log channels created successfully.\n"
                f"• **Channels** : {member_ch.mention}, {msg_ch.mention}, {mod_ch.mention}, {channel_ch.mention}, {role_ch.mention}, {voice_ch.mention}, {logs_ch.mention}, {nick_ch.mention}"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Setup Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=err_embed)

@bot.command(name='welcomesetup')
@commands.has_permissions(administrator=True)
async def welcomesetup(ctx):
    guild = ctx.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    try:
        welcome_ch1 = await guild.create_text_channel('welcome-main', overwrites=overwrites)
        welcome_ch2 = await guild.create_text_channel('welcome-announcements', overwrites=overwrites)
        
        guild_welcomes[guild.id] = {
            'channel1': welcome_ch1.id,
            'channel2': welcome_ch2.id
        }
        save_data()

        embed = discord.Embed(
            title="✨ Welcome Setup Complete",
            description=(
                f"• **Status** : Dual welcome channels created successfully.\n"
                f"• **Channels** : {welcome_ch1.mention} and {welcome_ch2.mention}"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Setup Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=err_embed)

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
            description=f"• **Channel Created** : {nick_ch.mention}\n• **Usage** : Send your preferred new nickname directly in that channel.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=err_embed)

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
        await ctx.send(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=err_embed)

# --- GIVEAWAY COMMAND ---
@bot.command(name='giveaway')
@commands.has_permissions(manage_guild=True)
async def giveaway(ctx, duration: str, winners_count: int, *, prize: str):
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = duration[-1].lower()
    
    if unit not in time_units:
        await ctx.send("❌ Invalid duration format! Use `s`, `m`, `h`, or `d`. Example: `10m`")
        return
    try:
        val = int(duration[:-1])
    except ValueError:
        await ctx.send("❌ Invalid duration value! Example: `10m`, `1h`, `2d`")
        return
    
    total_seconds = val * time_units[unit]
    end_time = datetime.utcnow() + timedelta(seconds=total_seconds)
    
    giveaway_data = {"entries": []}
    view = GiveawayJoinView(giveaway_data)
    
    embed = discord.Embed(
        title="🎉 **GIVEAWAY TIME!** 🎉",
        description=(
            f"```ansi\n\u001b[0;32m{prize}\u001b[0m\n```\n"
            f"• **Prize** : {prize}\n"
            f"• **Winners** : `{winners_count}`\n"
            f"• **Hosted By** : {ctx.author.mention}\n"
            f"• **Ends At** : {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            "• **Click the button below to participate!**"
        ),
        color=discord.Color.from_rgb(255, 215, 0),
        timestamp=end_time
    )
    embed.set_footer(text="Moonlight Heaven • Giveaway System")
    
    msg = await ctx.send(embed=embed, view=view)
    await ctx.message.delete()
    
    await asyncio.sleep(total_seconds)
    
    for child in view.children:
        child.disabled = True
    
    entries = giveaway_data["entries"]
    if not entries:
        ended_embed = discord.Embed(
            title="🎉 **GIVEAWAY ENDED** 🎉",
            description=f"• **Prize** : {prize}\n• **Result** : No valid entries recorded. Nobody won!",
            color=discord.Color.red()
        )
        ended_embed.set_footer(text="Moonlight Heaven • Giveaway System")
        await msg.edit(embed=ended_embed, view=view)
        return
    
    actual_winners_count = min(winners_count, len(entries))
    winners = random.sample(entries, actual_winners_count)
    winner_mentions = ", ".join([f"<@{w_id}>" for w_id in winners])
    
    ended_embed = discord.Embed(
        title="🎉 **GIVEAWAY ENDED** 🎉",
        description=(
            f"• **Prize** : {prize}\n"
            f"• **Winner(s)** : {winner_mentions}\n"
            f"• **Total Entries** : `{len(entries)}`"
        ),
        color=discord.Color.green()
    )
    ended_embed.set_footer(text="Moonlight Heaven • Giveaway System")
    await msg.edit(embed=ended_embed, view=view)
    await ctx.send(f"🎊 Congratulations {winner_mentions}! You won **{prize}**!")

@bot.command(name='autorole')
@commands.has_permissions(administrator=True)
async def autorole(ctx, role: discord.Role):
    guild_autoroles[ctx.guild.id] = role.id
    save_data()
    embed = discord.Embed(title="✅ Autorole Updated", description=f"• **Role** : {role.mention}\n• **Status** : Assigned automatically to all incoming members.", color=discord.Color.green())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed)

@bot.command(name='ticketsetup')
@commands.has_permissions(administrator=True)
async def ticketsetup(ctx):
    embed = discord.Embed(
        title="🎫 Support Tickets",
        description="• Click the button below to open a private support ticket with our team.",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Moonlight Heaven • Ticket System")
    view = TicketView()
    await ctx.send(embed=embed, view=view)

@bot.command(name='language')
@commands.has_permissions(administrator=True)
async def set_language(ctx, lang_code: str):
    guild_languages[ctx.guild.id] = lang_code.lower()
    save_data()
    embed = discord.Embed(title="🌐 Language Updated", description=f"• **Language** : `{lang_code.upper()}`\n• **Status** : Server language preferences updated.", color=discord.Color.green())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed)

@bot.command(name='backup')
@commands.has_permissions(administrator=True)
async def backup_server(ctx):
    guild = ctx.guild
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
        
        embed = discord.Embed(title="💾 Backup Successful", description="• **Status** : Server layout backup saved successfully! (Also runs automatically every 6 hours).", color=discord.Color.green())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=err_embed)

@bot.command(name='restore')
@commands.has_permissions(administrator=True)
async def restore_server(ctx):
    guild = ctx.guild
    if guild.id not in server_backups:
        embed = discord.Embed(title="⚠️ No Backup Found", description="• **Status** : Please run `&backup` first or wait for the automatic 6-hour backup.", color=discord.Color.orange())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=embed)
        return

    backup = server_backups[guild.id]
    msg = await ctx.send("🔄 Restoring server categories and channels from backup...")

    try:
        for cat_data in backup["categories"]:
            category = await guild.create_category(cat_data["name"])
            for ch_name in cat_data["channels"]:
                await guild.create_text_channel(ch_name, category=category)
        for ch_name in backup["channels_without_category"]:
            await guild.create_text_channel(ch_name)

        await msg.edit(content=None, embed=discord.Embed(title="✅ Restore Complete", description="• **Status** : Server categories and channels restored successfully!", color=discord.Color.green()).set_footer(text="Moonlight Heaven • Developed by Zeus"))
    except Exception as e:
        await msg.edit(content=None, embed=discord.Embed(title="❌ Restore Failed", description=f"• **Details** : `{e}`", color=discord.Color.red()).set_footer(text="Moonlight Heaven • Developed by Zeus"))

@bot.command(name='setprefix')
@commands.has_permissions(administrator=True)
async def setprefix(ctx, new_prefix: str):
    if len(new_prefix) > 5:
        embed = discord.Embed(title="❌ Error", description="• **Details** : Prefix cannot be longer than 5 characters.", color=discord.Color.red())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=embed)
        return
        
    guild_prefixes[ctx.guild.id] = new_prefix
    save_data()
    
    embed = discord.Embed(
        title="✨ Prefix Updated",
        description=f"• **New Prefix** : `{new_prefix}`\n• **Status** : You can now use `{new_prefix}` commands in this server!",
        color=discord.Color.green()
    )
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed)

# --- MENU & SERVERINFO COMMANDS ---
@bot.command(name='menu', aliases=['help'])
async def menu(ctx):
    p = guild_prefixes.get(ctx.guild.id, "&") if ctx.guild else "&"
    embed = discord.Embed(
        title="✨ Moonlight Heaven • Command Center",
        description=(
            "```ansi\n\u001b[0;34mAdvanced Server Management & Utility\u001b[0m\n```\n"
            "• **Quick Start Guide**\n"
            f"  ‣ View Menu : `{p}menu`\n"
            f"  ‣ Server Info : `{p}si`\n"
            f"  ‣ Check Stats : `{p}m`, `{p}i`, `{p}v`\n\n"
            "• **Developer** : Created by **Zeus** 🚀\n\n"
            "*Select a category below to explore commands and toolsets.*"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Moonlight Heaven • Command Center", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
    view = MenuView(p)
    await ctx.send(embed=embed, view=view)

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
    await ctx.send(embed=embed)

# --- STATS COMMANDS ---
@bot.command(name='m')
async def check_messages(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = user_messages.get(target.id, 0)
    embed = discord.Embed(
        title=f"💬 {target.name}'s Messages",
        description=(
            f"• **User** : {target.mention}\n"
            f"• **Total Messages** : `{count}` messages logged !\n"
            f"• **Status** : Active & tracked in real-time ✨"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed)

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
    await ctx.send(embed=embed)

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
            f"• **Status** : Real-time voice tracking active 🎙️"
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed)

# --- RESET COMMANDS ---
@bot.command(name='rm')
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, target: str):
    if target.lower() == "all":
        user_messages.clear()
        embed = discord.Embed(title="🔄 All Messages Reset", description="• **Status** : Message count for all members reset to 0.", color=discord.Color.orange())
    else:
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            user_messages[member.id] = 0
            embed = discord.Embed(title="🔄 Message Reset", description=f"• **User** : {member.mention}\n• **Status** : Count successfully reset to 0.", color=discord.Color.orange())
        except Exception:
            embed = discord.Embed(title="❌ Error", description="• **Details** : Please specify a valid member or type `all`.", color=discord.Color.red())
    
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed)

@bot.command(name='ri')
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, member: discord.Member):
    user_invites[member.id] = 0
    embed = discord.Embed(title="🔄 Invite Reset", description=f"• **User** : {member.mention}\n• **Status** : Count successfully reset to 0.", color=discord.Color.orange())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed)

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
        embed = discord.Embed(title="🔄 All Voice Time Reset", description="• **Status** : Voice time for all members reset to 0.", color=discord.Color.orange())
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
    await ctx.send(embed=embed)

# --- MODERATION COMMANDS ---
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
    embed = discord.Embed(title="⚠️ Member Warned", description=f"• **User** : {member.mention}\n• **Reason** : `{reason}`\n• **Total Warnings** : `{len(guild_warns[guild_id][str(member.id)])}`", color=discord.Color.orange())
    embed.set_footer(text="Moonlight Heaven • Moderation")
    await ctx.send(embed=embed)

@bot.command(name='warnings')
async def check_warnings(ctx, member: discord.Member):
    guild_id = ctx.guild.id
    warns = guild_warns.get(guild_id, {}).get(str(member.id), [])
    reasons = "\n".join([f"{i+1}. {w}" for i, w in enumerate(warns)]) if warns else "No warnings found."
    embed = discord.Embed(title=f"⚠️ Warnings for {member.name}", description=reasons, color=discord.Color.orange())
    embed.set_footer(text="Moonlight Heaven • Moderation")
    await ctx.send(embed=embed)

@bot.command(name='clearwarn')
@commands.has_permissions(kick_members=True)
async def clear_warnings(ctx, member: discord.Member):
    guild_id = ctx.guild.id
    if guild_id in guild_warns and str(member.id) in guild_warns[guild_id]:
        guild_warns[guild_id][str(member.id)] = []
        save_data()
    embed = discord.Embed(title="✅ Warnings Cleared", description=f"• **User** : {member.mention}\n• **Status** : All warnings have been wiped.", color=discord.Color.green())
    embed.set_footer(text="Moonlight Heaven • Moderation")
    await ctx.send(embed=embed)

@bot.command(name='massban')
@commands.has_permissions(ban_members=True)
async def massban(ctx, members: commands.Greedy[discord.Member], *, reason="Massban executed"):
    if not members:
        await ctx.send("❌ Please mention valid members to massban.")
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
    await ctx.send(embed=embed)

@bot.command(name='automod')
@commands.has_permissions(administrator=True)
async def automod(ctx, status: str):
    guild_id = ctx.guild.id
    if status.lower() == "on":
        guild_automod[guild_id] = True
        save_data()
        await ctx.send("🛡️ Automod filter has been enabled!")
    elif status.lower() == "off":
        guild_automod[guild_id] = False
        save_data()
        await ctx.send("🛡️ Automod filter has been disabled!")
    else:
        await ctx.send("❌ Please specify `on` or `off`.")

# --- UTILITY & MODERATION TOOLS ---
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
        await ctx.send(embed=embed)

@bot.command(name='timeout')
@commands.has_permissions(moderate_members=True)
async def timeout_member(ctx, member: discord.Member, time_str: str, *, reason="No reason provided"):
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = time_str[-1].lower()
    
    if unit not in time_units:
        await ctx.send("❌ Invalid time format! Use `s`, `m`, `h`, or `d`. Example: `1m`")
        return
    try:
        val = int(time_str[:-1])
    except ValueError:
        await ctx.send("❌ Invalid time value! Example: `1m`, `30m`, `1h`")
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
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Timeout failed: `{e}`. Ensure my role is higher than the target member's role!")

@bot.command(name='afk')
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    embed = discord.Embed(title="💤 AFK Mode Activated", description=f"• **User** : {ctx.author.mention}\n• **Reason** : `{reason}`", color=discord.Color.blue())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed)

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    embed = discord.Embed(title="👢 Member Kicked", description=f"• **User** : {member.mention}\n• **Reason** : `{reason or 'None'}`", color=discord.Color.orange())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 Member Banned", description=f"• **User** : {member.mention}\n• **Reason** : `{reason or 'None'}`", color=discord.Color.dark_red())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=embed)

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        embed = discord.Embed(title="🔓 Member Unbanned", description=f"• **User** : {user.mention}", color=discord.Color.green())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="⚠️ Warning", description=f"• **Status** : User not found or invalid ID. ({e})", color=discord.Color.orange())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.send(embed=embed)

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
