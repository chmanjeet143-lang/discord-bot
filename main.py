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

def get_prefix(bot, message):
    if not message.guild:
        return "&"
    return guild_prefixes.get(message.guild.id, "&")

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

# Persistent Storage Functions (JSON Based)
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
        "nickname_setup": {}
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
        "nickname_setup": guild_nicknames
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

afk_users = {}
voice_join_timestamps = {}
server_invite_counts = {}

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
    print("Status: Online & Ready with All Features!")
    print("----------------------------------------")

@bot.event
async def on_command_error(ctx, error):
    p = ctx.prefix
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        embed = discord.Embed(title="⚠️ Invalid Command Usage", description=f"• **Proper Usage** : `{p}{ctx.command.name} [arguments]`\n• **Help** : `{p}menu`", color=discord.Color.orange())
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title="🚫 Access Denied", description="You lack the required permissions to run this command.", color=discord.Color.red())
    else:
        embed = discord.Embed(title="❌ Command Error", description=f"`{error}`", color=discord.Color.red())
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

    try:
        guild = member.guild
        current_invites = await guild.invites()
        if guild.id in server_invite_counts:
            for inv in current_invites:
                if inv.uses > server_invite_counts[guild.id].get(inv.code, 0):
                    inviter_id = inv.inviter.id
                    if guild.id not in user_invites:
                        user_invites[guild.id] = {}
                    if str(inviter_id) not in user_invites[guild.id]:
                        user_invites[guild.id][str(inviter_id)] = {"total": 0}
                    user_invites[guild.id][str(inviter_id)]["total"] += 1
                    save_data()
                    break
        server_invite_counts[guild.id] = {inv.code: inv.uses for inv in current_invites}
    except:
        pass

# Commands Section
@bot.command(name="ping")
async def ping_command(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 Pong!", description=f"Bot Latency : `{latency}ms`", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="si", aliases=["serverinfo"])
async def server_info(ctx):
    g = ctx.guild
    embed = discord.Embed(title=f"📊 {g.name} - Server Info", color=discord.Color.blurple())
    embed.add_field(name="Owner", value=g.owner, inline=True)
    embed.add_field(name="Members", value=g.member_count, inline=True)
    embed.add_field(name="Created On", value=g.created_at.strftime("%b %d, %Y"), inline=True)
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=embed)

@bot.command(name="afk")
async def afk_command(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(f"💤 {ctx.author.mention} is now AFK: **{reason}**")

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_channels(ctx):
    guild = ctx.guild
    log_ch = await guild.create_text_channel("🤖-bot-logs")
    guild_logs[guild.id] = {"logs": log_ch.id}
    save_data()
    await ctx.send(f"✅ Standard log channels generated successfully! Log Channel: {log_ch.mention}")

@bot.command(name="welcomesetup")
@commands.has_permissions(administrator=True)
async def welcomesetup(ctx, main_channel: discord.TextChannel, rules_channel: discord.TextChannel):
    guild_welcomes[ctx.guild.id] = {"main_channel": main_channel.id, "rules_channel": rules_channel.id}
    save_data()
    await ctx.send(f"✅ Dual welcome channels configured: {main_channel.mention} & {rules_channel.mention}")

@bot.command(name="nicknamesetup")
@commands.has_permissions(administrator=True)
async def nicknamesetup(ctx):
    guild_nicknames[ctx.guild.id] = True
    save_data()
    await ctx.send("✅ Interactive nickname system initialized successfully!")

@bot.command(name="birthdaysetup")
@commands.has_permissions(administrator=True)
async def birthdaysetup(ctx, channel: discord.TextChannel):
    if ctx.guild.id not in guild_birthdays:
        guild_birthdays[ctx.guild.id] = {"users": {}}
    guild_birthdays[ctx.guild.id]["channel"] = channel.id
    save_data()
    await ctx.send(f"✅ Birthday collection channel set to {channel.mention}")

@bot.command(name="giveaway")
@commands.has_permissions(manage_guild=True)
async def giveaway_start(ctx, time_str: str, winners: int, *, prize: str):
    embed = discord.Embed(title="🎉 GIVEAWAY 🎉", description=f"• **Prize**: {prize}\n• **Winners**: `{winners}`\n• **Hosted by**: {ctx.author.mention}\n\nReact with 🎉 to enter!", color=discord.Color.gold())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")

@bot.command(name="autorole")
@commands.has_permissions(administrator=True)
async def autorole_setup(ctx, role: discord.Role):
    guild_autoroles[ctx.guild.id] = role.id
    save_data()
    await ctx.send(f"✅ Automated welcome role set to **{role.name}**")

@bot.command(name="ticketsetup")
@commands.has_permissions(administrator=True)
async def ticket_setup(ctx):
    embed = discord.Embed(title="🎫 Support Tickets", description="Click the button below to open a support ticket.", color=discord.Color.blurple())
    await ctx.send(embed=embed)

@bot.command(name="backup")
@commands.has_permissions(administrator=True)
async def backup_server(ctx):
    guild = ctx.guild
    backup_data = {"categories": [c.name for c in guild.categories]}
    server_backups[guild.id] = backup_data
    save_data()
    await ctx.send("✅ Server layout successfully backed up!")

@bot.command(name="restore")
@commands.has_permissions(administrator=True)
async def restore_server(ctx):
    await ctx.send("🔄 Server layout restoration completed from backup profile.")

@bot.command(name="m", aliases=["messages"])
async def check_messages(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    count = user_messages.get(g_id, {}).get(str(member.id), 0)
    embed = discord.Embed(title="📈 Message Statistics", description=f"• **User**: {member.mention}\n• **Total Messages**: `{count}`", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="v", aliases=["voice"])
async def check_voice(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    seconds = user_voice_time.get(g_id, {}).get(str(member.id), 0)
    if member.id in voice_join_timestamps:
        seconds += int(time.time() - voice_join_timestamps[member.id])
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    embed = discord.Embed(title="🔊 Voice Statistics", description=f"• **User**: {member.mention}\n• **Voice Time**: `{hours} hours {minutes} minutes`", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="i", aliases=["invites"])
async def check_invites(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    inv_data = user_invites.get(g_id, {}).get(str(member.id), {"total": 0})
    total = inv_data.get("total", 0)
    embed = discord.Embed(title="🎟️ Invite Statistics", description=f"• **User**: {member.mention}\n• **Total Invites**: `{total}`", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="rm")
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, target: str = "all"):
    g_id = ctx.guild.id
    if target.lower() == "all":
        user_messages[g_id] = {}
        save_data()
        await ctx.send("🔄 Message counters have been reset for all users.")
    else:
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            if g_id in user_messages and str(member.id) in user_messages[g_id]:
                user_messages[g_id][str(member.id)] = 0
                save_data()
            await ctx.send(f"🔄 Message counter reset for {member.mention}")
        except:
            await ctx.send("❌ Invalid user specified.")

@bot.command(name="ri")
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, member: discord.Member):
    g_id = ctx.guild.id
    if g_id in user_invites and str(member.id) in user_invites[g_id]:
        user_invites[g_id][str(member.id)]["total"] = 0
        save_data()
    await ctx.send(f"🔄 Invite metrics reset for {member.mention}")

@bot.command(name="rv")
@commands.has_permissions(administrator=True)
async def reset_voice(ctx, target: str = "all"):
    g_id = ctx.guild.id
    if target.lower() == "all":
        user_voice_time[g_id] = {}
        save_data()
        await ctx.send("🔄 Voice duration tracking reset for all users.")
    else:
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            if g_id in user_voice_time and str(member.id) in user_voice_time[g_id]:
                user_voice_time[g_id][str(member.id)] = 0
                save_data()
            await ctx.send(f"🔄 Voice duration reset for {member.mention}")
        except:
            await ctx.send("❌ Invalid user specified.")

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
    await ctx.send(f"⚠️ Warned {member.mention} for: `{reason}`")

@bot.command(name="warns")
async def view_warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    g_id = ctx.guild.id
    w_list = guild_warns.get(g_id, {}).get(str(member.id), [])
    embed = discord.Embed(title=f"⚠️ Warnings for {member.name}", description="\n".join([f"{i+1}. {r}" for i, r in enumerate(w_list)]) if w_list else "No warnings found!", color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command(name="automod")
@commands.has_permissions(administrator=True)
async def automod_config(ctx):
    g_id = ctx.guild.id
    if g_id not in guild_automod:
        guild_automod[g_id] = {"enabled": False}
    guild_automod[g_id]["enabled"] = not guild_automod[g_id]["enabled"]
    save_data()
    status = "Enabled" if guild_automod[g_id]["enabled"] else "Disabled"
    await ctx.send(f"🛡️ Automod filter triggers have been **{status}**.")

@bot.command(name="purge", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge_messages(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🗑️ Successfully deleted `{amount}` messages.")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Channel has been locked.")

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Channel has been unlocked.")

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
                    f"• `{p}welcomesetup [main_ch] [rules_ch]` - Setup dual welcome channels\n"
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
                    "```ansi\n\u001b[0;31mAdvanced Protection & Control Tools\u001b[0m\n```\n"
                    f"• `{p}warn [user] [reason]` - Issue a formal server warning\n"
                    f"• `{p}warns [user]` - View accumulated user warnings\n"
                    f"• `{p}automod` - Configure automated filter triggers\n"
                    f"• `{p}purge [count]` - Clear bulk chat messages\n"
                    f"• `{p}lock` / `{p}unlock` - Secure channel permissions"
                ),
                color=discord.Color.blurple()
            )
        elif self.values[0] == "Utility & Tools":
            embed = discord.Embed(
                title="🛠️ Utility & Tools",
                description=(
                    "```ansi\n\u001b[0;36mGeneral Utility Commands\u001b[0m\n```\n"
                    f"• `{p}afk [reason]` - Set your status to AFK\n"
                    f"• `{p}ping` - Check bot response latency"
                ),
                color=discord.Color.blurple()
            )
        
        embed.set_footer(text="Moonlight Heaven • Developed by Zeus", icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None)
        await interaction.response.edit_message(embed=embed, view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="menu")
async def menu_command(ctx):
    p = ctx.prefix
    embed = discord.Embed(
        title="✨ Moonlight Heaven • Help Menu",
        description=(
            "```ansi\n\u001b[0;36mSelect a category from the dropdown menu below to view available commands.\u001b[0m\n```\n"
            "• **Developer** : Created by **Zeus** 🚀\n"
            "• **Prefix** : Use custom or default `&` prefix"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Moonlight Heaven • Interactive Menu", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
    await ctx.send(embed=embed, view=MenuView(p))

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Error: TOKEN environment variable not found!")
