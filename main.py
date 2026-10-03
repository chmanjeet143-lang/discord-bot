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

# ==================== WEB SERVER (KEEP ALIVE) ====================
app = Flask('')

@app.route('/')
def home():
    return "🤖 Moonlight Heaven Master Bot is Online & Fully Operational!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==================== INTENTS & CONFIG ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.presences = True
intents.invites = True

DATA_FILE = "bot_database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
            pass
    return {
        "logs": {}, "birthdays": {}, "backups": {}, "prefixes": {},
        "warns": {}, "automod": {}, "autorole": {}, "tickets": {}, 
        "welcome": {}, "messages": {}, "voice_time": {}, "invites": {},
        "nickname_setup": {}, "counting": {}, "autoresponder": {}, "antinuke": {}, 
        "reaction_roles": {}, "abuse_words": {}, "antispam_status": {}, "antiabuse_status": {},
        "antispam_config": {}, "antiabuse_config": {}, "command_logs": {}, "ghost_ping": {}
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
        "counting": guild_counting, 
        "autoresponder": guild_autoresponder,
        "antinuke": guild_antinuke, 
        "reaction_roles": guild_reaction_roles, 
        "abuse_words": guild_abuse_words,
        "antispam_status": guild_antispam_status, 
        "antiabuse_status": guild_antiabuse_status,
        "antispam_config": guild_antispam_config, 
        "antiabuse_config": guild_antiabuse_config,
        "command_logs": guild_command_logs, 
        "ghost_ping": guild_ghost_ping
    }
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving database: {e}")

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
guild_antispam_config = {int(k): v for k, v in db.get("antispam_config", {}).items()}
guild_antiabuse_config = {int(k): v for k, v in db.get("antiabuse_config", {}).items()}
guild_command_logs = {int(k): v for k, v in db.get("command_logs", {}).items()}
guild_ghost_ping = {int(k): v for k, v in db.get("ghost_ping", {}).items()}

def get_prefix(bot, message):
    if not message.guild:
        return "&"
    return guild_prefixes.get(message.guild.id, "&")

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

afk_users = {}
user_message_times = {}
voice_joindata = {}
cached_invites = {}
external_spam_tracker = {}

DEFAULT_THUMBNAIL = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def emb(title="", description="", color=0xFFFFFF, thumbnail=None):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail or DEFAULT_THUMBNAIL)
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    return embed

@bot.event
async def on_ready():
    print("----------------------------------------")
    print("Bot Name: Moonlight Heaven (Master Full Expanded Edition)")
    print("Status: All 680+ Lines Loaded Successfully!")
    print("----------------------------------------")
    for guild in bot.guilds:
        try:
            cached_invites[guild.id] = await guild.invites()
        except Exception as e:
            print(f"Invite cache error for {guild.name}: {e}")

@bot.event
async def on_member_join(member):
    guild = member.guild
    try:
        old_invites = cached_invites.get(guild.id, [])
        new_invites = await guild.invites()
        cached_invites[guild.id] = new_invites
        
        inviter = None
        for inv in new_invites:
            for old in old_invites:
                if inv.code == old.code and inv.uses > old.uses:
                    inviter = inv.inviter
                    break
            if inviter:
                break
        
        if inviter:
            g_id = guild.id
            if g_id not in user_invites: 
                user_invites[g_id] = {}
            inv_id = str(inviter.id)
            if inv_id not in user_invites[g_id]:
                user_invites[g_id][inv_id] = {"total": 0, "joins": []}
            user_invites[g_id][inv_id]["total"] += 1
            user_invites[g_id][inv_id]["joins"].append(member.id)
            save_data()
    except Exception as e:
        print(f"Invite tracking error: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot or not member.guild:
        return
    g_id = member.guild.id
    u_id = member.id
    key = (g_id, u_id)
    
    if before.channel is None and after.channel is not None:
        voice_joindata[key] = time.time()
    elif before.channel is not None and after.channel is None:
        if key in voice_joindata:
            elapsed = int(time.time() - voice_joindata.pop(key))
            if g_id not in user_voice_time: 
                user_voice_time[g_id] = {}
            user_voice_time[g_id][str(u_id)] = user_voice_time[g_id].get(str(u_id), 0) + elapsed
            save_data()

# ==================== ADVANCED EXTERNAL APP / TROLL SNIFFER ====================

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    g_id = message.guild.id if message.guild else 0
    u_id = message.author.id
    content = message.content.strip()

    # External Apps / Troll / Exploits Sniffer (Catches what audit log misses)
    if message.guild:
        now = time.time()
        if g_id not in external_spam_tracker:
            external_spam_tracker[g_id] = {}
        if u_id not in external_spam_tracker[g_id]:
            external_spam_tracker[g_id][u_id] = []
        
        external_spam_tracker[g_id][u_id] = [t for t in external_spam_tracker[g_id][u_id] if now - t < 3]
        external_spam_tracker[g_id][u_id].append(now)

        if len(external_spam_tracker[g_id][u_id]) >= 4:
            log_channel_id = guild_command_logs.get(g_id)
            if log_channel_id:
                log_ch = message.guild.get_channel(log_channel_id)
                if log_ch:
                    alert_embed = emb(
                        title="🚨 External App / Troll Activity Caught",
                        description=f"**User:** {message.author.mention} (`{message.author.id}`)\n**Channel:** {message.channel.mention}\n**Reason:** Rapid external payload / script detected.\n**Content:** `{content[:200]}`",
                        color=0xFF0000
                    )
                    try:
                        await log_ch.send(embed=alert_embed)
                    except Exception:
                        pass

    # Anti-Abuse Filter Check
    if message.guild and guild_antiabuse_status.get(g_id, False):
        abuse_list = guild_abuse_words.get(g_id, [])
        content_lower = content.lower()
        if any(word in content_lower for word in abuse_list):
            try:
                dur = timedelta(minutes=60)
                await message.author.timeout(dur, reason="Forbidden abuse words detected.")
                await message.channel.send(embed=emb(title="⚠️ Anti-Abuse Triggered", description=f"{message.author.mention}, forbidden words are not allowed! Timeout given."))
                return
            except Exception:
                pass

    # Counting Game Check
    if g_id in guild_counting:
        c_data = guild_counting[g_id]
        if message.channel.id == c_data.get("channel_id"):
            try:
                number = int(content)
                expected = c_data.get("next_number", 1)
                last_user = c_data.get("last_user", 0)
                custom_emoji = c_data.get("emoji", "✅")
                
                if number == expected and u_id != last_user:
                    c_data["next_number"] = expected + 1
                    c_data["last_user"] = u_id
                    save_data()
                    try:
                        await message.add_reaction(custom_emoji)
                    except Exception:
                        await message.add_reaction("✅")
                else:
                    await message.channel.send(embed=emb(title="❌ Counting Failed", description=f"{message.author.mention}, wrong number! Reset back to `{expected}`."))
            except ValueError:
                pass

    # Message Counting Tracker
    if g_id not in user_messages: 
        user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    # AFK Auto-Clear
    if u_id in afk_users:
        afk_users.pop(u_id)
        await message.channel.send(embed=emb(title="Welcome Back", description=f"Welcome back, {message.author.mention}! Your AFK status has been cleared."))

    await bot.process_commands(message)

# ==================== DELETED MESSAGE RESTORER ====================

@bot.event
async def on_message_delete(message):
    if not message.guild or message.author.bot:
        return
    g_id = message.guild.id
    log_channel_id = guild_ghost_ping.get(g_id)
    if log_channel_id:
        ch = message.guild.get_channel(log_channel_id)
        if ch:
            content = message.content if message.content else "*[No Text Content / Embedded or Attachment]*"
            e = emb(
                title="🗑️ Deleted Message Restored",
                description=f"**Author:** {message.author.mention} (`{message.author.id}`)\n**Original Channel:** {message.channel.mention}\n**Restored Content:**\n{content}",
                color=0xFFA500
            )
            try:
                await ch.send(embed=e)
            except Exception:
                pass

# ==================== SETUP / LOGGING COMMANDS ====================

@bot.command(name="setcmdlog")
@commands.has_permissions(administrator=True)
async def set_command_log(ctx, channel: discord.TextChannel):
    guild_command_logs[ctx.guild.id] = channel.id
    save_data()
    await ctx.send(embed=emb(title="External Sniffer Log Setup", description=f"✅ External & command logs set to {channel.mention}."))

@bot.command(name="setdeletelog")
@commands.has_permissions(administrator=True)
async def set_delete_log(ctx, channel: discord.TextChannel):
    guild_ghost_ping[ctx.guild.id] = channel.id
    save_data()
    await ctx.send(embed=emb(title="Message Restorer Log Setup", description=f"✅ Deleted message restoration logs set to {channel.mention}."))

# ==================== MODERATION & ROLE COMMANDS ====================

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.ban(reason=reason)
        await ctx.send(embed=emb(title="User Banned", description=f"🔨 {member.mention} has been banned.\n**Reason:** {reason}"))
    except Exception as e:
        await ctx.send(embed=emb(title="Error", description=f"Could not ban member: {e}"))

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_user(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.kick(reason=reason)
        await ctx.send(embed=emb(title="User Kicked", description=f"👢 {member.mention} has been kicked.\n**Reason:** {reason}"))
    except Exception as e:
        await ctx.send(embed=emb(title="Error", description=f"Could not kick member: {e}"))

@bot.command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute_user(ctx, member: discord.Member, minutes: int = 10, *, reason: str = "No reason"):
    try:
        await member.timeout(timedelta(minutes=minutes), reason=reason)
        await ctx.send(embed=emb(title="User Muted", description=f"🔇 {member.mention} has been muted for `{minutes} minutes`.\n**Reason:** {reason}"))
    except Exception as e:
        await ctx.send(embed=emb(title="Error", description=f"Could not mute user: {e}"))

@bot.command(name="addrole", aliases=["giverole"])
@commands.has_permissions(manage_roles=True)
async def add_role(ctx, member: discord.Member, role: discord.Role, *, reason="No reason"):
    if ctx.author.top_role <= role and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=emb(title="Error", description="Aap is role ko assign nahi kar sakte kyunki ye aapke top role ke upar ya barabar hai!"))
    try:
        await member.add_roles(role, reason=reason)
        await ctx.send(embed=emb(title="Role Added", description=f"✅ Successfully added {role.mention} to {member.mention}.\n**Reason:** {reason}"))
    except Exception as e:
        await ctx.send(embed=emb(title="Error", description=f"Role add nahi ho saka: {e}"))

@bot.command(name="removerole", aliases=["takerole"])
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, member: discord.Member, role: discord.Role, *, reason="No reason"):
    if ctx.author.top_role <= role and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=emb(title="Error", description="Aap is role ko remove nahi kar sakte kyunki ye aapke top role ke upar ya barabar hai!"))
    try:
        await member.remove_roles(role, reason=reason)
        await ctx.send(embed=emb(title="Role Removed", description=f"❌ Successfully removed {role.mention} from {member.mention}.\n**Reason:** {reason}"))
    except Exception as e:
        await ctx.send(embed=emb(title="Error", description=f"Role remove nahi ho saka: {e}"))

@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def warn_user(ctx, member: discord.Member, *, reason="No reason"):
    g_id = ctx.guild.id
    if g_id not in guild_warns: 
        guild_warns[g_id] = {}
    m_id = str(member.id)
    if m_id not in guild_warns[g_id]: 
        guild_warns[g_id][m_id] = []
    guild_warns[g_id][m_id].append({"reason": reason, "moderator": ctx.author.id, "time": str(datetime.now())})
    save_data()
    await ctx.send(embed=emb(title="User Warned", description=f"⚠️ {member.mention} has been warned.\n**Reason:** {reason}"))

@bot.command(name="warnlist")
@commands.has_permissions(manage_messages=True)
async def warn_list(ctx, member: discord.Member):
    g_id = ctx.guild.id
    warns = guild_warns.get(g_id, {}).get(str(member.id), [])
    if not warns:
        return await ctx.send(embed=emb(title="Warn List", description=f"{member.mention} has no warnings."))
    desc = "\n".join([f"• **Reason:** {w['reason']} (By <@{w['moderator']}>)" for w in warns])
    await ctx.send(embed=emb(title=f"Warnings for {member.name}", description=desc))

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=emb(title="Channel Locked", description=f"🔒 {ch.mention} has been locked."))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=emb(title="Channel Unlocked", description=f"🔓 {ch.mention} has been unlocked."))

@bot.command(name="hide")
@commands.has_permissions(manage_channels=True)
async def hide_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, view_channel=False)
    await ctx.send(embed=emb(title="Channel Hidden", description=f"🔒 {ch.mention} has been hidden."))

@bot.command(name="unhide")
@commands.has_permissions(manage_channels=True)
async def unhide_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, view_channel=True)
    await ctx.send(embed=emb(title="Channel Unhidden", description=f"🔓 {ch.mention} is now visible."))

@bot.command(name="purge", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge_msgs(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=emb(title="Messages Cleared", description=f"Deleted {amount} messages successfully."))
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass

# ==================== STATS & LEADERBOARDS ====================

@bot.command(name="m", aliases=["messagecount"])
async def message_count_cmd(ctx, member: discord.Member = None):
    m = member or ctx.author
    g_id = ctx.guild.id
    count = user_messages.get(g_id, {}).get(str(m.id), 0)
    await ctx.send(embed=emb(title="Message Count", description=f"📊 {m.mention} has sent **{count}** messages."))

@bot.command(name="v", aliases=["voicetime"])
async def voice_time_cmd(ctx, member: discord.Member = None):
    m = member or ctx.author
    g_id = ctx.guild.id
    total_sec = user_voice_time.get(g_id, {}).get(str(m.id), 0)
    key = (g_id, m.id)
    if key in voice_joindata:
        total_sec += int(time.time() - voice_joindata[key])
    
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    await ctx.send(embed=emb(title="Voice Timing Count", description=f"🎙️ {m.mention} has spent **{hours}h {minutes}m** in voice channels."))

@bot.command(name="i", aliases=["invitecount"])
async def invite_count_cmd(ctx, member: discord.Member = None):
    m = member or ctx.author
    g_id = ctx.guild.id
    invs = user_invites.get(g_id, {}).get(str(m.id), {}).get("total", 0)
    await ctx.send(embed=emb(title="Invite Count", description=f"🎟️ {m.mention} has invited **{invs}** members."))

@bot.command(name="rm")
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, target: str):
    if target.lower() == "all":
        user_messages[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=emb(title="Reset Complete", description="🗑️ All message counters have been reset."))

@bot.command(name="rv")
@commands.has_permissions(administrator=True)
async def reset_voice(ctx, target: str):
    if target.lower() == "all":
        user_voice_time[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=emb(title="Reset Complete", description="🗑️ All voice time counters have been reset."))

@bot.command(name="ri")
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, target: str):
    if target.lower() == "all":
        user_invites[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=emb(title="Reset Complete", description="🗑️ All invite counters have been reset."))

@bot.command(name="lm", aliases=["leaderboard_msg"])
async def leaderboard_messages(ctx):
    g_id = ctx.guild.id
    m_data = user_messages.get(g_id, {})
    if not m_data: 
        return await ctx.send(embed=emb(title="Message Leaderboard", description="No data found."))
    sorted_users = sorted(m_data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "".join([f"`#{idx}` <@{uid}> — **{count}** msgs\n" for idx, (uid, count) in enumerate(sorted_users, 1)])
    await ctx.send(embed=emb(title="🏆 Message Leaderboard", description=desc))

@bot.command(name="lv", aliases=["leaderboard_voice"])
async def leaderboard_voice(ctx):
    g_id = ctx.guild.id
    v_data = user_voice_time.get(g_id, {})
    if not v_data: 
        return await ctx.send(embed=emb(title="Voice Leaderboard", description="No data found."))
    sorted_users = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = ""
    for idx, (uid, sec) in enumerate(sorted_users, 1):
        h, m = sec // 3600, (sec % 3600) // 60
        desc += f"`#{idx}` <@{uid}> — **{h}h {m}m**\n"
    await ctx.send(embed=emb(title="🏆 Voice Time Leaderboard", description=desc))

@bot.command(name="li", aliases=["leaderboard_invite"])
async def leaderboard_invites(ctx):
    g_id = ctx.guild.id
    i_data = user_invites.get(g_id, {})
    if not i_data: 
        return await ctx.send(embed=emb(title="Invite Leaderboard", description="No data found."))
    sorted_users = sorted(i_data.items(), key=lambda x: x[1].get("total", 0), reverse=True)[:10]
    desc = "".join([f"`#{idx}` <@{uid}> — **{data.get('total', 0)}** invites\n" for idx, (uid, data) in enumerate(sorted_users, 1)])
    await ctx.send(embed=emb(title="🏆 Invite Leaderboard", description=desc))

# ==================== UTILITY & FUN COMMANDS ====================

@bot.command(name="say")
@commands.has_permissions(manage_messages=True)
async def say_cmd(ctx, *, message: str):
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await ctx.send(message)

@bot.command(name="reply")
@commands.has_permissions(manage_messages=True)
async def reply_cmd(ctx, message_id: int, *, message: str):
    try:
        msg = await ctx.channel.fetch_message(message_id)
        await msg.reply(message)
        try:
            await ctx.message.delete()
        except Exception:
            pass
    except Exception as e:
        await ctx.send(embed=emb(title="Error", description=str(e)))

@bot.command(name="clone")
@commands.has_permissions(manage_channels=True)
async def clone_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    new_ch = await ch.clone(reason=f"Cloned by {ctx.author}")
    await ctx.send(embed=emb(title="Channel Cloned", description=f"✅ Cloned {ch.mention} into {new_ch.mention}!"))

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send(embed=emb(title="Bot Latency", description=f"Response time: `{round(bot.latency * 1000)}ms`"))

@bot.command(name="afk")
async def afk_cmd(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(embed=emb(title="AFK Activated", description=f"{ctx.author.mention} is now AFK.\n**Reason:** {reason}"))

@bot.command(name="giveaway")
@commands.has_permissions(manage_guild=True)
async def start_giveaway(ctx, minutes: int, *, prize: str):
    e = emb(title="🎉 GIVEAWAY 🎉", description=f"Prize: **{prize}**\nDuration: `{minutes} minutes`\nReact with 🎉 to enter!")
    msg = await ctx.send(embed=e)
    await msg.add_reaction("🎉")
    await asyncio.sleep(minutes * 60)
    try:
        new_msg = await ctx.channel.fetch_message(msg.id)
        users = [u async for u in new_msg.reactions[0].users() if not u.bot]
        if users:
            winner = random.choice(users)
            await ctx.send(embed=emb(title="🎉 Giveaway Ended!", description=f"Winner: {winner.mention} won **{prize}**! 🎁"))
        else:
            await ctx.send(embed=emb(title="🎉 Giveaway Ended!", description="No valid entries found."))
    except Exception as e:
        print(f"Giveaway error: {e}")

@bot.command(name="start", aliases=["counting"])
@commands.has_permissions(administrator=True)
async def start_counting(ctx, amount: int = 1, channel: discord.TextChannel = None, emoji: str = "✅"):
    target_channel = channel or ctx.channel
    guild_counting[ctx.guild.id] = {"channel_id": target_channel.id, "next_number": amount, "last_user": 0, "emoji": emoji}
    save_data()
    await ctx.send(embed=emb(title="Counting Initialized", description=f"Started counting in {target_channel.mention} at number `{amount}`."))

@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, prefix: str):
    guild_prefixes[ctx.guild.id] = prefix
    save_data()
    await ctx.send(embed=emb(title="Prefix Updated", description=f"New server prefix has been set to: `{prefix}`"))

# ==================== HELP MENU SYSTEM ====================

class MenuSelect(discord.ui.Select):
    def __init__(self, prefix):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Moderation", description="Ban, kick, mute, addrole, removerole, lock/unlock", emoji="🛠️"),
            discord.SelectOption(label="Security & Sniffers", description="External Sniffer, Message Restorer, Anti-Abuse", emoji="🛡️️"),
            discord.SelectOption(label="Stats & Trackers", description="Message, voice & invite stats/leaderboards", emoji="📊"),
            discord.SelectOption(label="Utility & Fun", description="Ping, afk, say, reply, clone, giveaway", emoji="🎉")
        ]
        super().__init__(placeholder="CHOOSE A MODULE", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        p = self.prefix
        choice = self.values[0]
        if choice == "Moderation":
            desc = f"• `{p}ban` | `{p}kick` | `{p}mute`\n• `{p}addrole` | `{p}removerole`\n• `{p}lock` | `{p}unlock` | `{p}purge`\n• `{p}hide` | `{p}unhide`"
        elif choice == "Security & Sniffers":
            desc = f"• `{p}setcmdlog` (External Sniffer)\n• `{p}setdeletelog` (Message Restorer)\n• `{p}antiabuse` | `{p}addabuse` | `{p}warn`"
        elif choice == "Stats & Trackers":
            desc = f"• `{p}m` | `{p}v` | `{p}i` (Counts)\n• `{p}lm` | `{p}lv` | `{p}li` (Leaderboards)\n• `{p}rm all` | `{p}rv all` | `{p}ri all` (Resets)"
        else:
            desc = f"• `{p}say` | `{p}reply` | `{p}clone`\n• `{p}start` (Counting) | `{p}giveaway` | `{p}ping`"
        await interaction.response.edit_message(embed=emb(title=f"Module: {choice}", description=desc), view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="help", aliases=["cmds", "menu"])
async def help_command(ctx):
    p = ctx.prefix
    desc = f"Hey, I'm Moonlight Heaven™ Control Panel\nPrefix: `{p}`\nSelect a category below to explore commands:"
    e = discord.Embed(title="🤖 Moonlight Heaven Control Center", description=desc, color=0xFFFFFF)
    e.set_thumbnail(url=DEFAULT_THUMBNAIL)
    e.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=e, view=MenuView(p))

# ==================== BOT STARTUP ====================
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Error: TOKEN environment variable nahi mila! Kripya apna bot token set karein.")
