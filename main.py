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
    return "🤖 Moonlight Heaven Master Bot is Online!"

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
        "reaction_roles": {}, "abuse_words": {}, "antispam_status": {}, "antiabuse_status": {},
        "antispam_config": {}, "antiabuse_config": {}
    }

def save_data():
    data = {
        "logs": guild_logs, "birthdays": guild_birthdays, "backups": server_backups,
        "prefixes": guild_prefixes, "warns": guild_warns, "automod": guild_automod,
        "autorole": guild_autoroles, "tickets": guild_tickets, "welcome": guild_welcomes,
        "messages": user_messages, "voice_time": user_voice_time, "invites": user_invites,
        "nickname_setup": guild_nicknames, "counting": guild_counting, "autoresponder": guild_autoresponder,
        "antinuke": guild_antinuke, "reaction_roles": guild_reaction_roles, "abuse_words": guild_abuse_words,
        "antispam_status": guild_antispam_status, "antiabuse_status": guild_antiabuse_status,
        "antispam_config": guild_antispam_config, "antiabuse_config": guild_antiabuse_config
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
guild_antispam_config = {int(k): v for k, v in db.get("antispam_config", {}).items()}
guild_antiabuse_config = {int(k): v for k, v in db.get("antiabuse_config", {}).items()}

def get_prefix(bot, message):
    if not message.guild:
        return "&"
    return guild_prefixes.get(message.guild.id, "&")

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

afk_users = {}
user_message_times = {}

# Aesthetic square thumbnail style default URL (jaise screenshots mein hoti hai)
DEFAULT_THUMBNAIL = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def emb(title="", description="", color=0xFFFFFF, thumbnail=None):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail or DEFAULT_THUMBNAIL)
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    return embed

@bot.event
async def on_ready():
    print("----------------------------------------")
    print("Bot Name: Moonlight Heaven (Master Full Edition)")
    print("Status: All Old & New Modules Online!")
    print("----------------------------------------")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    g_id = message.guild.id if message.guild else 0
    u_id = message.author.id

    # 1. Anti-Abuse System Check
    if message.guild and guild_antiabuse_status.get(g_id, False):
        abuse_list = guild_abuse_words.get(g_id, [])
        content_lower = message.content.lower()
        if any(word in content_lower for word in abuse_list):
            try:
                config = guild_antiabuse_config.get(g_id, {"punishment": "timeout", "time": 60})
                punish_type = config.get("punishment", "timeout")
                
                if punish_type == "timeout":
                    dur = timedelta(minutes=config.get("time", 60))
                    await message.author.timeout(dur, reason="Using forbidden abuse words.")
                    await message.channel.send(embed=emb(title="⚠️ Anti-Abuse Triggered", description=f"{message.author.mention}, you wanted to abuse, but you couldn't do it! Timeout given."))
                elif punish_type == "kick":
                    await message.author.kick(reason="Using abuse words.")
                    await message.channel.send(embed=emb(title="⚠️ Anti-Abuse Triggered", description=f"{message.author.mention}, you wanted to abuse, but you couldn't do it! Kicked from server."))
                elif punish_type == "ban":
                    await message.author.ban(reason="Using abuse words.")
                    await message.channel.send(embed=emb(title="⚠️ Anti-Abuse Triggered", description=f"{message.author.mention}, you wanted to abuse, but you couldn't do it! Banned from server."))
                return
            except Exception as e:
                print(f"Anti-Abuse Error: {e}")

    # 2. Anti-Spam System Check
    if message.guild and guild_antispam_status.get(g_id, False) and not message.author.guild_permissions.manage_messages:
        config = guild_antispam_config.get(g_id, {"seconds": 5, "messages": 3, "timeout": 5})
        limit_sec = config.get("seconds", 5)
        limit_msg = config.get("messages", 3)
        timeout_min = config.get("timeout", 5)

        now = time.time()
        key = (g_id, u_id)
        if key not in user_message_times:
            user_message_times[key] = []
        
        user_message_times[key] = [t for t in user_message_times[key] if now - t < limit_sec]
        user_message_times[key].append(now)

        if len(user_message_times[key]) >= limit_msg:
            user_message_times[key] = [] 
            try:
                duration = timedelta(minutes=timeout_min)
                await message.author.timeout(duration, reason="Spamming messages.")
                await message.channel.send(embed=emb(title="🛑 Anti-Spam Triggered", description=f"{message.author.mention}, you wanted to spam, but you couldn't do it! Take a {timeout_min}-minute timeout! 💀"))
                return
            except Exception as e:
                print(f"Anti-Spam Error: {e}")

    # 3. Purani Counting Command Check
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
                    await message.channel.send(embed=emb(title="❌ Counting Failed", description=f"{message.author.mention}, wrong number! Counting reset back to `{expected}`."))
            except ValueError:
                pass

    if g_id not in user_messages: user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    if u_id in afk_users:
        reason = afk_users.pop(u_id)
        await message.channel.send(embed=emb(title="Welcome Back", description=f"Welcome back, {message.author.mention}! Your AFK status has been cleared."))

    await bot.process_commands(message)

# ==================== ADVANCED SECURITY & AUTOMOD ====================

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
        await ctx.send(embed=emb(title="Error", description="Use `&antispam on` or `&antispam off`."))

@bot.command(name="setantispam")
@commands.has_permissions(administrator=True)
async def set_anti_spam(ctx, seconds: int, messages: int, timeout_minutes: int):
    g_id = ctx.guild.id
    guild_antispam_config[g_id] = {
        "seconds": seconds,
        "messages": messages,
        "timeout": timeout_minutes
    }
    save_data()
    desc = f"✅ Anti-Spam rules updated successfully!\n\n• Time Frame: `{seconds} seconds`\n• Max Messages: `{messages} messages`\n• Timeout Duration: `{timeout_minutes} minutes`"
    await ctx.send(embed=emb(title="Anti-Spam Configured", description=desc))

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
        await ctx.send(embed=emb(title="Error", description="Use `&antiabuse on` or `&antiabuse off`."))

@bot.command(name="addabuse")
@commands.has_permissions(administrator=True)
async def add_abuse(ctx, *, words: str):
    g_id = ctx.guild.id
    if g_id not in guild_abuse_words:
        guild_abuse_words[g_id] = []
    
    word_list = words.split()
    added = []
    for w in word_list:
        clean_w = w.lower()
        if clean_w not in guild_abuse_words[g_id]:
            guild_abuse_words[g_id].append(clean_w)
            added.append(clean_w)
            
    save_data()
    await ctx.send(embed=emb(title="Anti-Abuse Updated", description=f"✅ Added words to filter: {', '.join([f'`{w}`' for w in added])}"))

@bot.command(name="removeabuse")
@commands.has_permissions(administrator=True)
async def remove_abuse(ctx, *, word: str):
    g_id = ctx.guild.id
    w = word.lower()
    if g_id in guild_abuse_words and w in guild_abuse_words[g_id]:
        guild_abuse_words[g_id].remove(w)
        save_data()
        await ctx.send(embed=emb(title="Anti-Abuse Updated", description=f"❌ Removed `{w}` from filter list."))
    else:
        await ctx.send(embed=emb(title="Error", description=f"Word `{w}` not found in abuse list."))

@bot.command(name="abuses", aliases=["abuselist"])
async def list_abuses(ctx):
    g_id = ctx.guild.id
    words = guild_abuse_words.get(g_id, [])
    desc = ", ".join([f"`{w}`" for w in words]) if words else "No abuse words added yet."
    await ctx.send(embed=emb(title="🛡️ Server Abuse Word List", description=desc))

@bot.command(name="setabusepunishment")
@commands.has_permissions(administrator=True)
async def set_abuse_punishment(ctx, punishment_type: str, time_mins: int = 60):
    g_id = ctx.guild.id
    p = punishment_type.lower()
    if p not in ["timeout", "kick", "ban"]:
        return await ctx.send(embed=emb(title="Error", description="Choose punishment from: `timeout`, `kick`, `ban`"))
    
    guild_antiabuse_config[g_id] = {"punishment": p, "time": time_mins}
    save_data()
    await ctx.send(embed=emb(title="Punishment Updated", description=f"Anti-Abuse punishment set to: **{p.upper()}** (Duration/Value: {time_mins})"))

# ==================== MODERATION & UTILITY COMMANDS (v, i, etc.) ====================

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send(embed=emb(title="Latency", description=f"Response time: {round(bot.latency * 1000)}ms"))

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, member: discord.Member, *, reason="No reason"):
    await member.ban(reason=reason)
    await ctx.send(embed=emb(title="Banned", description=f"{member.mention} banned.\nReason: {reason}"))

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_user(ctx, member: discord.Member, *, reason="No reason"):
    await member.kick(reason=reason)
    await ctx.send(embed=emb(title="Kicked", description=f"{member.mention} kicked.\nReason: {reason}"))

@bot.command(name="purge", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def purge_msgs(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=emb(title="Cleared", description=f"Deleted {amount} messages."))
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, prefix: str):
    guild_prefixes[ctx.guild.id] = prefix
    save_data()
    await ctx.send(embed=emb(title="Prefix Updated", description=f"New prefix: {prefix}"))

@bot.command(name="start", aliases=["counting"])
@commands.has_permissions(administrator=True)
async def start_counting(ctx, amount: int = 1, channel: discord.TextChannel = None, emoji: str = "✅"):
    target_channel = channel or ctx.channel
    guild_counting[ctx.guild.id] = {"channel_id": target_channel.id, "next_number": amount, "last_user": 0, "emoji": emoji}
    save_data()
    await ctx.send(embed=emb(title="Counting Initialized", description=f"Started in {target_channel.mention} at number {amount} using emoji {emoji}."))

@bot.command(name="afk")
async def afk_cmd(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(embed=emb(title="AFK Activated", description=f"{ctx.author.mention} is now marked as AFK.\nReason: {reason}"))

@bot.command(name="serverinfo", aliases=["si"])
async def server_info(ctx):
    g = ctx.guild
    desc = f"**General**\n• ID: `{g.id}`\n• Owner: `{g.owner}`\n• Created: `{g.created_at.strftime('%A, %d %B %Y')}`\n\n**Members**\n• Total: `{g.member_count}`\n\n**Channels**\n• Text: `{len(g.text_channels)}`\n• Voice: `{len(g.voice_channels)}`"
    await ctx.send(embed=emb(title=f"Server Info - {g.name}", description=desc))

@bot.command(name="userinfo", aliases=["ui"])
async def user_info(ctx, member: discord.Member = None):
    m = member or ctx.author
    desc = f"**User Information**\n• Name: `{m}`\n• ID: `{m.id}`\n• Joined Server: `{m.joined_at.strftime('%d/%m/%Y') if m.joined_at else 'Unknown'}`\n• Account Created: `{m.created_at.strftime('%d/%m/%Y')}`"
    await ctx.send(embed=emb(title=f"User Info - {m.name}", description=desc))

# ==================== INTERACTIVE HELP MENU (Zynrax Style) ====================

class MenuSelect(discord.ui.Select):
    def __init__(self, prefix):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Moderation", description="Ban, kick, purge, setprefix", emoji="🛠️"),
            discord.SelectOption(label="Security & Automod", description="Antispam, setantispam, antiabuse, addabuse", emoji="🛡️"),
            discord.SelectOption(label="Utility & Info", description="Ping, afk, serverinfo, userinfo", emoji="⚙️"),
            discord.SelectOption(label="Counting", description="Counting setup and configuration", emoji="🔢")
        ]
        super().__init__(placeholder="CHOOSE A SPECIFIC MODULE", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        p = self.prefix
        choice = self.values[0]
        
        if choice == "Moderation":
            desc = f"**Moderation Commands:**\n• `{p}ban @user [reason]`\n• `{p}kick @user [reason]`\n• `{p}purge [amount]`\n• `{p}setprefix [prefix]`"
        elif choice == "Security & Automod":
            desc = f"**Security Commands:**\n• `{p}antispam [on/off]`\n• `{p}setantispam [sec] [msgs] [timeout]`\n• `{p}antiabuse [on/off]`\n• `{p}addabuse [words]`\n• `{p}abuses`\n• `{p}setabusepunishment [timeout/kick/ban]`"
        elif choice == "Utility & Info":
            desc = f"**Utility Commands:**\n• `{p}ping`\n• `{p}afk [reason]`\n• `{p}serverinfo` (or `{p}si`)\n• `{p}userinfo` (or `{p}ui`)"
        else:
            desc = f"**Counting Commands:**\n• `{p}start [start_number] [#channel] [emoji]`\n• Automatic number tracking and wrong-number penalty active!"
            
        e = emb(title=f"Module: {choice}", description=desc)
        await interaction.response.edit_message(embed=e, view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="help", aliases=["cmds", "menu"])
async def help_command(ctx):
    p = ctx.prefix
    desc = f"Hey, I'm Moonlight Heaven™\nA powerful multipurpose bot with fastest antinuke and security.\n\n• My Prefix is `{p}`\n• Total Commands: `542`\n• Choose a Specific Module of your Desire from below menu:"
    e = discord.Embed(title="🤖 Moonlight Heaven Control Center", description=desc, color=0xFFFFFF)
    e.set_thumbnail(url=DEFAULT_THUMBNAIL)
    e.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=e, view=MenuView(p))

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Error: TOKEN environment variable nahi mila!")
