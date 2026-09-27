import os
import time
import json
import random
import asyncio
import aiohttp
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
        "logs": {}, "prefixes": {}, "warns": {}, "messages": {}, 
        "voice_time": {}, "invites": {}, "counting": {}, "abuse_words": {}, 
        "antispam_status": {}, "antiabuse_status": {}, "antispam_config": {}, 
        "antiabuse_config": {}
    }

def save_data():
    data = {
        "logs": guild_logs, "prefixes": guild_prefixes, "warns": guild_warns,
        "messages": user_messages, "voice_time": user_voice_time, "invites": user_invites,
        "counting": guild_counting, "abuse_words": guild_abuse_words,
        "antispam_status": guild_antispam_status, "antiabuse_status": guild_antiabuse_status,
        "antispam_config": guild_antispam_config, "antiabuse_config": guild_antiabuse_config
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()
guild_logs = {int(k): v for k, v in db.get("logs", {}).items()}
guild_prefixes = {int(k): v for k, v in db.get("prefixes", {}).items()}
guild_warns = {int(k): v for k, v in db.get("warns", {}).items()}
user_messages = {int(k): v for k, v in db.get("messages", {}).items()}
user_voice_time = {int(k): v for k, v in db.get("voice_time", {}).items()}
user_invites = {int(k): v for k, v in db.get("invites", {}).items()}
guild_counting = {int(k): v for k, v in db.get("counting", {}).items()}
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

DEFAULT_THUMBNAIL = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def emb(title="", description="", color=0xFFFFFF, thumbnail=None):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail or DEFAULT_THUMBNAIL)
    embed.set_footer(text="Moonlight Heaven • Developed by Zeus")
    return embed

@bot.event
async def on_ready():
    print("----------------------------------------")
    print("Bot Name: Moonlight Heaven (Master Edition)")
    print("Status: All Systems & Keep-Alive Online!")
    print("----------------------------------------")

@tasks.loop(seconds=60)
async def voice_time_tracker():
    for guild in bot.guilds:
        g_id = guild.id
        if g_id not in user_voice_time:
            user_voice_time[g_id] = {}
        for vc in guild.voice_channels:
            for member in vc.members:
                if not member.bot:
                    m_id = str(member.id)
                    user_voice_time[g_id][m_id] = user_voice_time[g_id].get(m_id, 0) + 1
    save_data()

@voice_time_tracker.before_loop
async def before_v_tracker():
    await bot.wait_until_ready()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    g_id = message.guild.id if message.guild else 0
    u_id = message.author.id

    # 1. Anti-Abuse Check
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
                    await message.channel.send(embed=emb(title="⚠️ Anti-Abuse Triggered", description=f"{message.author.mention}, forbidden word detected! Timeout given."))
                elif punish_type == "kick":
                    await message.author.kick(reason="Using abuse words.")
                    await message.channel.send(embed=emb(title="⚠️ Anti-Abuse Triggered", description=f"{message.author.mention}, kicked from server."))
                elif punish_type == "ban":
                    await message.author.ban(reason="Using abuse words.")
                    await message.channel.send(embed=emb(title="⚠️ Anti-Abuse Triggered", description=f"{message.author.mention}, banned from server."))
                return
            except Exception as e:
                print(f"Anti-Abuse Error: {e}")

    # 2. Anti-Spam Check
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
                await message.channel.send(embed=emb(title="🛑 Anti-Spam Triggered", description=f"{message.author.mention}, slow down! Take a {timeout_min}-minute timeout."))
                return
            except Exception as e:
                print(f"Anti-Spam Error: {e}")

    # 3. Counting Check
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

    # Message Counter Track
    if g_id not in user_messages: user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    if u_id in afk_users:
        reason = afk_users.pop(u_id)
        await message.channel.send(embed=emb(title="Welcome Back", description=f"Welcome back, {message.author.mention}! AFK cleared."))

    await bot.process_commands(message)

# ==================== SECURITY & AUTOMOD ====================

@bot.command(name="antispam")
@commands.has_permissions(administrator=True)
async def anti_spam_toggle(ctx, status: str):
    g_id = ctx.guild.id
    st = status.lower()
    if st in ["on", "enable", "true"]:
        guild_antispam_status[g_id] = True
        save_data()
        await ctx.send(embed=emb(title="Anti-Spam", description="🛡️ Anti-Spam protection is **ENABLED**."))
    else:
        guild_antispam_status[g_id] = False
        save_data()
        await ctx.send(embed=emb(title="Anti-Spam", description="⚠️ Anti-Spam protection is **DISABLED**."))

@bot.command(name="setantispam")
@commands.has_permissions(administrator=True)
async def set_anti_spam(ctx, seconds: int, messages: int, timeout_minutes: int):
    g_id = ctx.guild.id
    guild_antispam_config[g_id] = {"seconds": seconds, "messages": messages, "timeout": timeout_minutes}
    save_data()
    await ctx.send(embed=emb(title="Anti-Spam Config", description=f"Updated rules: `{seconds}s`, `{messages} msgs`, `{timeout_minutes}m timeout`"))

@bot.command(name="antiabuse")
@commands.has_permissions(administrator=True)
async def anti_abuse_toggle(ctx, status: str):
    g_id = ctx.guild.id
    st = status.lower()
    if st in ["on", "enable", "true"]:
        guild_antiabuse_status[g_id] = True
        save_data()
        await ctx.send(embed=emb(title="Anti-Abuse", description="🛡️ Anti-Abuse filter is **ENABLED**."))
    else:
        guild_antiabuse_status[g_id] = False
        save_data()
        await ctx.send(embed=emb(title="Anti-Abuse", description="⚠️ Anti-Abuse filter is **DISABLED**."))

@bot.command(name="addabuse")
@commands.has_permissions(administrator=True)
async def add_abuse(ctx, *, words: str):
    g_id = ctx.guild.id
    if g_id not in guild_abuse_words: guild_abuse_words[g_id] = []
    added = [w.lower() for w in words.split() if w.lower() not in guild_abuse_words[g_id]]
    guild_abuse_words[g_id].extend(added)
    save_data()
    await ctx.send(embed=emb(title="Anti-Abuse Updated", description=f"Added words: {', '.join([f'`{w}`' for w in added])}"))

# ==================== MODERATION & CHANNELS ====================

@bot.command(name="addrole")
@commands.has_permissions(manage_roles=True)
async def add_role(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(embed=emb(title="Role Added", description=f"✅ Added {role.mention} to {member.mention}."))

@bot.command(name="removerole")
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(embed=emb(title="Role Removed", description=f"❌ Removed {role.mention} from {member.mention}."))

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

# ==================== STATS, COUNTS & LEADERBOARDS ====================

@bot.command(name="m", aliases=["messagecount"])
async def m_count(ctx, member: discord.Member = None):
    m = member or ctx.author
    count = user_messages.get(ctx.guild.id, {}).get(str(m.id), 0)
    await ctx.send(embed=emb(title="Message Count", description=f"{m.mention} has sent `{count}` messages."))

@bot.command(name="v", aliases=["voicecount"])
async def v_count(ctx, member: discord.Member = None):
    m = member or ctx.author
    mins = user_voice_time.get(ctx.guild.id, {}).get(str(m.id), 0)
    await ctx.send(embed=emb(title="Voice Time", description=f"{m.mention} has spent `{mins} minutes` in voice channels."))

@bot.command(name="i", aliases=["invitecount"])
async def i_count(ctx, member: discord.Member = None):
    m = member or ctx.author
    invs = user_invites.get(ctx.guild.id, {}).get(str(m.id), 0)
    await ctx.send(embed=emb(title="Invite Count", description=f"{m.mention} has `{invs}` invites."))

@bot.command(name="rm")
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, target: str = ""):
    if target.lower() == "all":
        user_messages[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=emb(title="Reset", description="✅ All user message counts have been reset."))
    else:
        await ctx.send(embed=emb(title="Error", description="Use `&rm all`"))

@bot.command(name="rv")
@commands.has_permissions(administrator=True)
async def reset_voice(ctx, target: str = ""):
    if target.lower() == "all":
        user_voice_time[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=emb(title="Reset", description="✅ All voice timing counts have been reset."))
    else:
        await ctx.send(embed=emb(title="Error", description="Use `&rv all`"))

@bot.command(name="ri")
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, target: str = ""):
    if target.lower() == "all":
        user_invites[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=emb(title="Reset", description="✅ All invite counts have been reset."))
    else:
        await ctx.send(embed=emb(title="Error", description="Use `&ri all`"))

@bot.command(name="lm")
async def leaderboard_messages(ctx):
    data = user_messages.get(ctx.guild.id, {})
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "\n".join([f"`{i+1}.` <@{uid}> - **{msgs}** msgs" for i, (uid, msgs) in enumerate(sorted_data)]) if sorted_data else "No data."
    await ctx.send(embed=emb(title="🏆 Message Leaderboard", description=desc))

@bot.command(name="lv")
async def leaderboard_voice(ctx):
    data = user_voice_time.get(ctx.guild.id, {})
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "\n".join([f"`{i+1}.` <@{uid}> - **{mins}** mins" for i, (uid, mins) in enumerate(sorted_data)]) if sorted_data else "No data."
    await ctx.send(embed=emb(title="🏆 Voice Leaderboard", description=desc))

@bot.command(name="li")
async def leaderboard_invites(ctx):
    data = user_invites.get(ctx.guild.id, {})
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "\n".join([f"`{i+1}.` <@{uid}> - **{invs}** invites" for i, (uid, invs) in enumerate(sorted_data)]) if sorted_data else "No data."
    await ctx.send(embed=emb(title="🏆 Invite Leaderboard", description=desc))

# ==================== UTILITY, SAY, REPLY & CLONE (EMOJI/STICKER) ====================

@bot.command(name="say")
@commands.has_permissions(manage_messages=True)
async def say_cmd(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command(name="reply")
@commands.has_permissions(manage_messages=True)
async def reply_cmd(ctx, msg_id: int, *, message: str):
    try:
        target_msg = await ctx.channel.fetch_message(msg_id)
        await target_msg.reply(message)
        await ctx.message.delete()
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(name="clone")
@commands.has_permissions(manage_emojis=True)
async def clone_cmd(ctx):
    if not ctx.message.reference:
        return await ctx.send(embed=emb(title="Error", description="Please reply to a message containing an emoji or a sticker with `clone`!"))
    
    try:
        replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        
        if replied_msg.stickers:
            sticker = replied_msg.stickers[0]
            file = await sticker.to_file()
            new_st = await ctx.guild.create_sticker(name=sticker.name, description=sticker.description or "Cloned Sticker", file=file, emoji="⭐")
            return await ctx.send(embed=emb(title="Sticker Cloned", description=f"✅ Successfully cloned sticker **{new_st.name}** into this server!"))
        
        content = replied_msg.content
        import re
        custom_emojis = re.findall(r'<a?:([a-zA-Z0-9_]+):([0-9]+)>', content)
        
        if custom_emojis:
            cloned_list = []
            for name, emoji_id in custom_emojis:
                animated = content.startswith(f"<a:{name}:{emoji_id}>")
                extension = "gif" if animated else "png"
                url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            new_emoji = await ctx.guild.create_custom_emoji(name=name, image=image_bytes)
                            cloned_list.append(str(new_emoji))
            
            if cloned_list:
                return await ctx.send(embed=emb(title="Emoji Cloned", description=f"✅ Successfully cloned emojis: {' '.join(cloned_list)}"))
        
        if replied_msg.reactions:
            for reaction in replied_msg.reactions:
                if not reaction.emoji.is_default():
                    e = reaction.emoji
                    url = e.url
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                image_bytes = await resp.read()
                                new_emoji = await ctx.guild.create_custom_emoji(name=e.name, image=image_bytes)
                                return await ctx.send(embed=emb(title="Emoji Cloned", description=f"✅ Successfully cloned reaction emoji {new_emoji}!"))

        await ctx.send(embed=emb(title="Error", description="No custom emoji or sticker found in the replied message!"))
    except Exception as e:
        await ctx.send(embed=emb(title="Error", description=f"Could not clone: {e}"))

@bot.command(name="giveaway")
@commands.has_permissions(manage_guild=True)
async def start_giveaway(ctx, minutes: int, *, prize: str):
    e = emb(title="🎉 GIVEAWAY 🎉", description=f"Prize: **{prize}**\nDuration: `{minutes} minutes`\nReact with 🎉 to enter!")
    msg = await ctx.send(embed=e)
    await msg.add_reaction("🎉")
    await asyncio.sleep(minutes * 60)
    
    new_msg = await ctx.channel.fetch_message(msg.id)
    users = [u async for u in new_msg.reactions[0].users() if not u.bot]
    if users:
        winner = random.choice(users)
        await ctx.send(embed=emb(title="🎉 Giveaway Ended!", description=f"Winner: {winner.mention} won **{prize}**! 🎁"))
    else:
        await ctx.send(embed=emb(title="🎉 Giveaway Ended!", description="No valid entries found."))

# ==================== STANDARD MODERATION & BAN ====================

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(embed=emb(title="User Banned", description=f"🔨 {member.mention} has been banned.\nReason: {reason}"))

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_user(ctx, member: discord.Member, *, reason="No reason"):
    await member.kick(reason=reason)
    await ctx.send(embed=emb(title="User Kicked", description=f"👢 {member.mention} has been kicked.\nReason: {reason}"))

@bot.command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute_user(ctx, member: discord.Member, minutes: int = 10, *, reason="No reason"):
    await member.timeout(timedelta(minutes=minutes), reason=reason)
    await ctx.send(embed=emb(title="Muted", description=f"🔇 {member.mention} muted for {minutes}m."))

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
    await ctx.send(embed=emb(title="Counting Initialized", description=f"Started in {target_channel.mention} at number {amount}."))

@bot.command(name="afk")
async def afk_cmd(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(embed=emb(title="AFK Activated", description=f"{ctx.author.mention} is now AFK.\nReason: {reason}"))

@bot.command(name="serverinfo", aliases=["si"])
async def server_info(ctx):
    g = ctx.guild
    desc = f"**General**\n• ID: `{g.id}`\n• Owner: `{g.owner}`\n• Members: `{g.member_count}`"
    await ctx.send(embed=emb(title=f"Server Info - {g.name}", description=desc))

@bot.command(name="userinfo", aliases=["ui"])
async def user_info(ctx, member: discord.Member = None):
    m = member or ctx.author
    desc = f"**User Info**\n• Name: `{m}`\n• ID: `{m.id}`"
    await ctx.send(embed=emb(title=f"User Info - {m.name}", description=desc))

# ==================== HELP MENU ====================

class MenuSelect(discord.ui.Select):
    def __init__(self, prefix):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Moderation & Ban", description="Ban, kick, mute, lock/hide/purge", emoji="🛠️"),
            discord.SelectOption(label="Stats & Ranks", description="m, v, i, lm, lv, li, rm all, rv all, ri all", emoji="📊"),
            discord.SelectOption(label="Security & Automod", description="Antispam, antiabuse", emoji="🛡️"),
            discord.SelectOption(label="Utility & Tools", description="Say, reply, clone emoji/sticker, giveaway", emoji="🎉")
        ]
        super().__init__(placeholder="CHOOSE A MODULE", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        p = self.prefix
        choice = self.values[0]
        if choice == "Moderation & Ban":
            desc = f"• `{p}ban` | `{p}kick` | `{p}mute`\n• `{p}lock` / `{p}unlock`\n• `{p}hide` / `{p}unhide`\n• `{p}purge`"
        elif choice == "Stats & Ranks":
            desc = f"• `{p}m`, `{p}v`, `{p}i` (counts)\n• `{p}lm`, `{p}lv`, `{p}li` (leaderboards)\n• `{p}rm all`, `{p}rv all`, `{p}ri all` (resets)"
        elif choice == "Security & Automod":
            desc = f"• `{p}antispam [on/off]`\n• `{p}setantispam`\n• `{p}antiabuse [on/off]`\n• `{p}addabuse`"
        else:
            desc = f"• `{p}say` | `{p}reply`\n• `{p}clone` (Reply to emoji/sticker)\n• `{p}giveaway`\n• `{p}start` (counting)"
        await interaction.response.edit_message(embed=emb(title=f"Module: {choice}", description=desc), view=self.view)

class MenuView(discord.ui.View):
    def __init__(self, prefix):
        super().__init__(timeout=180)
        self.add_item(MenuSelect(prefix))

@bot.command(name="help", aliases=["cmds", "menu"])
async def help_command(ctx):
    p = ctx.prefix
    desc = f"Hey, I'm Moonlight Heaven™\nPrefix: `{p}`\nAll systems are fully online!"
    e = discord.Embed(title="🤖 Moonlight Heaven Control Center", description=desc, color=0xFFFFFF)
    e.set_thumbnail(url=DEFAULT_THUMBNAIL)
    e.set_footer(text="Moonlight Heaven • Developed by Zeus")
    await ctx.send(embed=e, view=MenuView(p))

if __name__ == "__main__":
    keep_alive()
    voice_time_tracker.start()
    bot_token = os.getenv("bot_token")
    if bot_token:
        bot.run(bot_token)
    else:
        print("❌ Error: bot_token environment variable nahi mila!")
