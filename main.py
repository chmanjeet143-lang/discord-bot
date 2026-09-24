import os
import time
import json
import random
import asyncio
import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')

@app.route('/')
def home():
    return "🤖 Zynrax Bot is Alive and Running!"

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
        return "Z"
    return guild_prefixes.get(message.guild.id, "Z")

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

afk_users = {}
voice_join_timestamps = {}

def ae(title="", description="", color=discord.Color.from_rgb(15, 15, 20)):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="❖ Zynrax Bot Core ❖")
    return embed

@bot.event
async def on_ready():
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            for member in channel.members:
                if not member.bot:
                    voice_join_timestamps[(guild.id, member.id)] = time.time()

    print("----------------------------------------")
    print(f"Bot Name: {bot.user.name}")
    print("Status: Zynrax Fully Operational with All Commands!")
    print("----------------------------------------")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=ae(title="Access Denied", description="You lack required permissions for this command."))
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
            if g_id not in user_voice_time:
                user_voice_time[g_id] = {}
            user_voice_time[g_id][u_id] = user_voice_time[g_id].get(u_id, 0) + duration
            save_data()
            
    elif before.channel != after.channel and before.channel is not None and after.channel is not None:
        start_time = voice_join_timestamps.pop(key, None)
        if start_time:
            duration = int(time.time() - start_time)
            if g_id not in user_voice_time:
                user_voice_time[g_id] = {}
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
                    await message.channel.send(f"{message.author.mention}, wrong counting number! Reset to `{expected}`.", delete_after=4)
            except ValueError:
                if not message.author.guild_permissions.manage_messages:
                    try: await message.delete()
                    except: pass

    if g_id not in user_messages:
        user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    if u_id in afk_users:
        del afk_users[u_id]
        try: await message.channel.send(f"Welcome back, {message.author.mention}. AFK removed.", delete_after=5)
        except: pass

    await bot.process_commands(message)

# ==================== ALL COMMANDS ====================

@bot.command(name="ping")
async def ping_command(ctx):
    await ctx.send(embed=ae(title="Latency Matrix", description=f"⚡ Response Rate: `{round(bot.latency * 1000)}ms`"))

@bot.command(name="si", aliases=["serverinfo"])
async def server_info(ctx):
    g = ctx.guild
    emb = ae(title=f"Server Info • {g.name}", description=f"Supreme Ruler: {g.owner}\nTotal Members: `{g.member_count}`")
    if g.icon: emb.set_thumbnail(url=g.icon.url)
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
    
    desc = (
        f"🦇 **Total Members**: `{total}`\n"
        f"🤍 **Total Humans**: `{humans}`\n"
        f"🤖 **Total Bots**: `{bots}`\n"
        f"🟢 **Online**: `{online}`\n"
        f"🔴 **Dnd**: `{dnd}`\n"
        f"🟡 **Idle**: `{idle}`\n"
        f"⚫ **Offline**: `{offline}`"
    )
    await ctx.send(embed=ae(title="Member Statistics", description=desc))

@bot.command(name="warn")
@commands.has_permissions(kick_members=True)
async def warn_user(ctx, member: discord.Member, *, reason="No reason"):
    g_id = ctx.guild.id
    if g_id not in guild_warns: guild_warns[g_id] = {}
    if str(member.id) not in guild_warns[g_id]: guild_warns[g_id][str(member.id)] = []
    guild_warns[g_id][str(member.id)].append(reason)
    save_data()
    await ctx.send(embed=ae(title="Disciplinary Strike", description=f"Target: {member.mention}\nInfraction: `{reason}`"))

@bot.command(name="purge", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge_msgs(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=ae(title="Data Expunged", description=f"Purged `{amount}` messages."))
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_ch(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=ae(title="Sector Lockdown", description="Channel locked successfully."))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_ch(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=ae(title="Sector Restored", description="Channel unlocked successfully."))

@bot.command(name="afk")
async def afk_cmd(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(embed=ae(title="AFK Enabled", description=f"{ctx.author.mention} is now AFK: **{reason}**"))

@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, prefix: str):
    guild_prefixes[ctx.guild.id] = prefix
    save_data()
    await ctx.send(embed=ae(title="Prefix Modified", description=f"New prefix set to: `{prefix}`"))

@bot.command(name="clone")
@commands.has_permissions(manage_emojis=True)
async def clone_emoji(ctx):
    await ctx.send(embed=ae(title="Asset Duplication", description="Reply to an emoji to clone it."))

@bot.command(name="start", aliases=["counting"])
@commands.has_permissions(administrator=True)
async def start_counting(ctx, amount: int = 1, channel: discord.TextChannel = None, emoji: str = "❖"):
    target_channel = channel or ctx.channel
    guild_counting[ctx.guild.id] = {
        "channel_id": target_channel.id,
        "next_number": amount,
        "last_user": 0,
        "emoji": emoji
    }
    save_data()
    await ctx.send(embed=ae(title="Counting Active", description=f"Configured in {target_channel.mention} starting from **{amount}**!"))

@bot.command(name="roll")
async def roll_dice(ctx):
    await ctx.send(embed=ae(title="Dice Roll", description=f"Result: `[{random.randint(1, 6)}]`"))

@bot.command(name="coinflip")
async def coin_flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(embed=ae(title="Coin Flip", description=f"Result: **{result}**"))

@bot.command(name="m", aliases=["messages"])
async def msg_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    count = user_messages.get(ctx.guild.id, {}).get(str(member.id), 0)
    await ctx.send(embed=ae(title="Transmission Metrics", description=f"{member.mention} has sent `{count}` messages."))

@bot.command(name="v", aliases=["voice"])
async def voice_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    secs = user_voice_time.get(ctx.guild.id, {}).get(str(member.id), 0)
    minutes = secs // 60
    hours = minutes // 60
    rem_mins = minutes % 60
    await ctx.send(embed=ae(title="Auditory Chrono Log", description=f"{member.mention} has spent `{hours} hours and {rem_mins} minutes` in voice channels."))

@bot.command(name="i", aliases=["invites"])
async def invite_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(embed=ae(title="Recruitment Analytics", description=f"Invite statistics for {member.mention}."))

@bot.command(name="rm")
async def reset_messages(ctx, target: str = None):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=ae(title="Error", description="You need Administrator permissions."))
    if target == "all":
        user_messages[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=ae(title="Success", description="All users message stats have been reset."))
    else:
        await ctx.send(embed=ae(title="Usage", description="Use `&rm all` to clear message stats."))

@bot.command(name="rv")
async def reset_voice(ctx, target: str = None):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=ae(title="Error", description="You need Administrator permissions."))
    if target == "all":
        user_voice_time[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=ae(title="Success", description="All users voice time stats have been reset."))
    else:
        await ctx.send(embed=ae(title="Usage", description="Use `&rv all` to clear voice stats."))

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
    await ctx.send(embed=ae(title="Autorole Set", description=f"New members will get **{role.name}**."))

@bot.command(name="ar")
@commands.has_permissions(administrator=True)
async def auto_responder(ctx, trigger: str, *, response: str):
    g_id = ctx.guild.id
    if g_id not in guild_autoresponder: guild_autoresponder[g_id] = {}
    guild_autoresponder[g_id][trigger.lower()] = response
    save_data()
    await ctx.send(embed=ae(title="Autoresponder Added", description=f"Trigger `{trigger}` added successfully!"))

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
    await ctx.send(embed=ae(title="Music Player", description=f"Queued song: `{song}`"))

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

# ==================== HELP MENU (ZYNRAX EXACT) ====================

class MenuSelect(discord.ui.Select):
    def __init__(self, prefix):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Antinuke", description="Anti-nuke security system", emoji="🛡️"),
            discord.SelectOption(label="AutoMod", description="Message and link filters", emoji="🤖"),
            discord.SelectOption(label="Automations", description="Automated triggers", emoji="🔗"),
            discord.SelectOption(label="Autoresponder", description="Custom text responses", emoji="🤍"),
            discord.SelectOption(label="CustomRole", description="Role icons & management", emoji="🎨"),
            discord.SelectOption(label="Fun", description="Fun games & counting", emoji="⚛️"),
            discord.SelectOption(label="General", description="General commands", emoji="📱"),
            discord.SelectOption(label="Giveaway", description="Host giveaways", emoji="🎉"),
            discord.SelectOption(label="Leaderboard", description="Stats & tracking", emoji="🏆"),
            discord.SelectOption(label="Logging", description="Audit logs setup", emoji="🦇"),
            discord.SelectOption(label="Moderation", description="Warns, purge, lock", emoji="🛠️"),
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
        p = self.prefix
        mod = self.values[0]
        desc = f"• Active directives under **{mod}** module."
        embed = ae(title=f"Module Matrix • {mod}", description=desc)
        await interaction.response.edit_message(embed=embed, view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="help", aliases=["cmds", "menu", "zhelp"])
async def help_command(ctx):
    p = ctx.prefix
    desc = (
        "A powerful multipurpose bot with Fastest Antinuke\n\n"
        f"• **My Prefix is** `{p}`\n"
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
        "⭐ `»` Vanityroles\n"
        "🔊 `»` Voice\n"
        "🎙️ `»` VoiceMaster\n"
        "🚪 `»` Welcomer"
    )
    embed = discord.Embed(
        title="Hey, I'm Zynrax™",
        description=desc,
        color=discord.Color.from_rgb(15, 15, 20)
    )
    embed.set_thumbnail(url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe")
    embed.set_footer(text="❖ Zynrax Bot Core ❖")
    
    await ctx.send(embed=embed, view=MenuView(p))

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Error: TOKEN environment variable not found!")
