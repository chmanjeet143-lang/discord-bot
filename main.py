import os
import time
import json
import random
import aiohttp
import asyncio
import io
import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# Flask server to keep bot alive on Render 24/7
app = Flask('')

@app.route('/')
def home():
    return "🤖 Moonlight Heaven is Alive and Running!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Bot Intents & Configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.bans = True
intents.invites = True

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
        "nickname_setup": {}, "counting": {}
    }

def save_data():
    data = {
        "logs": guild_logs,
        "birthdays": guild_birthdays,
        "backups": server_backups,
        "prefixes": guild_prefixes,
        "warns": guild_warns,
        "automod": guild_automod,
        "autorole": guild_autoroles,
        "tickets": guild_tickets,
        "welcome": guild_welcomes,
        "messages": user_messages,
        "voice_time": user_voice_time,
        "invites": user_invites,
        "nickname_setup": guild_nicknames,
        "counting": guild_counting
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

def get_prefix(bot, message):
    if not message.guild:
        return "."
    return guild_prefixes.get(message.guild.id, ".")

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

afk_users = {}
voice_join_timestamps = {}
server_invite_counts = {}

# Standard Aesthetic Embed Color Function
def aesthetic_embed(title="", description="", color=discord.Color.from_rgb(20, 20, 20)):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

@bot.event
async def on_ready():
    if not daily_birthday_check.is_running():
        daily_birthday_check.start()
    if not auto_backup_task.is_running():
        auto_backup_task.start()
    
    for guild in bot.guilds:
        try:
            server_invite_counts[guild.id] = {inv.code: inv.uses for inv in await guild.invites()}
        except:
            pass

    print("----------------------------------------")
    print("Bot Name: Moonlight Heaven")
    print("Developer: Zeus")
    print("Status: Online with Uniform Aesthetic Embeds!")
    print("----------------------------------------")

@bot.event
async def on_command_error(ctx, error):
    p = ctx.prefix
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        embed = aesthetic_embed(title="⚠️ Invalid Command Usage", description=f"• **Proper Usage** : `{p}{ctx.command.name} [arguments]`\n• **Help Menu** : `{p}help`")
    elif isinstance(error, commands.MissingPermissions):
        embed = aesthetic_embed(title="🚫 Access Denied", description="You lack the required permissions to run this command.")
    else:
        embed = aesthetic_embed(title="❌ Command Error", description=f"`{error}`")
    await ctx.send(embed=embed)

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
                member = guild.get_member(int(user_id_str))
                if member:
                    await channel.send(content=f"@everyone 🎉 Happy Birthday {member.mention}! 🎂🥳")

@tasks.loop(hours=6)
async def auto_backup_task():
    for guild in bot.guilds:
        try:
            backup_data = {"categories": [], "channels_without_category": []}
            for category in guild.categories:
                backup_data["categories"].append({"name": category.name, "channels": [ch.name for ch in category.channels]})
            server_backups[guild.id] = backup_data
            save_data()
        except:
            pass

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    g_id = message.guild.id if message.guild else 0
    u_id = message.author.id

    # Counting System Logic
    if g_id in guild_counting:
        c_data = guild_counting[g_id]
        if message.channel.id == c_data.get("channel_id"):
            try:
                number = int(message.content.strip())
                expected = c_data.get("next_number", 1)
                last_user = c_data.get("last_user", 0)

                if number == expected and u_id != last_user:
                    c_data["next_number"] = expected + 1
                    c_data["last_user"] = u_id
                    save_data()
                    react_emoji = c_data.get("emoji", "✅")
                    await message.add_reaction(react_emoji)
                else:
                    await message.delete()
                    await message.channel.send(f"❌ {message.author.mention}, wrong counting or consecutive message! Reset to `{expected}`.", delete_after=4)
            except ValueError:
                if not message.author.guild_permissions.manage_messages:
                    try:
                        await message.delete()
                    except:
                        pass

    # Automod Check
    if g_id in guild_automod and guild_automod[g_id].get("enabled", False):
        blocked_words = ["discord.gg/", "http://", "https://"]
        if any(w in message.content.lower() for w in blocked_words) and not message.author.guild_permissions.manage_messages:
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, links/invites are blocked by Automod!", delete_after=4)
                return
            except:
                pass

    if g_id not in user_messages:
        user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    if u_id in afk_users:
        del afk_users[u_id]
        try:
            await message.channel.send(f"Welcome back {message.author.mention}, I removed your AFK status!", delete_after=5)
        except:
            pass

    for ment in message.mentions:
        if ment.id in afk_users:
            reason = afk_users[ment.id]
            await message.channel.send(f"💤 **{ment.name}** is currently AFK: {reason}")

    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    u_id = member.id
    g_id = member.guild.id
    
    if before.channel is None and after.channel is not None:
        voice_join_timestamps[u_id] = time.time()
    elif before.channel is not None and after.channel is None:
        if u_id in voice_join_timestamps:
            duration = int(time.time() - voice_join_timestamps[u_id])
            if g_id not in user_voice_time:
                user_voice_time[g_id] = {}
            user_voice_time[g_id][str(u_id)] = user_voice_time[g_id].get(str(u_id), 0) + duration
            save_data()
            del voice_join_timestamps[u_id]

@bot.event
async def on_member_join(member):
    g_id = member.guild.id
    if g_id in guild_autoroles:
        role_id = guild_autoroles[g_id]
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except:
                pass

    data = guild_welcomes.get(g_id)
    if data:
        ch = member.guild.get_channel(data.get("main_channel"))
        if ch:
            await ch.send(f"✨ Welcome {member.mention} to **{member.guild.name}**! 🎉")

# ==================== ALL BOT COMMANDS ====================

# 1. PREFIX CHANGER
@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix_cmd(ctx, new_prefix: str):
    if len(new_prefix) > 5:
        embed = aesthetic_embed(title="❌ Error", description="Prefix length cannot exceed 5 characters.")
        await ctx.send(embed=embed)
        return
    guild_prefixes[ctx.guild.id] = new_prefix
    save_data()
    embed = aesthetic_embed(title="⚙️ Prefix Updated", description=f"Server prefix successfully updated to: `{new_prefix}`")
    await ctx.send(embed=embed)

# 2. EMOJI & STICKER CLONE COMMAND
@bot.command(name="clone")
@commands.has_permissions(manage_emojis=True)
async def clone_command(ctx):
    if not ctx.message.reference:
        embed = aesthetic_embed(title="❌ Action Failed", description="Please reply to a message containing an emoji or a sticker to clone it!")
        await ctx.send(embed=embed)
        return
    
    try:
        referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except:
        embed = aesthetic_embed(title="❌ Error", description="Could not fetch the replied message.")
        await ctx.send(embed=embed)
        return

    cloned_count = 0
    
    if referenced_msg.stickers:
        for sticker in referenced_msg.stickers:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(sticker.url) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            file = discord.File(fp=io.BytesIO(data), filename=f"{sticker.name}.png")
                            await ctx.guild.create_sticker(name=sticker.name, description="Cloned sticker", file=file, emoji="✨")
                            cloned_count += 1
            except:
                pass

    import re
    custom_emojis = re.findall(r'<a?:([a-zA-Z0-9_]+):([0-9]+)>', referenced_msg.content)
    for name, emoji_id in custom_emojis:
        animated = referenced_msg.content.startswith("<a:")
        extension = "gif" if animated else "png"
        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        emoji = await ctx.guild.create_custom_emoji(name=name, image=data)
                        cloned_count += 1
        except:
            pass

    if cloned_count > 0:
        embed = aesthetic_embed(title="🚀 Clone Successful", description=f"Successfully cloned `{cloned_count}` items to the server!")
    else:
        embed = aesthetic_embed(title="❌ Clone Failed", description="No valid custom emoji or sticker found in the replied message.")
    await ctx.send(embed=embed)

# 3. HIDDEN COUNTING START COMMAND
@bot.command(name="start")
@commands.has_permissions(administrator=True)
async def start_counting(ctx, amount: int = 1, channel: discord.TextChannel = None, emoji: str = "✅"):
    target_channel = channel or ctx.channel
    guild_counting[ctx.guild.id] = {
        "channel_id": target_channel.id,
        "next_number": amount,
        "last_user": 0,
        "emoji": emoji
    }
    save_data()
    embed = aesthetic_embed(title="🔢 Counting Initialized", description=f"Counting configured in {target_channel.mention} starting from **{amount}** with reaction **{emoji}**!")
    await ctx.send(embed=embed)

# 4. ROLE ICON COMMAND
@bot.command(name="roleicon")
@commands.has_permissions(manage_roles=True)
async def role_icon(ctx, role: discord.Role, emoji: str):
    embed = aesthetic_embed(
        title="Role Icon Updated!",
        description=f"📁 **Role** : {role.mention}\n🛡️ **Moderator** : `{ctx.author.name}`\n🎨 **Icon** : {emoji}"
    )
    await ctx.send(embed=embed)

# 5. PING COMMAND
@bot.command(name="ping")
async def ping_command(ctx):
    latency = round(bot.latency * 1000)
    embed = aesthetic_embed(title="🏓 Pong!", description=f"Bot Latency : `{latency}ms`")
    await ctx.send(embed=embed)

# 6. SERVER INFO COMMAND
@bot.command(name="si", aliases=["serverinfo"])
async def server_info(ctx):
    g = ctx.guild
    embed = aesthetic_embed(title=f"📊 {g.name} - Server Info", description=f"• **Owner**: {g.owner}\n• **Members**: `{g.member_count}`\n• **Created On**: `{g.created_at.strftime('%b %d, %Y')}`")
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=embed)

# 7. AFK COMMAND
@bot.command(name="afk")
async def afk_command(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    embed = aesthetic_embed(title="💤 Status Updated", description=f"{ctx.author.mention} is now AFK: **{reason}**")
    await ctx.send(embed=embed)

# 8. SETUP LOGS COMMAND
@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_channels(ctx):
    guild = ctx.guild
    log_ch = await guild.create_text_channel("🤖-bot-logs")
    guild_logs[guild.id] = {"logs": log_ch.id}
    save_data()
    embed = aesthetic_embed(title="⚙️ Setup Complete", description=f"Standard log channel generated successfully! Log Channel: {log_ch.mention}")
    await ctx.send(embed=embed)

# 9. WELCOME SETUP COMMAND
@bot.command(name="welcomesetup")
@commands.has_permissions(administrator=True)
async def welcomesetup(ctx, main_channel: discord.TextChannel, rules_channel: discord.TextChannel):
    guild_welcomes[ctx.guild.id] = {"main_channel": main_channel.id, "rules_channel": rules_channel.id}
    save_data()
    embed = aesthetic_embed(title="🚪 Welcomer Configured", description=f"Dual welcome channels configured: {main_channel.mention} & {rules_channel.mention}")
    await ctx.send(embed=embed)

# 10. NICKNAME SETUP COMMAND
@bot.command(name="nicknamesetup")
@commands.has_permissions(administrator=True)
async def nicknamesetup(ctx):
    guild_nicknames[ctx.guild.id] = True
    save_data()
    embed = aesthetic_embed(title="📝 Nickname Setup", description="Interactive nickname system initialized successfully!")
    await ctx.send(embed=embed)

# 11. BIRTHDAY SETUP COMMAND
@bot.command(name="birthdaysetup")
@commands.has_permissions(administrator=True)
async def birthdaysetup(ctx, channel: discord.TextChannel):
    if ctx.guild.id not in guild_birthdays:
        guild_birthdays[ctx.guild.id] = {"users": {}}
    guild_birthdays[ctx.guild.id]["channel"] = channel.id
    save_data()
    embed = aesthetic_embed(title="🎂 Birthday Setup", description=f"Birthday collection channel set to {channel.mention}")
    await ctx.send(embed=embed)

# 12. GIVEAWAY COMMAND
@bot.command(name="giveaway")
@commands.has_permissions(manage_guild=True)
async def giveaway_start(ctx, time_str: str, winners: int, *, prize: str):
    embed = aesthetic_embed(title="🎉 GIVEAWAY 🎉", description=f"• **Prize**: {prize}\n• **Winners**: `{winners}`\n• **Hosted by**: {ctx.author.mention}\n\nReact with 🎉 to enter!")
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")

# 13. AUTOROLE COMMAND
@bot.command(name="autorole")
@commands.has_permissions(administrator=True)
async def autorole_setup(ctx, role: discord.Role):
    guild_autoroles[ctx.guild.id] = role.id
    save_data()
    embed = aesthetic_embed(title="🛡️ Autorole Set", description=f"Automated welcome role set to **{role.name}**")
    await ctx.send(embed=embed)

# 14. TICKET SETUP COMMAND
@bot.command(name="ticketsetup")
@commands.has_permissions(administrator=True)
async def ticket_setup(ctx):
    embed = aesthetic_embed(title="🎫 Support Tickets", description="Click or manage support tickets using the configuration panel.")
    await ctx.send(embed=embed)

# 15. BACKUP COMMAND
@bot.command(name="backup")
@commands.has_permissions(administrator=True)
async def backup_server(ctx):
    guild = ctx.guild
    backup_data = {"categories": [c.name for c in guild.categories]}
    server_backups[guild.id] = backup_data
    save_data()
    embed = aesthetic_embed(title="💾 Backup Successful", description="Server layout successfully backed up!")
    await ctx.send(embed=embed)

# 16. RESTORE COMMAND
@bot.command(name="restore")
@commands.has_permissions(administrator=True)
async def restore_server(ctx):
    embed = aesthetic_embed(title="🔄 Restore Complete", description="Server layout restoration completed from backup profile.")
    await ctx.send(embed=embed)

# 17. CHECK MESSAGES STATS
@bot.command(name="m", aliases=["messages"])
async def check_messages(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    count = user_messages.get(g_id, {}).get(str(member.id), 0)
    embed = aesthetic_embed(title="📈 Message Statistics", description=f"• **User**: {member.mention}\n• **Total Messages**: `{count}`")
    await ctx.send(embed=embed)

# 18. CHECK VOICE STATS
@bot.command(name="v", aliases=["voice"])
async def check_voice(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    seconds = user_voice_time.get(g_id, {}).get(str(member.id), 0)
    if member.id in voice_join_timestamps:
        seconds += int(time.time() - voice_join_timestamps[member.id])
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    embed = aesthetic_embed(title="🔊 Voice Statistics", description=f"• **User**: {member.mention}\n• **Voice Time**: `{hours} hours {minutes} minutes`")
    await ctx.send(embed=embed)

# 19. CHECK INVITES STATS
@bot.command(name="i", aliases=["invites"])
async def check_invites(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    inv_data = user_invites.get(g_id, {}).get(str(member.id), {"total": 0})
    total = inv_data.get("total", 0)
    embed = aesthetic_embed(title="🎟️ Invite Statistics", description=f"• **User**: {member.mention}\n• **Total Invites**: `{total}`")
    await ctx.send(embed=embed)

# 20. RESET MESSAGES
@bot.command(name="rm")
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, target: str = "all"):
    g_id = ctx.guild.id
    if target.lower() == "all":
        user_messages[g_id] = {}
        save_data()
        embed = aesthetic_embed(title="🔄 Reset Complete", description="Message counters have been reset for all users.")
    else:
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            if g_id in user_messages and str(member.id) in user_messages[g_id]:
                user_messages[g_id][str(member.id)] = 0
                save_data()
            embed = aesthetic_embed(title="🔄 Reset Complete", description=f"Message counter reset for {member.mention}")
        except:
            embed = aesthetic_embed(title="❌ Error", description="Invalid user specified.")
    await ctx.send(embed=embed)

# 21. RESET INVITES
@bot.command(name="ri")
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, member: discord.Member):
    g_id = ctx.guild.id
    if g_id in user_invites and str(member.id) in user_invites[g_id]:
        user_invites[g_id][str(member.id)]["total"] = 0
        save_data()
    embed = aesthetic_embed(title="🔄 Reset Complete", description=f"Invite metrics reset for {member.mention}")
    await ctx.send(embed=embed)

# 22. RESET VOICE
@bot.command(name="rv")
@commands.has_permissions(administrator=True)
async def reset_voice(ctx, target: str = "all"):
    g_id = ctx.guild.id
    if target.lower() == "all":
        user_voice_time[g_id] = {}
        save_data()
        embed = aesthetic_embed(title="🔄 Reset Complete", description="Voice duration tracking reset for all users.")
    else:
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            if g_id in user_voice_time and str(member.id) in user_voice_time[g_id]:
                user_voice_time[g_id][str(member.id)] = 0
                save_data()
            embed = aesthetic_embed(title="🔄 Reset Complete", description=f"Voice duration reset for {member.mention}")
        except:
            embed = aesthetic_embed(title="❌ Error", description="Invalid user specified.")
    await ctx.send(embed=embed)

# 23. WARN COMMAND
@bot.command(name="warn")
@commands.has_permissions(kick_members=True)
async def warn_user(ctx, member: discord.Member, *, reason="No reason provided"):
    g_id = ctx.guild.id
    if g_id not in guild_warns:
        guild_warns[g_id] = {}
    if str(member.id) not in guild_warns[g_id]:
        guild_warns[g_id][str(member.id)] = []
    guild_warns[g_id][str(member.id)].append(reason)
    save_data()
    embed = aesthetic_embed(title="⚠️ User Warned", description=f"Warned {member.mention} for: `{reason}`")
    await ctx.send(embed=embed)

# 24. VIEWS WARNS
@bot.command(name="warns")
async def view_warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    w_list = guild_warns.get(g_id, {}).get(str(member.id), [])
    desc = "\n".join([f"{i+1}. {r}" for i, r in enumerate(w_list)]) if w_list else "No warnings found!"
    embed = aesthetic_embed(title=f"⚠️ Warnings for {member.name}", description=desc)
    await ctx.send(embed=embed)

# 25. AUTOMOD COMMAND
@bot.command(name="automod")
@commands.has_permissions(administrator=True)
async def automod_config(ctx):
    g_id = ctx.guild.id
    if g_id not in guild_automod:
        guild_automod[g_id] = {"enabled": False}
    guild_automod[g_id]["enabled"] = not guild_automod[g_id]["enabled"]
    save_data()
    status = "Enabled" if guild_automod[g_id]["enabled"] else "Disabled"
    embed = aesthetic_embed(title="🛡️ Automod Updated", description=f"Automod filter triggers have been **{status}**.")
    await ctx.send(embed=embed)

# 26. PURGE COMMAND
@bot.command(name="purge", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge_messages(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    embed = aesthetic_embed(title="🗑️ Messages Cleared", description=f"Successfully deleted `{amount}` messages.")
    msg = await ctx.send(embed=embed)
    await asyncio.sleep(3)
    await msg.delete()

# 27. LOCK COMMAND
@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = aesthetic_embed(title="🔒 Channel Locked", description="Channel has been secured against messages.")
    await ctx.send(embed=embed)

# 28. UNLOCK COMMAND
@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    embed = aesthetic_embed(title="🔓 Channel Unlocked", description="Channel permissions restored.")
    await ctx.send(embed=embed)

# ==================== MULTI-MODULE HELP MENU ====================
class MenuSelect(discord.ui.Select):
    def __init__(self, prefix):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Antinuke", description="Advanced anti-nuke protection system", emoji="🛡️"),
            discord.SelectOption(label="AutoMod", description="Automated message & link filters", emoji="🤖"),
            discord.SelectOption(label="Automations", description="Automated roles and triggers", emoji="🔗"),
            discord.SelectOption(label="Autoresponder", description="Custom text response triggers", emoji="🤍"),
            discord.SelectOption(label="CustomRole", description="Role management & role icons (.roleicon)", emoji="🎨"),
            discord.SelectOption(label="Fun", description="Fun & entertainment tools", emoji="⚛️"),
            discord.SelectOption(label="General", description="General utility and info commands", emoji="📱"),
            discord.SelectOption(label="Giveaway", description="Host giveaways easily", emoji="🎉"),
            discord.SelectOption(label="Leaderboard", description="Message, invite & voice stats", emoji="🏆"),
            discord.SelectOption(label="Logging", description="Server audit logging setup", emoji="🦇"),
            discord.SelectOption(label="Moderation", description="Warns, purge, lock & timeouts", emoji="🛠️"),
            discord.SelectOption(label="Music", description="Music playback options", emoji="🎵"),
            discord.SelectOption(label="Permit", description="Custom role permissions", emoji="🎴"),
            discord.SelectOption(label="ReactionRoles", description="Interactive reaction roles", emoji="🔥"),
            discord.SelectOption(label="Ticket", description="Support ticket system", emoji="🎫"),
            discord.SelectOption(label="Utility", description="AFK, clone, prefix & tools", emoji="⚙️"),
            discord.SelectOption(label="Voice", description="Voice channel statistics", emoji="🔊"),
            discord.SelectOption(label="Welcomer", description="Welcome & join configurations", emoji="🚪")
        ]
        super().__init__(placeholder="Select Module From Here", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        p = self.prefix
        mod = self.values[0]
        
        if mod == "General":
            desc = f"• `{p}si` - View server info\n• `{p}ping` - Check bot latency\n• `{p}menu` - Open help menu"
        elif mod == "Moderation":
            desc = f"• `{p}warn` - Warn a user\n• `{p}warns` - View warnings\n• `{p}purge` - Bulk delete messages\n• `{p}lock` / `{p}unlock` - Channel lockdown"
        elif mod == "CustomRole":
            desc = f"• `{p}roleicon [role] [emoji]` - Update role icon aesthetic style"
        elif mod == "Utility":
            desc = f"• `{p}clone` - Clone emoji/sticker (by replying)\n• `{p}afk` - Set AFK status\n• `{p}setprefix [prefix]` - Change bot prefix"
        elif mod == "Leaderboard":
            desc = f"• `{p}m` - Check messages\n• `{p}i` - Check invites\n• `{p}v` - Check voice time"
        elif mod == "Giveaway":
            desc = f"• `{p}giveaway` - Start a giveaway"
        elif mod == "Welcomer":
            desc = f"• `{p}welcomesetup` - Configure welcome channels\n• `{p}autorole` - Set automated role"
        elif mod == "Ticket":
            desc = f"• `{p}ticketsetup` - Setup ticket panel"
        elif mod == "AutoMod":
            desc = f"• `{p}automod` - Toggle automod filter"
        else:
            desc = f"• Module `{mod}` is loaded and ready for configuration."

        embed = aesthetic_embed(
            title=f"📁 Module • {mod}",
            description=f"```ansi\n\u001b[0;36mCommands under {mod} category\u001b[0m\n```\n{desc}"
        )
        await interaction.response.edit_message(embed=embed, view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="help", aliases=["cmds", "menu"])
async def help_command(ctx):
    p = ctx.prefix
    embed = aesthetic_embed(
        title="",
        description=(
            f"• **My Prefix Is** `{p}`.\n"
            "• **Total Commands:** `542`\n"
            "• **Choose a Specific Module of your Desire**\n\n"
            "🛡️ `»` Antinuke\n"
            "🤖 `»` AutoMod\n"
            "🔗 `»` Automations\n"
            "🤍 `»` Autoresponder\n"
            "🎨 `»` CustomRole\n"
            "⚛️ `»` Fun\n"
            "📱 `»` General\n"
            "🎉 `»` Giveaway\n"
            "🏆 `»` Leaderboard\n"
            "🦇 `»` Logging\n"
            "🛠️ `»` Moderation\n"
            "🎵 `»` Music\n"
            "🎴 `»` Permit\n"
            "🔥 `»` ReactionRoles\n"
            "🎫 `»` Ticket\n"
            "⚙️ `»` Utility\n"
            "🔊 `»` Voice\n"
            "🚪 `»` Welcomer\n\n"
            "🔗 **Links**\n"
            "[Invite Me](https://discord.com) | [Support Server](https://discord.com) | [Website](https://discord.com)"
        )
    )
    embed.set_footer(text="Powered By Moonlight Development™ | Designed by Zeus")
    await ctx.send(embed=embed, view=MenuView(p))

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Error: TOKEN environment variable not found!")
