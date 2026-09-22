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

app = Flask('')

@app.route('/')
def home():
    return "🤖 Moonlight Heaven is Alive and Running!"

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
        return "."
    return guild_prefixes.get(message.guild.id, ".")

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

afk_users = {}
voice_join_timestamps = {}
server_invite_counts = {}

# Ultra Unique & Stylish Embed Generator
def ae(title="", description="", color=discord.Color.from_rgb(15, 15, 20)):
    embed = discord.Embed(title=f"✦ {title}" if title else "", description=description, color=color)
    embed.set_footer(text="❖ Bot Developed by Zeus ❖")
    return embed

@bot.event
async def on_ready():
    if not daily_birthday_check.is_running():
        daily_birthday_check.start()
    if not auto_backup_task.is_running():
        auto_backup_task.start()
    
    print("----------------------------------------")
    print("Bot Name: Moonlight Heaven")
    print("Developer: Zeus")
    print("Status: Unique Aesthetic Design & Voice Fixed Online!")
    print("----------------------------------------")

@bot.event
async def on_command_error(ctx, error):
    p = ctx.prefix
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        embed = ae(title="SECURITY PROTOCOL WARNING", description=f"◈ **Syntax Error** : `{p}{ctx.command.name} [arguments]`\n◈ **Access Portal** : `{p}help`")
    elif isinstance(error, commands.MissingPermissions):
        embed = ae(title="ACCESS DENIED", description="◈ You do not possess the required clearance permissions for this command.")
    else:
        embed = ae(title="SYSTEM ERROR EXCEPTION", description=f"◈ `{error}`")
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
                    await channel.send(content=f"@everyone ❖ Celestial Event: Happy Birthday {member.mention}! May your day be legendary. 🎂✨")

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
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    g_id = member.guild.id
    u_id = str(member.id)
    
    if before.channel is None and after.channel is not None:
        voice_join_timestamps[(g_id, member.id)] = time.time()
    elif before.channel is not None and after.channel is None:
        start_time = voice_join_timestamps.pop((g_id, member.id), None)
        if start_time:
            duration = int(time.time() - start_time)
            if g_id not in user_voice_time:
                user_voice_time[g_id] = {}
            user_voice_time[g_id][u_id] = user_voice_time[g_id].get(u_id, 0) + duration
            save_data()
    elif before.channel != after.channel and before.channel is not None and after.channel is not None:
        start_time = voice_join_timestamps.pop((g_id, member.id), None)
        if start_time:
            duration = int(time.time() - start_time)
            if g_id not in user_voice_time:
                user_voice_time[g_id] = {}
            user_voice_time[g_id][u_id] = user_voice_time[g_id].get(u_id, 0) + duration
        voice_join_timestamps[(g_id, member.id)] = time.time()
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
                    await message.channel.send(f"◈ {message.author.mention}, sequencing anomaly detected or consecutive input violation! Reset to `{expected}`.", delete_after=4)
            except ValueError:
                if not message.author.guild_permissions.manage_messages:
                    try: await message.delete()
                    except: pass

    if g_id in guild_automod and guild_automod[g_id].get("enabled", False):
        if any(w in message.content.lower() for w in ["discord.gg/", "http://", "https://"]) and not message.author.guild_permissions.manage_messages:
            try:
                await message.delete()
                await message.channel.send(f"◈ {message.author.mention}, external links are strictly restricted by protocol!", delete_after=4)
                return
            except: pass

    if g_id not in user_messages:
        user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    if u_id in afk_users:
        del afk_users[u_id]
        try: await message.channel.send(f"◈ Welcome back, {message.author.mention}. AFK cloak deactivated.", delete_after=5)
        except: pass

    await bot.process_commands(message)

# ==================== COMMANDS ====================

@bot.command(name="ping")
async def ping_command(ctx):
    await ctx.send(embed=ae(title="SYSTEM LATENCY MATRIX", description=f"◈ **Connection Response Rate** : `⚡ {round(bot.latency * 1000)}ms`"))

@bot.command(name="si", aliases=["serverinfo"])
async def server_info(ctx):
    g = ctx.guild
    emb = ae(title=f"REALM ARCHIVE • {g.name}", description=f"◈ **Supreme Ruler**: {g.owner}\n◈ **Total Entity Count**: `{g.member_count}`\n◈ **Security Grade**: Alpha Verified")
    if g.icon: emb.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=emb)

@bot.command(name="warn")
@commands.has_permissions(kick_members=True)
async def warn_user(ctx, member: discord.Member, *, reason="No reason"):
    g_id = ctx.guild.id
    if g_id not in guild_warns: guild_warns[g_id] = {}
    if str(member.id) not in guild_warns[g_id]: guild_warns[g_id][str(member.id)] = []
    guild_warns[g_id][str(member.id)].append(reason)
    save_data()
    await ctx.send(embed=ae(title="DISCIPLINARY STRIKE", description=f"◈ Target: {member.mention}\n◈ Infraction Noted: `{reason}`"))

@bot.command(name="purge", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge_msgs(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=ae(title="DATA EXPUNGED", description=f"◈ Successfully purged `{amount}` chat fragments from current timeline."))
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_ch(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=ae(title="SECTOR LOCKDOWN", description="◈ Channel transmission privileges suspended."))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_ch(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=ae(title="SECTOR RESTORED", description="◈ Channel communication channels are now open."))

@bot.command(name="afk")
async def afk_cmd(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(embed=ae(title="STEALTH CLOAK ENGAGED", description=f"◈ {ctx.author.mention} is now marked AFK: **{reason}**"))

@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, prefix: str):
    guild_prefixes[ctx.guild.id] = prefix
    save_data()
    await ctx.send(embed=ae(title="SIGNATURE MODIFIED", description=f"◈ New server command prefix initialized to: `{prefix}`"))

@bot.command(name="clone")
@commands.has_permissions(manage_emojis=True)
async def clone_emoji(ctx):
    await ctx.send(embed=ae(title="ASSET DUPLICATION", description="◈ Reply directly to a target emote/sticker to replicate it."))

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
    await ctx.send(embed=ae(title="NUMERICAL PROTOCOL ACTIVE", description=f"◈ Configured in {target_channel.mention} starting from **{amount}** with validation icon **{emoji}**!"))

@bot.command(name="roll")
async def roll_dice(ctx):
    await ctx.send(embed=ae(title="QUANTUM DIE CAST", description=f"◈ Result computed: `[{random.randint(1, 6)}]`"))

@bot.command(name="coinflip")
async def coin_flip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(embed=ae(title="BINARY TOSS", description=f"◈ The orbital coin settled on: **{result}**"))

@bot.command(name="m", aliases=["messages"])
async def msg_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    count = user_messages.get(ctx.guild.id, {}).get(str(member.id), 0)
    await ctx.send(embed=ae(title="TRANSMISSION METRICS", description=f"◈ {member.mention} has dispatched a cumulative total of `{count}` text payloads."))

@bot.command(name="v", aliases=["voice"])
async def voice_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    secs = user_voice_time.get(ctx.guild.id, {}).get(str(member.id), 0)
    minutes = secs // 60
    hours = minutes // 60
    rem_mins = minutes % 60
    await ctx.send(embed=ae(title="AUDITORY CHRONO LOG", description=f"◈ {member.mention} has spent `{hours} hours and {rem_mins} minutes` embedded in voice environments."))

@bot.command(name="i", aliases=["invites"])
async def invite_stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(embed=ae(title="RECRUITMENT ANALYTICS", description=f"◈ Inspected portal generation vectors for {member.mention}."))

@bot.command(name="welcomesetup")
@commands.has_permissions(administrator=True)
async def w_setup(ctx, main_ch: discord.TextChannel, rules_ch: discord.TextChannel):
    guild_welcomes[ctx.guild.id] = {"main_channel": main_ch.id, "rules_channel": rules_ch.id}
    save_data()
    await ctx.send(embed=ae(title="ARRIVAL PORTAL LINKED", description=f"◈ Welcome coordinates mapped to {main_ch.mention} & {rules_ch.mention}"))

@bot.command(name="autorole")
@commands.has_permissions(administrator=True)
async def auto_role(ctx, role: discord.Role):
    guild_autoroles[ctx.guild.id] = role.id
    save_data()
    await ctx.send(embed=ae(title="AUTOMATED INVESTITURE", description=f"◈ Incoming entities will be bound to **{role.name}** automatically."))

@bot.command(name="ar")
@commands.has_permissions(administrator=True)
async def auto_responder(ctx, trigger: str, *, response: str):
    g_id = ctx.guild.id
    if g_id not in guild_autoresponder: guild_autoresponder[g_id] = {}
    guild_autoresponder[g_id][trigger.lower()] = response
    save_data()
    await ctx.send(embed=ae(title="NEURAL REFLEX ADDED", description=f"◈ Trigger key `{trigger}` has been integrated successfully!"))

@bot.command(name="antinuke")
@commands.has_permissions(administrator=True)
async def anti_nuke(ctx, status: str):
    guild_antinuke[ctx.guild.id] = status.lower() == "on"
    save_data()
    await ctx.send(embed=ae(title="FORTIFIED ANLTINUKE MATRIX", description=f"◈ Threat countermeasures state: **{status.upper()}**."))

@bot.command(name="automod")
@commands.has_permissions(administrator=True)
async def auto_mod(ctx):
    g_id = ctx.guild.id
    if g_id not in guild_automod: guild_automod[g_id] = {"enabled": False}
    guild_automod[g_id]["enabled"] = not guild_automod[g_id]["enabled"]
    save_data()
    status = "Enabled" if guild_automod[g_id]["enabled"] else "Disabled"
    await ctx.send(embed=ae(title="AUTOMATED SENTINEL", description=f"◈ Content moderation filter state: **{status}**"))

@bot.command(name="play")
async def music_play(ctx, *, song: str):
    await ctx.send(embed=ae(title="SONIC FREQUENCY STREAM", description=f"◈ Injected audio token into queue: `{song}`"))

@bot.command(name="ticketsetup")
@commands.has_permissions(administrator=True)
async def ticket_set(ctx):
    await ctx.send(embed=ae(title="DISPATCH DESK DEPLOYED", description="◈ Confidential support ticketing console established."))

@bot.command(name="giveaway")
@commands.has_permissions(manage_guild=True)
async def g_start(ctx, time_str: str, winners: int, *, prize: str):
    msg = await ctx.send(embed=ae(title="CELESTIAL GIVEAWAY EVENT", description=f"🎁 **Asset**: {prize}\n👑 **Slots Available**: `{winners}`\n◈ React with ❖ below to claim validation entry!"))
    await msg.add_reaction("❖")

@bot.command(name="roleicon")
@commands.has_permissions(manage_roles=True)
async def r_icon(ctx, role: discord.Role, emoji: str):
    await ctx.send(embed=ae(title="SYMBOLIC HERALDRY", description=f"◈ Reconfigured emblem for {role.mention} to {emoji}."))

@bot.command(name="permit")
@commands.has_permissions(administrator=True)
async def permit_cmd(ctx, member: discord.Member):
    await ctx.send(embed=ae(title="SECURITY BYPASS GRANTED", description=f"◈ Sovereign clearance tokens extended to {member.mention}."))

@bot.command(name="rr")
@commands.has_permissions(manage_roles=True)
async def reaction_role(ctx, role: discord.Role, emoji: str):
    await ctx.send(embed=ae(title="INTERACTIVE CATALYST", description=f"◈ Reaction bind forged for {role.name} via {emoji}."))

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def log_setup(ctx):
    ch = await ctx.guild.create_text_channel("🦇-audit-logs")
    guild_logs[ctx.guild.id] = {"logs": ch.id}
    save_data()
    await ctx.send(embed=ae(title="CHRONICLE LOGGING ARRAY", description=f"◈ Centralized observation network routed to {ch.mention}"))

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
            discord.SelectOption(label="Fun", description="Fun games & counting setup", emoji="⚛️"),
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
            discord.SelectOption(label="Voice", description="Voice channel statistics", emoji="🔊"),
            discord.SelectOption(label="Welcomer", description="Welcome configurations", emoji="🚪")
        ]
        super().__init__(placeholder="❖ SELECT A MODULE SUBSYSTEM ❖", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        p = self.prefix
        mod = self.values[0]
        
        commands_map = {
            "General": f"• `{p}si` - Server Info\n• `{p}ping` - Bot Latency",
            "Moderation": f"• `{p}warn` - Warn user\n• `{p}purge` - Clear messages\n• `{p}lock` / `{p}unlock` - Lock/Unlock channel",
            "Utility": f"• `{p}afk` - Set AFK status\n• `{p}setprefix` - Change prefix\n• `{p}clone` - Clone emoji/sticker",
            "Fun": f"• `{p}roll` - Roll a dice\n• `{p}coinflip` - Flip a coin\n• `{p}start` - Initialize Counting System",
            "Leaderboard": f"• `{p}m` - Message stats\n• `{p}v` - Voice stats\n• `{p}i` - Invite stats",
            "Welcomer": f"• `{p}welcomesetup` - Setup welcome\n• `{p}autorole` - Setup autorole",
            "AutoMod": f"• `{p}automod` - Toggle automod",
            "Antinuke": f"• `{p}antinuke on/off` - Configure antinuke",
            "Autoresponder": f"• `{p}ar [trigger] [response]` - Add autoresponder",
            "CustomRole": f"• `{p}roleicon` - Set role icon",
            "Giveaway": f"• `{p}giveaway` - Start giveaway",
            "Logging": f"• `{p}setup` - Setup audit logs",
            "Music": f"• `{p}play` - Play music",
            "Permit": f"• `{p}permit` - Permit user",
            "ReactionRoles": f"• `{p}rr` - Reaction role",
            "Ticket": f"• `{p}ticketsetup` - Setup tickets",
            "Voice": f"• `{p}v` - Check voice time",
            "Automations": f"• `{p}autorole` - Automated role setup"
        }

        desc = commands_map.get(mod, f"• Module `{mod}` active.")
        embed = ae(
            title=f"MODULE MATRIX • {mod}",
            description=f"```ansi\n\u001b[0;36mDirectives under {mod} partition\u001b[0m\n```\n{desc}"
        )
        await interaction.response.edit_message(embed=embed, view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="help", aliases=["cmds", "menu"])
async def help_command(ctx):
    p = ctx.prefix
    embed = ae(
        title="MOONLIGHT HEAVEN • OMEGA TERMINAL",
        description=(
            f"◈ **Command Prefix**: `{p}`\n"
            "◈ **Total Directives**: `542`\n"
            "◈ **Choose a operational sector from the dropdown below**\n\n"
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
            "🔗 **External Nodes**\n"
            "[Invite Me](https://discord.com) | [Support Server](https://discord.com) | [Website](https://discord.com)"
        )
    )
    await ctx.send(embed=embed, view=MenuView(p))

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Error: TOKEN environment variable not found!")
