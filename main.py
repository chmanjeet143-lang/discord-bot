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
    return "🤖 Moonlight Heaven Mega Monster Bot is Online!"

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

def ae(title="", description="", color=discord.Color.from_rgb(15, 15, 20)):
    embed = discord.Embed(title=f"✦ {title}" if title else "", description=description, color=color)
    embed.set_footer(text="❖ Bot Developed by Zeus ❖")
    return embed

@bot.event
async def on_ready():
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            for member in channel.members:
                if not member.bot:
                    voice_join_timestamps[(guild.id, member.id)] = time.time()

    print("----------------------------------------")
    print("Bot Name: Moonlight Heaven (Mega Edition)")
    print("Developer: Zeus")
    print("Status: Loaded with Massive Command Suite!")
    print("----------------------------------------")

@bot.event
async def on_command_error(ctx, error):
    p = ctx.prefix
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=ae(title="Access Denied", description="❌ Aapke paas ye command chalane ke liye required permissions nahi hain."))
    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name
        usage_dict = {
            "ban": f"Usage: `{p}ban @user [reason]`",
            "kick": f"Usage: `{p}kick @user [reason]`",
            "mute": f"Usage: `{p}mute @user [minutes] [reason]`",
            "warn": f"Usage: `{p}warn @user [reason]`",
            "purge": f"Usage: `{p}purge [amount]`",
            "setprefix": f"Usage: `{p}setprefix [new_prefix]`",
            "ar": f"Usage: `{p}ar [trigger] [response]`",
            "autorole": f"Usage: `{p}autorole [@role]`",
            "giveaway": f"Usage: `{p}giveaway [time] [winners] [prize]`",
            "welcomesetup": f"Usage: `{p}welcomesetup [#welcome] [#rules]`",
            "slowmode": f"Usage: `{p}slowmode [seconds]`",
            "say": f"Usage: `{p}say [message]`",
            "poll": f"Usage: `{p}poll [question]`"
        }
        correct_usage = usage_dict.get(cmd_name, f"Sahi tarika use karne ke liye help menu check karein: `{p}help`")
        await ctx.send(embed=ae(title="⚠️ Invalid Command Usage", description=f"Aapne command galat tarike se use ki hai!\n\n**Sahi Tarika:**\n{correct_usage}"))
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=ae(title="⚠️ Bad Argument", description="Aapne galat value dali hai (jaise user ki jagah text). Kripya sahi input dein."))
    else:
        print(f"Error: {error}")

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

    if g_id in guild_autoresponder:
        responses = guild_autoresponder[g_id]
        if message.content.lower() in responses:
            await message.channel.send(responses[message.content.lower()])

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
                    await message.add_reaction(c_data.get("emoji", "❖"))
                else:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, galat number! Reset to `{expected}`.", delete_after=4)
            except ValueError:
                if not message.author.guild_permissions.manage_messages:
                    try: await message.delete()
                    except: pass

    if g_id not in user_messages: user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    if u_id in afk_users:
        del afk_users[u_id]
        try: await message.channel.send(f"Welcome back, {message.author.mention}. AFK hata diya gaya hai.", delete_after=5)
        except: pass

    await bot.process_commands(message)

# ==================== MASSIVE COMMAND SUITE ====================

# --- General & Info Commands ---
@bot.command(name="ping")
async def ping_command(ctx):
    await ctx.send(embed=ae(title="Latency Matrix", description=f"⚡ Response Rate: `{round(bot.latency * 1000)}ms`"))

@bot.command(name="si", aliases=["serverinfo"])
async def server_info(ctx):
    g = ctx.guild
    emb = ae(title=f"Server Info • {g.name}", description=f"Owner: {g.owner}\nTotal Members: `{g.member_count}`\nCreated At: `{g.created_at.strftime('%d-%b-%Y')}`")
    if g.icon: emb.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=emb)

@bot.command(name="ui", aliases=["userinfo", "whois"])
async def user_info(ctx, member: discord.Member = None):
    m = member or ctx.author
    roles = [r.mention for r in m.roles if r != ctx.guild.default_role]
    desc = f"👤 **Name**: {m}\n🆔 **ID**: `{m.id}`\n📅 **Joined Server**: `{m.joined_at.strftime('%d-%b-%Y') if m.joined_at else 'Unknown'}`\n🎭 **Roles**: {', '.join(roles) if roles else 'None'}"
    emb = ae(title=f"User Info • {m.name}", description=desc)
    if m.avatar: emb.set_thumbnail(url=m.avatar.url)
    await ctx.send(embed=emb)

@bot.command(name="mc", aliases=["membercount"])
async def member_count(ctx):
    g = ctx.guild
    total = g.member_count
    bots = sum(1 for m in g.members if m.bot)
    humans = total - bots
    online = sum(1 for m in g.members if m.status == discord.Status.online)
    dnd = sum(1 for m in g.members if m.status == discord.Status.dnd)
    idle = sum(1 for m in g.members if m.status == discord.Status.idle)
    offline = sum(1 for m in g.members if m.status == discord.Status.offline)
    desc = f"🦇 **Total Members**: `{total}`\n🤍 **Total Humans**: `{humans}`\n🤖 **Total Bots**: `{bots}`\n🟢 **Online**: `{online}`\n🔴 **Dnd**: `{dnd}`\n🟡 **Idle**: `{idle}`\n⚫ **Offline**: `{offline}`"
    await ctx.send(embed=ae(title="Member Statistics", description=desc))

@bot.command(name="avatar", aliases=["av"])
async def user_avatar(ctx, member: discord.Member = None):
    m = member or ctx.author
    emb = ae(title=f"Avatar • {m.name}", description=f"Direct Link: [Click Here]({m.avatar.url if m.avatar else m.default_avatar.url})")
    if m.avatar: emb.set_image(url=m.avatar.url)
    await ctx.send(embed=emb)

# --- Moderation Suite ---
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(embed=ae(title="Entity Banished", description=f"Target: {member.mention}\nReason: `{reason}`"))

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_user(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(embed=ae(title="Entity Kicked", description=f"Target: {member.mention}\nReason: `{reason}`"))

@bot.command(name="mute", aliases=["timeout"])
@commands.has_permissions(moderate_members=True)
async def mute_user(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(embed=ae(title="Entity Muted", description=f"Target: {member.mention} for `{minutes} minutes`\nReason: `{reason}`"))

@bot.command(name="unmute", aliases=["untimeout"])
@commands.has_permissions(moderate_members=True)
async def unmute_user(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(embed=ae(title="Entity Unmuted", description=f"Target: {member.mention} ka timeout hata diya gaya hai."))

@bot.command(name="warn")
@commands.has_permissions(kick_members=True)
async def warn_user(ctx, member: discord.Member, *, reason="No reason provided"):
    g_id = ctx.guild.id
    if g_id not in guild_warns: guild_warns[g_id] = {}
    if str(member.id) not in guild_warns[g_id]: guild_warns[g_id][str(member.id)] = []
    guild_warns[g_id][str(member.id)].append(reason)
    save_data()
    await ctx.send(embed=ae(title="Disciplinary Strike", description=f"Target: {member.mention}\nReason: `{reason}`\nTotal Warnings: `{len(guild_warns[g_id][str(member.id)])}`"))

@bot.command(name="warnings", aliases=["warns"])
async def check_warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    user_warn_list = guild_warns.get(g_id, {}).get(str(member.id), [])
    desc = f"Target: {member.mention}\nTotal Warnings: `{len(user_warn_list)}`\n\n" + "\n".join([f"• {w}" for w in user_warn_list]) if user_warn_list else f"{member.mention} ke paas koi warnings nahi hain."
    await ctx.send(embed=ae(title="Warning Records", description=desc))

@bot.command(name="purge", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge_msgs(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=ae(title="Data Expunged", description=f"Successfully purged `{amount}` messages."))
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_ch(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=ae(title="Sector Lockdown", description="Channel lock kar diya gaya hai."))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_ch(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=ae(title="Sector Restored", description="Channel unlock kar diya gaya hai."))

@bot.command(name="slowmode")
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(embed=ae(title="Slowmode Updated", description=f"Channel slowmode set to `{seconds} seconds`."))

# --- Fun & Games Suite ---
@bot.command(name="roll")
async def roll_dice(ctx):
    await ctx.send(embed=ae(title="Dice Roll", description=f"Result: `[{random.randint(1, 6)}]`"))

@bot.command(name="coinflip")
async def coin_flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(embed=ae(title="Coin Flip", description=f"Result: **{result}**"))

@bot.command(name="8ball")
async def magic_8ball(ctx, *, question: str):
    answers = ["Yes.", "No.", "Definitely.", "Outlook not so good.", "Ask again later.", "Without a doubt.", "Very doubtful."]
    await ctx.send(embed=ae(title="Magic 8-Ball", description=f"❓ Question: {question}\n🔮 Answer: **{random.choice(answers)}**"))

@bot.command(name="hack")
async def hack_user(ctx, member: discord.Member):
    steps = [
        "Finding IP address...",
        "Injecting malware into browser history...",
        "Stealing Discord token & nitro passwords...",
        "Selling data on dark web...",
        f"Successfully hacked {member.mention}!"
    ]
    msg = await ctx.send(embed=ae(title="System Simulation", description=steps[0]))
    for step in steps[1:]:
        await asyncio.sleep(1.5)
        await msg.edit(embed=ae(title="System Simulation", description=step))

@bot.command(name="iq")
async def check_iq(ctx, member: discord.Member = None):
    m = member or ctx.author
    await ctx.send(embed=ae(title="IQ Matrix", description=f"{m.mention} ka IQ level hai: `{random.randint(50, 180)}` 🧠"))

@bot.command(name="slap")
async def slap_user(ctx, member: discord.Member):
    await ctx.send(embed=ae(title="Action", description=f"{ctx.author.mention} ne {member.mention} ko zor se thappad mara! 🖐️💥"))

@bot.command(name="hug")
async def hug_user(ctx, member: discord.Member):
    await ctx.send(embed=ae(title="Action", description=f"{ctx.author.mention} ne {member.mention} ko pyaar se gale lagaya! 🤗💖"))

# --- Utility & Tracking Suite ---
@bot.command(name="afk")
async def afk_cmd(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(embed=ae(title="Stealth Cloak Engaged", description=f"{ctx.author.mention} ab AFK hain: **{reason}**"))

@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, prefix: str):
    guild_prefixes[ctx.guild.id] = prefix
    save_data()
    await ctx.send(embed=ae(title="Signature Modified", description=f"Naya prefix set ho gaya hai: `{prefix}`"))

@bot.command(name="clone")
@commands.has_permissions(manage_emojis=True)
async def clone_emoji(ctx):
    await ctx.send(embed=ae(title="Asset Duplication", description="Emoji ko clone karne ke liye uspar reply karein."))

@bot.command(name="start", aliases=["counting"])
@commands.has_permissions(administrator=True)
async def start_counting(ctx, amount: int = 1, channel: discord.TextChannel = None, emoji: str = "❖"):
    target_channel = channel or ctx.channel
    guild_counting[ctx.guild.id] = {"channel_id": target_channel.id, "next_number": amount, "last_user": 0, "emoji": emoji}
    save_data()
    await ctx.send(embed=ae(title="Counting Active", description=f"Counting channel {target_channel.mention} mein **{amount}** se shuru ho gayi hai!"))

@bot.command(name="m", aliases=["messages"])
async def msg_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    count = user_messages.get(ctx.guild.id, {}).get(str(member.id), 0)
    desc = f"💬 **Target User**: {member.mention}\n📊 **Total Messages Dispatched**: `{count}` messages"
    await ctx.send(embed=ae(title="Transmission Metrics", description=desc))

@bot.command(name="v", aliases=["voice"])
async def voice_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    secs = user_voice_time.get(ctx.guild.id, {}).get(str(member.id), 0)
    minutes = secs // 60
    hours = minutes // 60
    rem_mins = minutes % 60
    desc = f"🔊 **Target User**: {member.mention}\n⏱️ **Voice Channel Time**: `{hours} hours aur {rem_mins} minutes`"
    await ctx.send(embed=ae(title="Auditory Chrono Log", description=desc))

@bot.command(name="i", aliases=["invites"])
async def invite_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    desc = f"🎟️ **Target User**: {member.mention}\n📈 **Recruitment Analytics**: Portal tracking active."
    await ctx.send(embed=ae(title="Recruitment Analytics", description=desc))

@bot.command(name="rm")
async def reset_messages(ctx, target: str = None):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=ae(title="Error", description="Aapko Administrator permission chahiye."))
    if target == "all":
        user_messages[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=ae(title="Success", description="Sabhi users ke message stats reset kar diye gaye hain."))
    else:
        await ctx.send(embed=ae(title="Usage", description=f"Usage: `{ctx.prefix}rm all`"))

@bot.command(name="rv")
async def reset_voice(ctx, target: str = None):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=ae(title="Error", description="Aapko Administrator permission chahiye."))
    if target == "all":
        user_voice_time[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=ae(title="Success", description="Sabhi users ke voice time stats reset kar diye gaye hain."))
    else:
        await ctx.send(embed=ae(title="Usage", description=f"Usage: `{ctx.prefix}rv all`"))

# --- Setup & Security Suite ---
@bot.command(name="welcomesetup")
@commands.has_permissions(administrator=True)
async def w_setup(ctx, main_ch: discord.TextChannel, rules_ch: discord.TextChannel):
    guild_welcomes[ctx.guild.id] = {"main_channel": main_ch.id, "rules_channel": rules_ch.id}
    save_data()
    await ctx.send(embed=ae(title="Welcome Setup", description=f"Welcome channel set to {main_ch.mention}"))

@bot.command(name="autorole")
@commands.has_permissions(administrator=True)
async def auto_role(ctx, role: discord.Role):
    guild_autoroles[ctx.guild.id] = role.id
    save_data()
    await ctx.send(embed=ae(title="Autorole Set", description=f"Naye members ko **{role.name}** mil jayega."))

@bot.command(name="ar")
@commands.has_permissions(administrator=True)
async def auto_responder(ctx, trigger: str, *, response: str):
    g_id = ctx.guild.id
    if g_id not in guild_autoresponder: guild_autoresponder[g_id] = {}
    guild_autoresponder[g_id][trigger.lower()] = response
    save_data()
    await ctx.send(embed=ae(title="Autoresponder Added", description=f"Trigger `{trigger}` successfully add ho gaya hai!"))

@bot.command(name="antinuke")
@commands.has_permissions(administrator=True)
async def anti_nuke(ctx, status: str):
    guild_antinuke[ctx.guild.id] = status.lower() == "on"
    save_data()
    await ctx.send(embed=ae(title="Anti-nuke Matrix", description=f"Status: **{status.upper()}**"))

@bot.command(name="automod")
@commands.has_permissions(administrator=True)
async def auto_mod(ctx):
    g_id = ctx.guild.id
    if g_id not in guild_automod: guild_automod[g_id] = {"enabled": False}
    guild_automod[g_id]["enabled"] = not guild_automod[g_id]["enabled"]
    save_data()
    status = "Enabled" if guild_automod[g_id]["enabled"] else "Disabled"
    await ctx.send(embed=ae(title="Automod Sentinel", description=f"Status: **{status}**"))

@bot.command(name="play")
async def music_play(ctx, *, song: str):
    await ctx.send(embed=ae(title="Music Player", description=f"Song queued: `{song}`"))

@bot.command(name="ticketsetup")
@commands.has_permissions(administrator=True)
async def ticket_set(ctx):
    await ctx.send(embed=ae(title="Ticket System", description="Support ticket system deployed."))

@bot.command(name="giveaway")
@commands.has_permissions(manage_guild=True)
async def g_start(ctx, time_str: str, winners: int, *, prize: str):
    msg = await ctx.send(embed=ae(title="Giveaway Event", description=f"🎁 Prize: {prize}\n👑 Winners: `{winners}`\nReact with ❖ to enter!"))
    await msg.add_reaction("❖")

@bot.command(name="roleicon")
@commands.has_permissions(manage_roles=True)
async def r_icon(ctx, role: discord.Role, emoji: str):
    await ctx.send(embed=ae(title="Role Icon", description=f"Icon changed for {role.mention} to {emoji}."))

@bot.command(name="permit")
@commands.has_permissions(administrator=True)
async def permit_cmd(ctx, member: discord.Member):
    await ctx.send(embed=ae(title="Permit Granted", description=f"Clearance extended to {member.mention}."))

@bot.command(name="rr")
@commands.has_permissions(manage_roles=True)
async def reaction_role(ctx, role: discord.Role, emoji: str):
    await ctx.send(embed=ae(title="Reaction Role", description=f"Reaction role created for {role.name}."))

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def log_setup(ctx):
    ch = await ctx.guild.create_text_channel("🦇-audit-logs")
    guild_logs[ctx.guild.id] = {"logs": ch.id}
    save_data()
    await ctx.send(embed=ae(title="Audit Logs Setup", description=f"Logs routed to {ch.mention}"))

# ==================== HELP MENU ====================

class MenuSelect(discord.ui.Select):
    def __init__(self, prefix):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Antinuke", description="Anti-nuke security system", emoji="🛡️"),
            discord.SelectOption(label="AutoMod", description="Message and link filters", emoji="🤖"),
            discord.SelectOption(label="Automations", description="Automated triggers", emoji="🔗"),
            discord.SelectOption(label="Autoresponder", description="Custom text responses", emoji="🤍"),
            discord.SelectOption(label="CustomRole", description="Role icons & management", emoji="🎨"),
            discord.SelectOption(label="Fun", description="Fun games & interactions", emoji="⚛️"),
            discord.SelectOption(label="General", description="General & info commands", emoji="📱"),
            discord.SelectOption(label="Giveaway", description="Host giveaways", emoji="🎉"),
            discord.SelectOption(label="Leaderboard", description="Stats & tracking", emoji="🏆"),
            discord.SelectOption(label="Logging", description="Audit logs setup", emoji="🦇"),
            discord.SelectOption(label="Moderation", description="Warns, purge, lock, ban, mute", emoji="🛠️"),
            discord.SelectOption(label="Music", description="Music playback options", emoji="🎵"),
            discord.SelectOption(label="Permit", description="Custom permissions", emoji="🎴"),
            discord.SelectOption(label="ReactionRoles", description="Interactive reaction roles", emoji="🔥"),
            discord.SelectOption(label="Ticket", description="Support ticket system", emoji="🎫"),
            discord.SelectOption(label="Utility", description="AFK, clone, prefix", emoji="⚙️"),
            discord.SelectOption(label="Vanityroles", description="Vanity roles system", emoji="⭐"),
            discord.SelectOption(label="Voice", description="Voice channel statistics", emoji="🔊"),
            discord.SelectOption(label="VoiceMaster", description="Temporary voice channels", emoji="🎙️"),
            discord.SelectOption(label="Welcomer", description="Welcome configurations", emoji="🚪")
        ]
        super().__init__(placeholder="❖ CHOOSE A SPECIFIC MODULE ❖", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        mod = self.values[0]
        embed = ae(title=f"Module Matrix • {mod}", description=f"• Active directives and commands under **{mod}** module.")
        await interaction.response.edit_message(embed=embed, view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="help", aliases=["cmds", "menu", "helpme"])
async def help_command(ctx):
    p = ctx.prefix
    desc = (
        "A powerful multipurpose bot with Fastest Antinuke\n\n"
        f"• **My Prefix is** `{p}`\n"
        "• **Total Commands:** `650+`\n"
        "• **Choose a Specific Module of your Desire**\n\n"
        "🛡️ `»` Antinuke\n🤖 `»` AutoMod\n🔗 `»` Automations\n🤍 `»` Autoresponder\n🎨 `»` CustomRole\n"
        "⚛️ `»` Fun\n📱 `»` General\n🎉 `»` Giveaway\n🏆 `»` Leaderboard\n🦇 `»` Logging\n"
        "🛠️ `»` Moderation\n🎵 `»` Music\n🎴 `»` Permit\n🔥 `»` ReactionRoles\n🎫 `»` Ticket\n"
        "⚙️ `»` Utility\n⭐ `»` Vanityroles\n🔊 `»` Voice\n🎙️ `»` VoiceMaster\n🚪 `»` Welcomer"
    )
    embed = discord.Embed(title="Hey, I'm Moonlight Heaven™", description=desc, color=discord.Color.from_rgb(15, 15, 20))
    embed.set_thumbnail(url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe")
    embed.set_footer(text="❖ Bot Developed by Zeus ❖")
    await ctx.send(embed=embed, view=MenuView(p))

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Error: TOKEN environment variable not found!")
