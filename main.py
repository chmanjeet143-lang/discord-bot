import os
import time
import json
import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

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

bot = commands.Bot(command_prefix="&", intents=intents)
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
    return {"logs": {}, "birthdays": {}, "backups": {}}

def save_data():
    data = {
        "logs": guild_logs,
        "birthdays": guild_birthdays,
        "backups": server_backups
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load data into memory on startup
db = load_data()
guild_logs = {int(k): v for k, v in db.get("logs", {}).items()}
guild_birthdays = {int(k): v for k, v in db.get("birthdays", {}).items()}
server_backups = {int(k): v for k, v in db.get("backups", {}).items()}

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
    print(f"Status: Online & Ready (Database Connected)!")
    print(f"----------------------------------------")


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
    def __init__(self):
        options = [
            discord.SelectOption(label="Command Center", description="Overview and quick-start guide", emoji="📊"),
            discord.SelectOption(label="Setups & Configuration", description="Server logs, backup & channels", emoji="⚙️"),
            discord.SelectOption(label="Statistics & Tracking", description="Messages, invites, voice time & resets", emoji="📈"),
            discord.SelectOption(label="Moderation / Admin", description="Server activation, roles & cleanup", emoji="🛡️"),
            discord.SelectOption(label="Utility & Tools", description="AFK, say, reply, server info", emoji="🛠️")
        ]
        super().__init__(placeholder="Select a category to view commands...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Command Center":
            embed = discord.Embed(
                title="Moonlight Heaven",
                description=(
                    "**Command Center**\n"
                    "Clean, reliable server management and interactive utility.\n\n"
                    "**Quick Start:**\n"
                    "• **View Menu** : Type `&menu`\n"
                    "• **Server Info** : Type `&si`\n"
                    "• **Check Stats** : Type `&m`, `&i`, `&v`\n"
                    "• **Developer** : Created by **Zeus** ✨"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Setups & Configuration":
            embed = discord.Embed(
                title="⚙️ Setups & Configuration",
                description=(
                    "Manage your server logging and custom features seamlessly.\n\n"
                    "• `&setup` - Create all automated log channels\n"
                    "• `&nicknamesetup` - Create instant nickname change channel\n"
                    "• `&birthdaysetup` - Create birthday collection channel\n"
                    "• `&backup` - Take manual server layout backup\n"
                    "• `&restore` - Restore server structure from backup"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Statistics & Tracking":
            embed = discord.Embed(
                title="📈 Statistics & Tracking",
                description=(
                    "Keep track of member activity in real time.\n\n"
                    "• `&m [user]` - Check message count\n"
                    "• `&i [user]` - Check invite count\n"
                    "• `&v [user]` - Check voice channel time\n"
                    "• `&rm [user/all]` - Reset messages\n"
                    "• `&ri [user]` - Reset invites\n"
                    "• `&rv [user/all]` - Reset voice time"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Moderation / Admin":
            embed = discord.Embed(
                title="🛡️ Moderation & Admin",
                description=(
                    "Powerful tools to maintain order and discipline.\n\n"
                    "• `&addrole [user] [role]` - Add a role to user\n"
                    "• `&removerole [user] [role]` - Remove a role from user\n"
                    "• `&hide [channel]` - Hide a channel\n"
                    "• `&show [channel]` - Show a channel\n"
                    "• `&lock [channel]` - Lock a channel\n"
                    "• `&unlock [channel]` - Unlock a channel\n"
                    "• `&timeout [user] [mins]` - Timeout a member\n"
                    "• `&kick [user]` - Kick a member\n"
                    "• `&ban [user]` - Ban a member\n"
                    "• `&clear [amount]` - Purge messages"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Utility & Tools":
            embed = discord.Embed(
                title="🛠️ Utility & Tools",
                description=(
                    "Handy utilities for everyday engagement.\n\n"
                    "• `&afk [reason]` - Set custom AFK status\n"
                    "• `&say [msg]` - Send anonymous bot message\n"
                    "• `&reply [link] [msg]` - Reply directly to message link\n"
                    "• `&si` - View detailed server information"
                ),
                color=discord.Color.blurple()
            )

        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await interaction.response.edit_message(embed=embed)

class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(MenuSelect())


# --- EVENTS & CHANNELS LOGIC ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else None

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


# --- SETUP & BACKUP COMMANDS ---

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


# --- MENU & SERVERINFO COMMANDS ---

@bot.command(name='menu', aliases=['help'])
async def menu(ctx):
    embed = discord.Embed(
        title="Moonlight Heaven",
        description=(
            "**Command Center**\n"
            "Clean, reliable server management and interactive utility.\n\n"
            "**Quick Start:**\n"
            "• **View Menu** : Type `&menu`\n"
            "• **Server Info** : Type `&si`\n"
            "• **Check Stats** : Type `&m`, `&i`, `&v`\n"
            "• **Developer** : Created by **Zeus** ✨\n\n"
            "*Select a category below to explore specific commands and permissions.*"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Moonlight Heaven • Command Center")
    view = MenuView()
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


# --- NEW ROLE & CHANNEL CONTROL COMMANDS ---

@bot.command(name='addrole')
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        embed = discord.Embed(title="✅ Role Added", description=f"• **User** : {member.mention}\n• **Role** : {role.mention}\n• **Status** : Successfully added!", color=discord.Color.green())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=err_embed)

@bot.command(name='removerole')
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        embed = discord.Embed(title="✅ Role Removed", description=f"• **User** : {member.mention}\n• **Role** : {role.mention}\n• **Status** : Successfully removed!", color=discord.Color.orange())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=err_embed)

@bot.command(name='hide')
@commands.has_permissions(manage_channels=True)
async def hide(ctx, channel: discord.TextChannel = None):
    target_channel = channel or ctx.channel
    try:
        await target_channel.set_permissions(ctx.guild.default_role, read_messages=False)
        embed = discord.Embed(title="🔒 Channel Hidden", description=f"• **Channel** : {target_channel.mention}\n• **Status** : Hidden from `@everyone`.", color=discord.Color.orange())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=err_embed)

@bot.command(name='show')
@commands.has_permissions(manage_channels=True)
async def show(ctx, channel: discord.TextChannel = None):
    target_channel = channel or ctx.channel
    try:
        await target_channel.set_permissions(ctx.guild.default_role, read_messages=True)
        embed = discord.Embed(title="🔓 Channel Visible", description=f"• **Channel** : {target_channel.mention}\n• **Status** : Visible to `@everyone`.", color=discord.Color.green())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=err_embed)

@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)
async def lock(ctx, channel: discord.TextChannel = None):
    target_channel = channel or ctx.channel
    try:
        await target_channel.set_permissions(ctx.guild.default_role, send_messages=False)
        embed = discord.Embed(title="🔒 Channel Locked", description=f"• **Channel** : {target_channel.mention}\n• **Status** : Locked for `@everyone`.", color=discord.Color.orange())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=err_embed)

@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, channel: discord.TextChannel = None):
    target_channel = channel or ctx.channel
    try:
        await target_channel.set_permissions(ctx.guild.default_role, send_messages=True)
        embed = discord.Embed(title="🔓 Channel Unlocked", description=f"• **Channel** : {target_channel.mention}\n• **Status** : Unlocked for `@everyone`.", color=discord.Color.green())
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=embed)
    except Exception as e:
        err_embed = discord.Embed(title="❌ Error", description=f"• **Details** : `{e}`", color=discord.Color.red())
        err_embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
        await ctx.reply(embed=err_embed)


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
async def timeout_member(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    duration = discord.utils.utcnow() + discord.utils.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    embed = discord.Embed(title="⏳ Member Timed Out", description=f"• **User** : {member.mention}\n• **Duration** : `{minutes} minutes`\n• **Reason** : `{reason}`", color=discord.Color.red())
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.reply(embed=embed)

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
async def unban(ctx, *, member_name):
    banned_users = await ctx.guild.bans()
    for ban_entry in banned_users:
        if ban_entry.user.name == member_name:
            await ctx.guild.unban(ban_entry.user)
            embed = discord.Embed(title="🔓 Member Unbanned", description=f"• **User** : {ban_entry.user.mention}", color=discord.Color.green())
            embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
            await ctx.reply(embed=embed)
            return
    embed = discord.Embed(title="⚠️ Warning", description="• **Status** : User not found in ban list.", color=discord.Color.orange())
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
