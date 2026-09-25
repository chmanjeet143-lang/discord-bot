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
        "nickname_setup": {}, "counting": {}, "autoresponder": {}, "antinuke": {}, 
        "reaction_roles": {}, "abuse_words": {}, "antispam_status": {}, "antiabuse_status": {}
    }

def save_data():
    data = {
        "logs": guild_logs, "birthdays": guild_birthdays, "backups": server_backups,
        "prefixes": guild_prefixes, "warns": guild_warns, "automod": guild_automod,
        "autorole": guild_autoroles, "tickets": guild_tickets, "welcome": guild_welcomes,
        "messages": user_messages, "voice_time": user_voice_time, "invites": user_invites,
        "nickname_setup": guild_nicknames, "counting": guild_counting, "autoresponder": guild_autoresponder,
        "antinuke": guild_antinuke, "reaction_roles": guild_reaction_roles, "abuse_words": guild_abuse_words,
        "antispam_status": guild_antispam_status, "antiabuse_status": guild_antiabuse_status
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
guild_abuse_words = {int(k): v for k, v in db.get("abuse_words", {}).items()}
guild_antispam_status = {int(k): v for k, v in db.get("antispam_status", {}).items()}
guild_antiabuse_status = {int(k): v for k, v in db.get("antiabuse_status", {}).items()}

def get_prefix(bot, message):
    if not message.guild:
        return "&"
    return guild_prefixes.get(message.guild.id, "&")

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

afk_users = {}
voice_join_timestamps = {}
snipe_data = {}
user_message_times = {}

def emb(title="", description="", color=0x5865F2):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
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
    print("Status: All Old Commands + Anti-Spam/Abuse Online!")
    print("----------------------------------------")

@bot.event
async def on_command_error(ctx, error):
    p = ctx.prefix
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=emb(title="Access Denied", description="You do not have the required permissions to use this command."))
    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name
        usage_dict = {
            "ban": f"Proper Way: `{p}ban @user [reason]`",
            "kick": f"Proper Way: `{p}kick @user [reason]`",
            "mute": f"Proper Way: `{p}mute @user [minutes] [reason]`",
            "warn": f"Proper Way: `{p}warn @user [reason]`",
            "purge": f"Proper Way: `{p}purge [amount]`",
            "setprefix": f"Proper Way: `{p}setprefix [new_prefix]`",
            "ar": f"Proper Way: `{p}ar [trigger] [response]`",
            "autorole": f"Proper Way: `{p}autorole [@role]`",
            "giveaway": f"Proper Way: `{p}giveaway [time] [winners] [prize]`",
            "poll": f"Proper Way: `{p}poll [question]`",
            "say": f"Proper Way: `{p}say [text]`",
            "reminder": f"Proper Way: `{p}reminder [minutes] [task]`",
            "addrole": f"Proper Way: `{p}addrole @user @role`",
            "removerole": f"Proper Way: `{p}removerole @user @role`",
            "cloneemoji": f"Proper Way: `{p}cloneemoji [emoji] [name]`",
            "clonesticker": f"Proper Way: `{p}clonesticker [name]`",
            "addabuse": f"Proper Way: `{p}addabuse [word]`",
            "removeabuse": f"Proper Way: `{p}removeabuse [word]`",
            "antispam": f"Proper Way: `{p}antispam [on/off]`",
            "antiabuse": f"Proper Way: `{p}antiabuse [on/off]`"
        }
        correct_usage = usage_dict.get(cmd_name, f"Check help menu: `{p}help`")
        await ctx.send(embed=emb(title="⚠️ Invalid Command Usage", description=correct_usage))
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=emb(title="⚠️ Bad Argument", description="You provided an invalid value. Please check your input parameters."))
    else:
        print(f"Error: {error}")

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    snipe_data[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "time": datetime.now().strftime("%H:%M:%S")
    }

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    g_id = member.guild.id
    u_id = str(member.id)
    key = (g_id, member.id)
    
    if before.channel is None and after.channel is not None:
        voice_join_timestamps[key] = time.time()
    elif before.channel is not None and after.channel is None:
        start_time = voice_join_timestamps.pop(key, None)
        if start_time:
            duration = int(time.time() - start_time)
            if g_id not in user_voice_time: user_voice_time[g_id] = {}
            user_voice_time[g_id][u_id] = user_voice_time[g_id].get(u_id, 0) + duration
            save_data()
    elif before.channel != after.channel and before.channel is not None and after.channel is not None:
        start_time = voice_join_timestamps.pop(key, None)
        if start_time:
            duration = int(time.time() - start_time)
            if g_id not in user_voice_time: user_voice_time[g_id] = {}
            user_voice_time[g_id][u_id] = user_voice_time[g_id].get(u_id, 0) + duration
        voice_join_timestamps[key] = time.time()
        save_data()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    g_id = message.guild.id if message.guild else 0
    u_id = message.author.id

    # 1. ANTI-ABUSE SYSTEM
    if message.guild and guild_antiabuse_status.get(g_id, False):
        abuse_list = guild_abuse_words.get(g_id, [])
        content_lower = message.content.lower()
        if any(word in content_lower for word in abuse_list):
            try:
                await message.delete()
                duration = timedelta(hours=1)
                await message.author.timeout(duration, reason="Using forbidden server abuse words.")
                await message.channel.send(f"⚠️ {message.author.mention}, you wanted to abuse, but you couldn't do it! Take a 1-hour timeout! 🤡", delete_after=10)
                return
            except Exception as e:
                print(f"Anti-Abuse Error: {e}")

    # 2. ANTI-SPAM SYSTEM (3 msgs in 5 seconds)
    if message.guild and guild_antispam_status.get(g_id, False) and not message.author.guild_permissions.manage_messages:
        now = time.time()
        key = (g_id, u_id)
        if key not in user_message_times:
            user_message_times[key] = []
        
        user_message_times[key] = [t for t in user_message_times[key] if now - t < 5]
        user_message_times[key].append(now)

        if len(user_message_times[key]) >= 3:
            user_message_times[key] = [] 
            try:
                duration = timedelta(minutes=5)
                await message.author.timeout(duration, reason="Spamming messages in chat.")
                await message.channel.send(f"🛑 {message.author.mention}, you wanted to spam, but you couldn't do it! Take a 5-minute timeout! 💀", delete_after=10)
                return
            except Exception as e:
                print(f"Anti-Spam Error: {e}")

    # Autoresponder Check
    if g_id in guild_autoresponder:
        responses = guild_autoresponder[g_id]
        if message.content.lower() in responses:
            await message.channel.send(responses[message.content.lower()])

    # Counting Check
    if g_id in guild_counting:
        c_data = guild_counting[g_id]
        if message.channel.id == c_data.get("channel_id"):
            try:
                number = int(message.content.strip())
                expected = c_data.get("next_number", 1)
                last_user = c_data.get("last_user", 0)
                custom_emoji = c_data.get("emoji", "✅")
                
                if number == expected and u_id != last_user:
                    c_data["next_number"] = expected + 1
                    c_data["last_user"] = u_id
                    save_data()
                    try:
                        await message.add_reaction(custom_emoji)
                    except:
                        await message.add_reaction("✅")
                else:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, wrong number! Counting reset back to `{expected}`.", delete_after=4)
            except ValueError:
                if not message.author.guild_permissions.manage_messages:
                    try: await message.delete()
                    except: pass

    if g_id not in user_messages: user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    if u_id in afk_users:
        del afk_users[u_id]
        try: await message.channel.send(f"Welcome back, {message.author.mention}! Your AFK status has been cleared.", delete_after=5)
        except: pass

    await bot.process_commands(message)

# ==================== ALL OLD & NEW COMMANDS ====================

@bot.command(name="ping")
async def ping_command(ctx):
    await ctx.send(embed=emb(title="Bot Latency", description=f"Response Rate: {round(bot.latency * 1000)}ms"))

@bot.command(name="si", aliases=["serverinfo"])
async def server_info(ctx):
    g = ctx.guild
    desc = f"Owner: {g.owner}\nTotal Members: {g.member_count}\nCreated At: {g.created_at.strftime('%d-%b-%Y')}\nChannels: {len(g.channels)}"
    e = emb(title=f"Server Information - {g.name}", description=desc)
    if g.icon: e.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=e)

@bot.command(name="ui", aliases=["userinfo", "whois"])
async def user_info(ctx, member: discord.Member = None):
    m = member or ctx.author
    roles = [r.mention for r in m.roles if r != ctx.guild.default_role]
    desc = f"Name: {m}\nID: {m.id}\nJoined Server: {m.joined_at.strftime('%d-%b-%Y') if m.joined_at else 'Unknown'}\nRoles: {', '.join(roles[:10]) if roles else 'None'}"
    e = emb(title=f"User Profile - {m.name}", description=desc)
    if m.avatar: e.set_thumbnail(url=m.avatar.url)
    await ctx.send(embed=e)

@bot.command(name="mc", aliases=["membercount"])
async def member_count(ctx):
    g = ctx.guild
    total = g.member_count
    bots = sum(1 for m in g.members if m.bot)
    humans = total - bots
    online = sum(1 for m in g.members if m.status == discord.Status.online)
    desc = f"Total Members: {total}\nTotal Humans: {humans}\nTotal Bots: {bots}\nOnline Members: {online}"
    await ctx.send(embed=emb(title="Member Statistics", description=desc))

@bot.command(name="avatar", aliases=["av"])
async def user_avatar(ctx, member: discord.Member = None):
    m = member or ctx.author
    e = emb(title=f"Avatar - {m.name}", description=f"Direct Link: [Click Here]({m.avatar.url if m.avatar else m.default_avatar.url})")
    if m.avatar: e.set_image(url=m.avatar.url)
    await ctx.send(embed=e)

@bot.command(name="snipe")
async def snipe_msg(ctx):
    ch_id = ctx.channel.id
    if ch_id in snipe_data:
        data = snipe_data[ch_id]
        e = emb(title="Last Deleted Message", description=f"Author: {data['author'].mention}\nContent: {data['content']}\nTime: {data['time']}")
        await ctx.send(embed=e)
    else:
        await ctx.send(embed=emb(title="Snipe Record", description="No recently deleted messages found in this channel."))

@bot.command(name="addrole")
@commands.has_permissions(manage_roles=True)
async def add_role(ctx, member: discord.Member, role: discord.Role):
    if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=emb(title="Error", description="You cannot assign a role higher or equal to your own top role."))
    await member.add_roles(role)
    await ctx.send(embed=emb(title="Role Added", description=f"Successfully added {role.name} to {member.mention}."))

@bot.command(name="removerole")
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=emb(title="Error", description="You cannot remove a role higher or equal to your own top role."))
    await member.remove_roles(role)
    await ctx.send(embed=emb(title="Role Removed", description=f"Successfully removed {role.name} from {member.mention}."))

@bot.command(name="hide")
@commands.has_permissions(manage_channels=True)
async def hide_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, view_channel=False)
    await ctx.send(embed=emb(title="Channel Hidden", description=f"{ch.mention} has been hidden from everyone."))

@bot.command(name="unhide")
@commands.has_permissions(manage_channels=True)
async def unhide_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, view_channel=True)
    await ctx.send(embed=emb(title="Channel Unhidden", description=f"{ch.mention} is now visible to members."))

@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx, category: str = "messages"):
    g_id = ctx.guild.id
    cat = category.lower()
    
    if cat in ["msg", "messages", "message"]:
        data = user_messages.get(g_id, {})
        if not data:
            return await ctx.send(embed=emb(title="Leaderboard", description="No message stats recorded yet."))
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
        desc = "\n".join([f"#{i+1} <@{uid}> — {count} messages" for i, (uid, count) in enumerate(sorted_data)])
        title = "Message Leaderboard"
    elif cat in ["voice", "vc", "vctime"]:
        data = user_voice_time.get(g_id, {})
        if not data:
            return await ctx.send(embed=emb(title="Leaderboard", description="No voice stats recorded yet."))
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
        desc = "\n".join([f"#{i+1} <@{uid}> — {secs // 60} mins" for i, (uid, secs) in enumerate(sorted_data)])
        title = "Voice Chat Leaderboard"
    else:
        return await ctx.send(embed=emb(title="Invalid Category", description="Please choose from: messages, voice."))
        
    await ctx.send(embed=emb(title=title, description=desc))

@bot.command(name="cloneemoji")
@commands.has_permissions(manage_emojis=True)
async def clone_emoji(ctx, emoji: discord.Emoji, name: str = None):
    e_name = name or emoji.name
    image_bytes = await emoji.url.read()
    new_emoji = await ctx.guild.create_custom_emoji(name=e_name, image=image_bytes)
    await ctx.send(embed=emb(title="Emoji Cloned", description=f"Successfully cloned emoji {new_emoji} as {e_name}!"))

@bot.command(name="clonesticker")
@commands.has_permissions(manage_emojis=True)
async def clone_sticker(ctx, name: str = None):
    if not ctx.message.stickers:
        return await ctx.send(embed=emb(title="Error", description="Please attach or reply with a message containing a sticker to clone."))
    sticker = ctx.message.stickers[0]
    file = await sticker.to_file()
    s_name = name or sticker.name
    new_sticker = await ctx.guild.create_sticker(name=s_name, description="Cloned sticker", file=file)
    await ctx.send(embed=emb(title="Sticker Cloned", description=f"Successfully cloned sticker {new_sticker.name}!"))

# --- Anti-Spam & Anti-Abuse Control Commands ---
@bot.command(name="antispam")
@commands.has_permissions(administrator=True)
async def anti_spam_toggle(ctx, status: str):
    g_id = ctx.guild.id
    st = status.lower()
    if st in ["on", "enable", "true"]:
        guild_antispam_status[g_id] = True
        save_data()
        await ctx.send(embed=emb(title="Anti-Spam Status", description="🛡️ Anti-Spam protection is now **ENABLED**."))
    elif st in ["off", "disable", "false"]:
        guild_antispam_status[g_id] = False
        save_data()
        await ctx.send(embed=emb(title="Anti-Spam Status", description="⚠️ Anti-Spam protection is now **DISABLED**."))
    else:
        await ctx.send(embed=emb(title="Error", description="Please use `&antispam on` or `&antispam off`."))

@bot.command(name="antiabuse")
@commands.has_permissions(administrator=True)
async def anti_abuse_toggle(ctx, status: str):
    g_id = ctx.guild.id
    st = status.lower()
    if st in ["on", "enable", "true"]:
        guild_antiabuse_status[g_id] = True
        save_data()
        await ctx.send(embed=emb(title="Anti-Abuse Status", description="🛡️ Anti-Abuse filter is now **ENABLED**."))
    elif st in ["off", "disable", "false"]:
        guild_antiabuse_status[g_id] = False
        save_data()
        await ctx.send(embed=emb(title="Anti-Abuse Status", description="⚠️ Anti-Abuse filter is now **DISABLED**."))
    else:
        await ctx.send(embed=emb(title="Error", description="Please use `&antiabuse on` or `&antiabuse off`."))

@bot.command(name="addabuse")
@commands.has_permissions(administrator=True)
async def add_abuse(ctx, *, word: str):
    g_id = ctx.guild.id
    if g_id not in guild_abuse_words:
        guild_abuse_words[g_id] = []
    w = word.lower()
    if w not in guild_abuse_words[g_id]:
        guild_abuse_words[g_id].append(w)
        save_data()
        await ctx.send(embed=emb(title="Anti-Abuse Updated", description=f"✅ Added `{w}` to the server's forbidden abuse list."))
    else:
        await ctx.send(embed=emb(title="Notice", description=f"The word `{w}` is already in the abuse list."))

@bot.command(name="removeabuse")
@commands.has_permissions(administrator=True)
async def remove_abuse(ctx, *, word: str):
    g_id = ctx.guild.id
    w = word.lower()
    if g_id in guild_abuse_words and w in guild_abuse_words[g_id]:
        guild_abuse_words[g_id].remove(w)
        save_data()
        await ctx.send(embed=emb(title="Anti-Abuse Updated", description=f"❌ Removed `{w}` from the forbidden abuse list."))
    else:
        await ctx.send(embed=emb(title="Error", description=f"The word `{w}` was not found in the abuse list."))

@bot.command(name="abuses", aliases=["abuselist"])
async def list_abuses(ctx):
    g_id = ctx.guild.id
    words = guild_abuse_words.get(g_id, [])
    desc = ", ".join([f"`{w}`" for w in words]) if words else "No abuse words added yet for this server."
    await ctx.send(embed=emb(title="🛡️ Server Abuse Filter List", description=desc))

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(embed=emb(title="User Banned", description=f"{member.mention} has been banned.\nReason: {reason}"))

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_user(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(embed=emb(title="User Kicked", description=f"{member.mention} has been kicked.\nReason: {reason}"))

@bot.command(name="mute", aliases=["timeout"])
@commands.has_permissions(moderate_members=True)
async def mute_user(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(embed=emb(title="User Muted", description=f"{member.mention} timed out for {minutes} mins.\nReason: {reason}"))

@bot.command(name="unmute", aliases=["untimeout"])
@commands.has_permissions(moderate_members=True)
async def unmute_user(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(embed=emb(title="User Unmuted", description=f"Timeout removed from {member.mention}."))

@bot.command(name="warn")
@commands.has_permissions(kick_members=True)
async def warn_user(ctx, member: discord.Member, *, reason="No reason provided"):
    g_id = ctx.guild.id
    if g_id not in guild_warns: guild_warns[g_id] = {}
    if str(member.id) not in guild_warns[g_id]: guild_warns[g_id][str(member.id)] = []
    guild_warns[g_id][str(member.id)].append(reason)
    save_data()
    total_warns = len(guild_warns[g_id][str(member.id)])
    await ctx.send(embed=emb(title="User Warned", description=f"{member.mention} has been warned.\nReason: {reason}\nTotal Warnings: {total_warns}"))

@bot.command(name="warnings", aliases=["warns"])
async def check_warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    user_warn_list = guild_warns.get(g_id, {}).get(str(member.id), [])
    desc = f"Target: {member.mention}\nTotal Warnings: {len(user_warn_list)}\n\n" + "\n".join([f"• {w}" for w in user_warn_list]) if user_warn_list else f"{member.mention} has no warnings."
    await ctx.send(embed=emb(title="Warning Records", description=desc))

@bot.command(name="purge", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge_msgs(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=emb(title="Messages Cleared", description=f"Successfully wiped {amount} messages."))
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_ch(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=emb(title="Channel Locked", description="Channel locked. Members cannot write messages."))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_ch(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=emb(title="Channel Unlocked", description="Channel unlocked. Members can chat again."))

@bot.command(name="slowmode")
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(embed=emb(title="Slowmode Updated", description=f"Channel slowmode set to {seconds} seconds."))

@bot.command(name="roll")
async def roll_dice(ctx):
    await ctx.send(embed=emb(title="Dice Roll", description=f"Result: [{random.randint(1, 6)}]"))

@bot.command(name="coinflip")
async def coin_flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(embed=emb(title="Coin Flip", description=f"Landed on: {result}"))

@bot.command(name="8ball")
async def magic_8ball(ctx, *, question: str):
    answers = ["Yes, definitely.", "No way.", "Outlook is good.", "Ask again later.", "Without a doubt.", "Very doubtful."]
    await ctx.send(embed=emb(title="Magic 8-Ball", description=f"Question: {question}\nAnswer: {random.choice(answers)}"))

@bot.command(name="iq")
async def check_iq(ctx, member: discord.Member = None):
    m = member or ctx.author
    await ctx.send(embed=emb(title="IQ Test", description=f"{m.mention}'s calculated IQ score is: {random.randint(50, 180)}"))

@bot.command(name="slap")
async def slap_user(ctx, member: discord.Member):
    await ctx.send(embed=emb(title="Action", description=f"{ctx.author.mention} slapped {member.mention}!"))

@bot.command(name="hug")
async def hug_user(ctx, member: discord.Member):
    await ctx.send(embed=emb(title="Action", description=f"{ctx.author.mention} hugged {member.mention}!"))

@bot.command(name="say")
async def say_msg(ctx, *, text: str):
    try: await ctx.message.delete()
    except: pass
    await ctx.send(text)

@bot.command(name="poll")
async def create_poll(ctx, *, question: str):
    e = emb(title="New Poll", description=f"{question}\n\n👍 Click for Yes\n👎 Click for No")
    msg = await ctx.send(embed=e)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")

@bot.command(name="afk")
async def afk_cmd(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(embed=emb(title="AFK Enabled", description=f"{ctx.author.mention} is now away: {reason}"))

@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, prefix: str):
    guild_prefixes[ctx.guild.id] = prefix
    save_data()
    await ctx.send(embed=emb(title="Prefix Updated", description=f"New prefix changed to: {prefix}"))

@bot.command(name="start", aliases=["counting"])
@commands.has_permissions(administrator=True)
async def start_counting(ctx, amount: int = 1, channel: discord.TextChannel = None, emoji: str = "✅"):
    target_channel = channel or ctx.channel
    guild_counting[ctx.guild.id] = {"channel_id": target_channel.id, "next_number": amount, "last_user": 0, "emoji": emoji}
    save_data()
    await ctx.send(embed=emb(title="Counting Initialized", description=f"Started in {target_channel.mention} at number {amount} using emoji {emoji}."))

@bot.command(name="m", aliases=["messages"])
async def msg_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    count = user_messages.get(ctx.guild.id, {}).get(str(member.id), 0)
    await ctx.send(embed=emb(title="Message Tracking", description=f"{member.mention} has sent {count} messages."))

@bot.command(name="v", aliases=["voice"])
async def voice_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    secs = user_voice_time.get(ctx.guild.id, {}).get(str(member.id), 0)
    minutes = secs // 60
    hours = minutes // 60
    rem_mins = minutes % 60
    await ctx.send(embed=emb(title="Voice Tracking", description=f"{member.mention} spent {hours}h {rem_mins}m in voice channels."))

@bot.command(name="reminder")
async def reminder_cmd(ctx, minutes: int, *, task: str):
    await ctx.send(embed=emb(title="Reminder Set", description=f"I will remind you about '{task}' in {minutes} minutes."))
    await asyncio.sleep(minutes * 60)
    await ctx.send(f"🔔 {ctx.author.mention}, reminder triggered: {task}")

@bot.command(name="welcomesetup")
@commands.has_permissions(administrator=True)
async def w_setup(ctx, main_ch: discord.TextChannel, rules_ch: discord.TextChannel):
    guild_welcomes[ctx.guild.id] = {"main_channel": main_ch.id, "rules_channel": rules_ch.id}
    save_data()
    await ctx.send(embed=emb(title="Welcome Setup", description=f"Welcome channel mapped to {main_ch.mention}."))

@bot.command(name="autorole")
@commands.has_permissions(administrator=True)
async def auto_role(ctx, role: discord.Role):
    guild_autoroles[ctx.guild.id] = role.id
    save_data()
    await ctx.send(embed=emb(title="Autorole Configured", description=f"New users receive {role.name} automatically."))

@bot.command(name="ar")
@commands.has_permissions(administrator=True)
async def auto_responder(ctx, trigger: str, *, response: str):
    g_id = ctx.guild.id
    if g_id not in guild_autoresponder: guild_autoresponder[g_id] = {}
    guild_autoresponder[g_id][trigger.lower()] = response
    save_data()
    await ctx.send(embed=emb(title="Autoresponder Saved", description=f"Trigger: {trigger} -> Response: {response}"))

@bot.command(name="antinuke")
@commands.has_permissions(administrator=True)
async def anti_nuke(ctx, status: str):
    guild_antinuke[ctx.guild.id] = status.lower() == "on"
    save_data()
    await ctx.send(embed=emb(title="Anti-Nuke Status", description=f"Security mode is now {status.upper()}."))

@bot.command(name="automod")
@commands.has_permissions(administrator=True)
async def auto_mod(ctx):
    g_id = ctx.guild.id
    if g_id not in guild_automod: guild_automod[g_id] = {"enabled": False}
    guild_automod[g_id]["enabled"] = not guild_automod[g_id]["enabled"]
    save_data()
    status = "Enabled" if guild_automod[g_id]["enabled"] else "Disabled"
    await ctx.send(embed=emb(title="Automod Protection", description=f"Automod status: {status}."))

@bot.command(name="giveaway", aliases=["gvw", "gcreate"])
@commands.has_permissions(manage_guild=True)
async def g_start(ctx, time_str: str, winners: int, *, prize: str):
    e = emb(title="🎉 GIVEAWAY 🎉", description=f"🎁 **Prize**: {prize}\n👑 **Winners**: `{winners}`\n⏱️ **Duration**: `{time_str}`\n\nReact with 🎉 to enter!")
    msg = await ctx.send(embed=e)
    await msg.add_reaction("🎉")

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def log_setup(ctx):
    ch = await ctx.guild.create_text_channel("bot-audit-logs")
    guild_logs[ctx.guild.id] = {"logs": ch.id}
    save_data()
    await ctx.send(embed=emb(title="Audit Logs Setup", description=f"Logs routing to {ch.mention}."))

# ==================== HELP MENU ====================

class MenuSelect(discord.ui.Select):
    def __init__(self, prefix):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Moderation & Roles", description="Ban, mute, add/role, hide/unhide", emoji="🛠️"),
            discord.SelectOption(label="Fun & Games", description="8ball, roll, coinflip, iq, slap, hug", emoji="⚛️"),
            discord.SelectOption(label="Utility & Leaderboard", description="Ping, info, snipe, lb (msg/voice)", emoji="⚙️"),
            discord.SelectOption(label="Setup & Security", description="Antinuke, automod, giveaway, clone, antispam, antiabuse", emoji="🛡️")
        ]
        super().__init__(placeholder="SELECT CATEGORY", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        mod = self.values[0]
        e = emb(title=f"Module - {mod}", description=f"Browsing section: {mod}\nUse prefix '{self.prefix}' before commands.")
        await interaction.response.edit_message(embed=e, view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="help", aliases=["cmds", "menu", "helpme"])
async def help_command(ctx):
    p = ctx.prefix
    desc = (
        f"Prefix: {p} | Developer: Zeus\n"
        "Status: Online & Fully Operational\n\n"
        "Select a category below to explore modular toolsets:\n\n"
        "🛠️ **Moderation**: ban, kick, mute, purge, addrole, removerole, hide, unhide\n"
        "⚛️ **Fun**: 8ball, roll, coinflip, iq, slap, hug, poll\n"
        "⚙️ **Utility**: ping, serverinfo, userinfo, snipe, leaderboard\n"
        "🛡️ **Setup**: giveaway, antispam, antiabuse, addabuse, removeabuse, cloneemoji"
    )
    e = discord.Embed(title="Moonlight Heaven - Control Center", description=desc, color=0x5865F2)
    e.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=e, view=MenuView(p))

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Error: TOKEN environment variable not found!")
