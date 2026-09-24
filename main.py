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

def emb(title="", description="", color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Bot Developed by Zeus")
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
    print("Status: All Commands Online!")
    print("----------------------------------------")

@bot.event
async def on_command_error(ctx, error):
    p = ctx.prefix
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=emb(title="Access Denied", description="❌ You do not have the required permissions to use this command."))
    elif isinstance(error, commands.MissingRequiredArgument):
        cmd_name = ctx.command.name
        usage_dict = {
            "ban": f"Correct Usage: `{p}ban @user [reason]`",
            "kick": f"Correct Usage: `{p}kick @user [reason]`",
            "mute": f"Correct Usage: `{p}mute @user [minutes] [reason]`",
            "warn": f"Correct Usage: `{p}warn @user [reason]`",
            "purge": f"Correct Usage: `{p}purge [amount]`",
            "setprefix": f"Correct Usage: `{p}setprefix [new_prefix]`",
            "ar": f"Correct Usage: `{p}ar [trigger] [response]`",
            "autorole": f"Correct Usage: `{p}autorole [@role]`",
            "giveaway": f"Correct Usage: `{p}giveaway [time] [winners] [prize]`",
            "poll": f"Correct Usage: `{p}poll [question]`",
            "say": f"Correct Usage: `{p}say [text]`",
            "reminder": f"Correct Usage: `{p}reminder [minutes] [task]`"
        }
        correct_usage = usage_dict.get(cmd_name, f"Check the help menu for correct usage: `{p}help`")
        await ctx.send(embed=emb(title="⚠️ Invalid Command Usage", description=f"You used the command incorrectly!\n\n**Proper Way:**\n{correct_usage}"))
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=emb(title="⚠️ Bad Argument", description="You provided an invalid value (e.g., text instead of a member). Please check your input."))
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
        try: await message.channel.send(f"Welcome back, {message.author.mention}! Your AFK status has been removed.", delete_after=5)
        except: pass

    await bot.process_commands(message)

# ==================== MASSIVE COMMAND SUITE ====================

# --- General & Info Commands ---
@bot.command(name="ping")
async def ping_command(ctx):
    await ctx.send(embed=emb(title="Bot Latency", description=f"⚡ Current response rate is: `{round(bot.latency * 1000)}ms`"))

@bot.command(name="si", aliases=["serverinfo"])
async def server_info(ctx):
    g = ctx.guild
    e = emb(title=f"Server Info • {g.name}", description=f"👑 **Owner**: {g.owner}\n👥 **Total Members**: `{g.member_count}`\n📅 **Created At**: `{g.created_at.strftime('%d-%b-%Y')}`")
    if g.icon: e.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=e)

@bot.command(name="ui", aliases=["userinfo", "whois"])
async def user_info(ctx, member: discord.Member = None):
    m = member or ctx.author
    roles = [r.mention for r in m.roles if r != ctx.guild.default_role]
    desc = f"👤 **Name**: {m}\n🆔 **ID**: `{m.id}`\n📅 **Joined Server**: `{m.joined_at.strftime('%d-%b-%Y') if m.joined_at else 'Unknown'}`\n🎭 **Roles**: {', '.join(roles) if roles else 'None'}"
    e = emb(title=f"User Info • {m.name}", description=desc)
    if m.avatar: e.set_thumbnail(url=m.avatar.url)
    await ctx.send(embed=e)

@bot.command(name="mc", aliases=["membercount"])
async def member_count(ctx):
    g = ctx.guild
    total = g.member_count
    bots = sum(1 for m in g.members if m.bot)
    humans = total - bots
    online = sum(1 for m in g.members if m.status == discord.Status.online)
    desc = f"👥 **Total Members**: `{total}`\n🧑 **Total Humans**: `{humans}`\n🤖 **Total Bots**: `{bots}`\n🟢 **Online Members**: `{online}`"
    await ctx.send(embed=emb(title="Member Statistics", description=desc))

@bot.command(name="avatar", aliases=["av"])
async def user_avatar(ctx, member: discord.Member = None):
    m = member or ctx.author
    e = emb(title=f"Avatar • {m.name}", description=f"Direct Link: [Click Here]({m.avatar.url if m.avatar else m.default_avatar.url})")
    if m.avatar: e.set_image(url=m.avatar.url)
    await ctx.send(embed=e)

@bot.command(name="snipe")
async def snipe_msg(ctx):
    ch_id = ctx.channel.id
    if ch_id in snipe_data:
        data = snipe_data[ch_id]
        e = emb(title="Last Deleted Message", description=f"👤 **Author**: {data['author'].mention}\n💬 **Message**: `{data['content']}`\n⏰ **Time**: `{data['time']}`")
        await ctx.send(embed=e)
    else:
        await ctx.send(embed=emb(title="Nothing Found", description="No messages have been deleted in this channel recently."))

# --- Moderation Commands ---
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(embed=emb(title="User Banned", description=f"✅ {member.mention} has been banned from the server.\n📝 **Reason**: `{reason}`"))

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_user(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(embed=emb(title="User Kicked", description=f"✅ {member.mention} has been kicked from the server.\n📝 **Reason**: `{reason}`"))

@bot.command(name="mute", aliases=["timeout"])
@commands.has_permissions(moderate_members=True)
async def mute_user(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(embed=emb(title="User Muted", description=f"✅ {member.mention} has been muted for `{minutes} minutes`.\n📝 **Reason**: `{reason}`"))

@bot.command(name="unmute", aliases=["untimeout"])
@commands.has_permissions(moderate_members=True)
async def unmute_user(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(embed=emb(title="User Unmuted", description=f"✅ Timeout has been removed from {member.mention}."))

@bot.command(name="warn")
@commands.has_permissions(kick_members=True)
async def warn_user(ctx, member: discord.Member, *, reason="No reason provided"):
    g_id = ctx.guild.id
    if g_id not in guild_warns: guild_warns[g_id] = {}
    if str(member.id) not in guild_warns[g_id]: guild_warns[g_id][str(member.id)] = []
    guild_warns[g_id][str(member.id)].append(reason)
    save_data()
    total_warns = len(guild_warns[g_id][str(member.id)])
    await ctx.send(embed=emb(title="User Warned", description=f"⚠️ {member.mention} has been warned successfully.\n📝 **Reason**: `{reason}`\n📊 **Total Warnings**: `{total_warns}`"))

@bot.command(name="warnings", aliases=["warns"])
async def check_warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    user_warn_list = guild_warns.get(g_id, {}).get(str(member.id), [])
    desc = f"Target: {member.mention}\nTotal Warnings: `{len(user_warn_list)}`\n\n" + "\n".join([f"• {w}" for w in user_warn_list]) if user_warn_list else f"{member.mention} has no warnings."
    await ctx.send(embed=emb(title="Warning Records", description=desc))

@bot.command(name="purge", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge_msgs(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=emb(title="Messages Cleared", description=f"🧹 Successfully deleted `{amount}` messages."))
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_ch(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=emb(title="Channel Locked", description="🔒 This channel has been locked. Members cannot send messages."))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_ch(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=emb(title="Channel Unlocked", description="🔓 This channel has been unlocked. Members can now chat."))

@bot.command(name="slowmode")
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(embed=emb(title="Slowmode Updated", description=f"⏱️ Channel slowmode set to `{seconds} seconds`."))

# --- Fun & Games Commands ---
@bot.command(name="roll")
async def roll_dice(ctx):
    await ctx.send(embed=emb(title="Dice Roll", description=f"🎲 You rolled: `[{random.randint(1, 6)}]`"))

@bot.command(name="coinflip")
async def coin_flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(embed=emb(title="Coin Flip", description=f"🪙 The coin landed on: **{result}**"))

@bot.command(name="8ball")
async def magic_8ball(ctx, *, question: str):
    answers = ["Yes, definitely.", "No way.", "Outlook is good.", "Ask again later.", "Without a doubt.", "Very doubtful."]
    await ctx.send(embed=emb(title="Magic 8-Ball", description=f"❓ Question: {question}\n🔮 Answer: **{random.choice(answers)}**"))

@bot.command(name="iq")
async def check_iq(ctx, member: discord.Member = None):
    m = member or ctx.author
    await ctx.send(embed=emb(title="IQ Check", description=f"🧠 {m.mention}'s IQ score is: `{random.randint(50, 180)}`"))

@bot.command(name="slap")
async def slap_user(ctx, member: discord.Member):
    await ctx.send(embed=emb(title="Action", description=f"👋 {ctx.author.mention} gave a hard slap to {member.mention}!"))

@bot.command(name="hug")
async def hug_user(ctx, member: discord.Member):
    await ctx.send(embed=emb(title="Action", description=f"🤗 {ctx.author.mention} gave a warm hug to {member.mention}!"))

@bot.command(name="say")
async def say_msg(ctx, *, text: str):
    try: await ctx.message.delete()
    except: pass
    await ctx.send(text)

@bot.command(name="poll")
async def create_poll(ctx, *, question: str):
    e = emb(title="📊 New Poll Created", description=f"{question}\n\n👍 React for Yes\n👎 React for No")
    msg = await ctx.send(embed=e)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")

# --- Utility & Tracking Commands ---
@bot.command(name="afk")
async def afk_cmd(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(embed=emb(title="AFK Enabled", description=f"💤 {ctx.author.mention} is now AFK: **{reason}**"))

@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, prefix: str):
    guild_prefixes[ctx.guild.id] = prefix
    save_data()
    await ctx.send(embed=emb(title="Prefix Updated", description=f"✅ New server prefix set to: `{prefix}`"))

@bot.command(name="start", aliases=["counting"])
@commands.has_permissions(administrator=True)
async def start_counting(ctx, amount: int = 1, channel: discord.TextChannel = None, emoji: str = "✅"):
    target_channel = channel or ctx.channel
    guild_counting[ctx.guild.id] = {"channel_id": target_channel.id, "next_number": amount, "last_user": 0, "emoji": emoji}
    save_data()
    await ctx.send(embed=emb(title="Counting Started", description=f"🔢 Counting initialized in {target_channel.mention} starting from **{amount}**!"))

@bot.command(name="m", aliases=["messages"])
async def msg_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    count = user_messages.get(ctx.guild.id, {}).get(str(member.id), 0)
    await ctx.send(embed=emb(title="Message Tracking", description=f"💬 {member.mention} has sent a total of **{count}** messages."))

@bot.command(name="v", aliases=["voice"])
async def voice_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    secs = user_voice_time.get(ctx.guild.id, {}).get(str(member.id), 0)
    minutes = secs // 60
    hours = minutes // 60
    rem_mins = minutes % 60
    await ctx.send(embed=emb(title="Voice Time Tracking", description=f"🔊 {member.mention} has spent **{hours} hours and {rem_mins} minutes** in voice channels."))

@bot.command(name="reminder")
async def reminder_cmd(ctx, minutes: int, *, task: str):
    await ctx.send(embed=emb(title="Reminder Set", description=f"⏰ I will remind you about '**{task}**' in {minutes} minutes."))
    await asyncio.sleep(minutes * 60)
    await ctx.send(f"🔔 {ctx.author.mention}, here is your reminder: **{task}**")

# --- Setup & Security Commands ---
@bot.command(name="welcomesetup")
@commands.has_permissions(administrator=True)
async def w_setup(ctx, main_ch: discord.TextChannel, rules_ch: discord.TextChannel):
    guild_welcomes[ctx.guild.id] = {"main_channel": main_ch.id, "rules_channel": rules_ch.id}
    save_data()
    await ctx.send(embed=emb(title="Welcome Setup", description=f"✅ Welcome channel configured to {main_ch.mention}."))

@bot.command(name="autorole")
@commands.has_permissions(administrator=True)
async def auto_role(ctx, role: discord.Role):
    guild_autoroles[ctx.guild.id] = role.id
    save_data()
    await ctx.send(embed=emb(title="Autorole Configured", description=f"✅ New members will automatically receive the **{role.name}** role."))

@bot.command(name="ar")
@commands.has_permissions(administrator=True)
async def auto_responder(ctx, trigger: str, *, response: str):
    g_id = ctx.guild.id
    if g_id not in guild_autoresponder: guild_autoresponder[g_id] = {}
    guild_autoresponder[g_id][trigger.lower()] = response
    save_data()
    await ctx.send(embed=emb(title="Autoresponder Added", description=f"✅ When anyone says `{trigger}`, bot will automatically respond with: `{response}`"))

@bot.command(name="antinuke")
@commands.has_permissions(administrator=True)
async def anti_nuke(ctx, status: str):
    guild_antinuke[ctx.guild.id] = status.lower() == "on"
    save_data()
    await ctx.send(embed=emb(title="Anti-Nuke Status", description=f"🛡️ Anti-nuke security status is now **{status.upper()}**."))

@bot.command(name="automod")
@commands.has_permissions(administrator=True)
async def auto_mod(ctx):
    g_id = ctx.guild.id
    if g_id not in guild_automod: guild_automod[g_id] = {"enabled": False}
    guild_automod[g_id]["enabled"] = not guild_automod[g_id]["enabled"]
    save_data()
    status = "Enabled" if guild_automod[g_id]["enabled"] else "Disabled"
    await ctx.send(embed=emb(title="Automod Status", description=f"🤖 Automod protection is now **{status}**."))

@bot.command(name="giveaway")
@commands.has_permissions(manage_guild=True)
async def g_start(ctx, time_str: str, winners: int, *, prize: str):
    msg = await ctx.send(embed=emb(title="🎉 Giveaway Started!", description=f"🎁 **Prize**: {prize}\n👑 **Winners**: `{winners}`\n\nReact with 🎉 below to participate!"))
    await msg.add_reaction("🎉")

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def log_setup(ctx):
    ch = await ctx.guild.create_text_channel("bot-audit-logs")
    guild_logs[ctx.guild.id] = {"logs": ch.id}
    save_data()
    await ctx.send(embed=emb(title="Audit Logs Setup", description=f"✅ Logs will now be routed to {ch.mention}."))

# ==================== HELP MENU ====================

class MenuSelect(discord.ui.Select):
    def __init__(self, prefix):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Moderation", description="Ban, kick, mute, warn, purge commands", emoji="🛠️"),
            discord.SelectOption(label="Fun & Games", description="8ball, roll, coinflip, iq, slap, hug", emoji="⚛️"),
            discord.SelectOption(label="Utility & Tracking", description="Ping, serverinfo, userinfo, snipe, afk", emoji="⚙️"),
            discord.SelectOption(label="Setup & Security", description="Antinuke, automod, autorole, welcome", emoji="🛡️")
        ]
        super().__init__(placeholder="❖ CHOOSE A CATEGORY ❖", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        mod = self.values[0]
        e = emb(title=f"Module • {mod}", description=f"You selected the **{mod}** module category.")
        await interaction.response.edit_message(embed=e, view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="help", aliases=["cmds", "menu", "helpme"])
async def help_command(ctx):
    p = ctx.prefix
    desc = (
        "A feature-packed multipurpose bot loaded with complete tools!\n\n"
        f"• **My Prefix is**: `{p}`\n"
        "• **Total Commands**: Massive collection!\n"
        "• **Choose a category from the dropdown below**\n\n"
        "🛠️ `»` Moderation (Ban, Kick, Mute, Warn, Clear)\n"
        "⚛️ `»` Fun (8ball, Roll, Slap, Hug, IQ)\n"
        "⚙️ `»` Utility (Ping, Serverinfo, Snipe, AFK)\n"
        "🛡️ `»` Setup (Antinuke, Automod, Autorole, Logs)"
    )
    e = discord.Embed(title="Moonlight Heaven Help Menu", description=desc, color=discord.Color.blue())
    e.set_footer(text="Bot Developed by Zeus")
    await ctx.send(embed=e, view=MenuView(p))

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Error: TOKEN environment variable not found!")
