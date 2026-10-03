import os
import time
import json
import random
import asyncio
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# ==================== WEB SERVER (KEEP ALIVE) ====================
app = Flask('')

@app.route('/')
def home():
    return "🤖 Moonlight Heaven Bot is Online!"

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
intents.invites = True

DATA_FILE = "bot_database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "prefixes": {}, "messages": {}, "voice_time": {}, "invites": {}, "counting": {}, "bot_channels": {}
    }

def save_data():
    data = {
        "prefixes": guild_prefixes, "messages": user_messages, 
        "voice_time": user_voice_time, "invites": user_invites, 
        "counting": guild_counting, "bot_channels": guild_bot_channels
    }
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

db = load_data()
guild_prefixes = {int(k): v for k, v in db.get("prefixes", {}).items()}
user_messages = {int(k): v for k, v in db.get("messages", {}).items()}
user_voice_time = {int(k): v for k, v in db.get("voice_time", {}).items()}
user_invites = {int(k): v for k, v in db.get("invites", {}).items()}
guild_counting = {int(k): v for k, v in db.get("counting", {}).items()}
guild_bot_channels = {int(k): v for k, v in db.get("bot_channels", {}).items()}

def get_prefix(bot, message):
    if not message.guild:
        return "&"
    return guild_prefixes.get(message.guild.id, "&")

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command("help")

voice_joindata = {}
cached_invites = {}

# Sleek ZEON-style modern embed helper
def emb(title="", description="", ctx=None, color=0x2B2D31):
    embed = discord.Embed(title=title, description=description, color=color)
    if ctx and hasattr(ctx, "author") and ctx.author:
        embed.set_footer(text=f"Requested by @{ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    else:
        embed.set_footer(text="Moonlight Heaven • Bot")
    return embed

@bot.event
async def on_ready():
    print("Bot is ready and running perfectly!")
    for guild in bot.guilds:
        try:
            cached_invites[guild.id] = await guild.invites()
        except Exception:
            pass

@bot.event
async def on_member_join(member):
    guild = member.guild
    g_id = guild.id
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
            if g_id not in user_invites: 
                user_invites[g_id] = {}
            inv_id = str(inviter.id)
            if inv_id not in user_invites[g_id]:
                user_invites[g_id][inv_id] = {"total": 0}
            user_invites[g_id][inv_id]["total"] += 1
            save_data()
    except Exception:
        pass

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

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return
    
    if not message.guild:
        return
    
    g_id = message.guild.id
    u_id = message.author.id
    content = message.content.strip()
    content_lower = content.lower()

    # 1. Check if message is in the auto-setup Bot Channel (Prefix-less triggers)
    designated_channel_id = guild_bot_channels.get(g_id)
    if designated_channel_id and message.channel.id == designated_channel_id:
        try:
            # Delete user's raw message for a clean bot-chat experience
            await message.delete()
        except Exception:
            pass
        
        # Prefix-less shortcuts handling
        if content_lower in ["m", "message", "messages"]:
            count = user_messages.get(g_id, {}).get(str(u_id), 0)
            await message.channel.send(embed=emb(title="📊 Message Count", description=f"{message.author.mention} has sent **{count}** messages.", ctx=message))
            return
            
        elif content_lower in ["v", "voice", "voicetime"]:
            total_sec = user_voice_time.get(g_id, {}).get(str(u_id), 0)
            key = (g_id, u_id)
            if key in voice_joindata:
                total_sec += int(time.time() - voice_joindata[key])
            hours, minutes = total_sec // 3600, (total_sec % 3600) // 60
            await message.channel.send(embed=emb(title="🎙️ Voice Time", description=f"{message.author.mention} has spent **{hours}h {minutes}m** in voice.", ctx=message))
            return
            
        elif content_lower in ["i", "invite", "invites"]:
            invs = user_invites.get(g_id, {}).get(str(u_id), {}).get("total", 0)
            await message.channel.send(embed=emb(title="🎟️ Invite Count", description=f"{message.author.mention} has successfully invited **{invs}** members.", ctx=message))
            return
            
        elif content_lower.startswith("change nickname") or content_lower.startswith("nickname"):
            parts = content.split(" ", 2)
            if len(parts) >= 3:
                new_nick = parts[2]
                try:
                    await message.author.edit(nick=new_nick)
                    await message.channel.send(embed=emb(title="✅ Nickname Changed", description=f"Successfully changed your nickname to **{new_nick}**!", ctx=message), delete_after=5)
                except Exception as e:
                    await message.channel.send(embed=emb(title="❌ Error", description=f"Could not change nickname: {e}", ctx=message), delete_after=5)
            else:
                await message.channel.send(embed=emb(title="⚠️ Usage", description="Please write like: `change nickname YourNewName`", ctx=message), delete_after=5)
            return

    # 2. Counting System Check
    if g_id in guild_counting:
        c_data = guild_counting[g_id]
        if message.channel.id == c_data.get("channel_id"):
            try:
                number = int(content)
                expected = c_data.get("next_number", 1)
                last_user = c_data.get("last_user", 0)
                
                if number == expected and u_id != last_user:
                    c_data["next_number"] = expected + 1
                    c_data["last_user"] = u_id
                    save_data()
                    try:
                        await message.add_reaction("✅")
                    except Exception:
                        pass
                else:
                    await message.add_reaction("❌")
                    await message.channel.send(embed=emb(title="❌ Counting Failed", description=f"{message.author.mention}, wrong number or consecutive message! Reset back to `{expected}`.", ctx=message), delete_after=6)
            except ValueError:
                pass

    # Message count tracker
    if g_id not in user_messages: 
        user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    await bot.process_commands(message)

# ==================== COMMANDS ====================

# Setup Bot Channel Command (Auto creates channel)
@bot.command(name="setupbotchannel", aliases=["botchannel"])
@commands.has_permissions(manage_channels=True)
async def setup_bot_channel(ctx):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.text_channels, name="🤖・bot-commands")
    if not existing_channel:
        try:
            existing_channel = await guild.create_text_channel("🤖・bot-commands")
        except Exception as e:
            return await ctx.send(embed=emb(title="Error", description=f"Could not create channel: {e}", ctx=ctx))
    
    guild_bot_channels[guild.id] = existing_channel.id
    save_data()
    await ctx.send(embed=emb(title="Bot Channel Ready", description=f"✅ Successfully set up {existing_channel.mention}!\nUsers can now type `m`, `v`, `i`, or `change nickname [name]` here without any prefix!", ctx=ctx))

# Add / Remove Role
@bot.command(name="addrole", aliases=["giverole"])
@commands.has_permissions(manage_roles=True)
async def add_role(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await ctx.send(embed=emb(title="Role Added", description=f"✅ Added {role.mention} to {member.mention}.", ctx=ctx))
    except Exception as e:
        await ctx.send(embed=emb(title="Error", description=str(e), ctx=ctx))

@bot.command(name="removerole", aliases=["takerole"])
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        await ctx.send(embed=emb(title="Role Removed", description=f"❌ Removed {role.mention} from {member.mention}.", ctx=ctx))
    except Exception as e:
        await ctx.send(embed=emb(title="Error", description=str(e), ctx=ctx))

# Hide / Unhide Channel
@bot.command(name="hide")
@commands.has_permissions(manage_channels=True)
async def hide_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, view_channel=False)
    await ctx.send(embed=emb(title="Channel Hidden", description=f"🔒 {ch.mention} is now hidden.", ctx=ctx))

@bot.command(name="unhide")
@commands.has_permissions(manage_channels=True)
async def unhide_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, view_channel=True)
    await ctx.send(embed=emb(title="Channel Unhidden", description=f"🔓 {ch.mention} is now visible.", ctx=ctx))

# Lock / Unlock Channel
@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=emb(title="Channel Locked", description=f"🔒 {ch.mention} has been locked.", ctx=ctx))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=emb(title="Channel Unlocked", description=f"🔓 {ch.mention} has been unlocked.", ctx=ctx))

# Stats Commands (m, v, i)
@bot.command(name="m", aliases=["messagecount"])
async def message_count_cmd(ctx, member: discord.Member = None):
    m = member or ctx.author
    g_id = ctx.guild.id
    count = user_messages.get(g_id, {}).get(str(m.id), 0)
    await ctx.send(embed=emb(title="Message Count", description=f"📊 {m.mention} has sent **{count}** messages.", ctx=ctx))

@bot.command(name="v", aliases=["voicetime"])
async def voice_time_cmd(ctx, member: discord.Member = None):
    m = member or ctx.author
    g_id = ctx.guild.id
    total_sec = user_voice_time.get(g_id, {}).get(str(m.id), 0)
    key = (g_id, m.id)
    if key in voice_joindata:
        total_sec += int(time.time() - voice_joindata[key])
    hours, minutes = total_sec // 3600, (total_sec % 3600) // 60
    await ctx.send(embed=emb(title="Voice Time", description=f"🎙️ {m.mention} has spent **{hours}h {minutes}m** in voice.", ctx=ctx))

@bot.command(name="i", aliases=["invitecount"])
async def invite_count_cmd(ctx, member: discord.Member = None):
    m = member or ctx.author
    g_id = ctx.guild.id
    invs = user_invites.get(g_id, {}).get(str(m.id), {}).get("total", 0)
    await ctx.send(embed=emb(title="Invite Count", description=f"🎟️ {m.mention} has successfully invited **{invs}** members.", ctx=ctx))

# Resets (rm all, rv all, ri all)
@bot.command(name="rm")
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, target: str):
    if target.lower() == "all":
        user_messages[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=emb(title="Reset Complete", description="✅ All message counts have been reset.", ctx=ctx))

@bot.command(name="rv")
@commands.has_permissions(administrator=True)
async def reset_voice(ctx, target: str):
    if target.lower() == "all":
        user_voice_time[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=emb(title="Reset Complete", description="✅ All voice time counts have been reset.", ctx=ctx))

@bot.command(name="ri")
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, target: str):
    if target.lower() == "all":
        user_invites[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=emb(title="Reset Complete", description="✅ All invite counts have been reset.", ctx=ctx))

# Leaderboards (lm, lv, li)
@bot.command(name="lm")
async def leaderboard_messages(ctx):
    g_id = ctx.guild.id
    m_data = user_messages.get(g_id, {})
    if not m_data: return await ctx.send(embed=emb(title="Leaderboard", description="No data found.", ctx=ctx))
    sorted_users = sorted(m_data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "".join([f"`#{idx}` <@{uid}> — **{count}** msgs\n" for idx, (uid, count) in enumerate(sorted_users, 1)])
    await ctx.send(embed=emb(title="🏆 Top Message Leaderboard", description=desc, ctx=ctx))

@bot.command(name="lv")
async def leaderboard_voice(ctx):
    g_id = ctx.guild.id
    v_data = user_voice_time.get(g_id, {})
    if not v_data: return await ctx.send(embed=emb(title="Leaderboard", description="No data found.", ctx=ctx))
    sorted_users = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = ""
    for idx, (uid, sec) in enumerate(sorted_users, 1):
        h, m = sec // 3600, (sec % 3600) // 60
        desc += f"`#{idx}` <@{uid}> — **{h}h {m}m**\n"
    await ctx.send(embed=emb(title="🏆 Top Voice Leaderboard", description=desc, ctx=ctx))

@bot.command(name="li")
async def leaderboard_invites(ctx):
    g_id = ctx.guild.id
    i_data = user_invites.get(g_id, {})
    if not i_data: return await ctx.send(embed=emb(title="Leaderboard", description="No data found.", ctx=ctx))
    sorted_users = sorted(i_data.items(), key=lambda x: x[1].get("total", 0), reverse=True)[:10]
    desc = "".join([f"`#{idx}` <@{uid}> — **{data.get('total', 0)}** invites\n" for idx, (uid, data) in enumerate(sorted_users, 1)])
    await ctx.send(embed=emb(title="🏆 Top Invite Leaderboard", description=desc, ctx=ctx))

# Say & Reply
@bot.command(name="say")
@commands.has_permissions(manage_messages=True)
async def say_cmd(ctx, *, message: str):
    try: await ctx.message.delete()
    except Exception: pass
    await ctx.send(message)

@bot.command(name="reply")
@commands.has_permissions(manage_messages=True)
async def reply_cmd(ctx, message_id: int, *, message: str):
    try:
        msg = await ctx.channel.fetch_message(message_id)
        await msg.reply(message)
        try: await ctx.message.delete()
        except Exception: pass
    except Exception as e:
        await ctx.send(embed=emb(title="Error", description=str(e), ctx=ctx))

# Clone & Giveaway
@bot.command(name="clone")
@commands.has_permissions(manage_channels=True)
async def clone_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    new_ch = await ch.clone()
    await ctx.send(embed=emb(title="Channel Cloned", description=f"✅ Cloned into {new_ch.mention}!", ctx=ctx))

@bot.command(name="giveaway")
@commands.has_permissions(manage_guild=True)
async def start_giveaway(ctx, minutes: int, *, prize: str):
    e = emb(title="🎉 GIVEAWAY", description=f"Prize: **{prize}**\nDuration: `{minutes} minutes`\nReact with 🎉 to enter!", ctx=ctx)
    msg = await ctx.send(embed=e)
    await msg.add_reaction("🎉")
    await asyncio.sleep(minutes * 60)
    try:
        new_msg = await ctx.channel.fetch_message(msg.id)
        users = [u async for u in new_msg.reactions[0].users() if not u.bot]
        if users:
            winner = random.choice(users)
            await ctx.send(embed=emb(title="🎉 Giveaway Winner!", description=f"Congratulations {winner.mention}! You won **{prize}**!", ctx=ctx))
        else:
            await ctx.send(embed=emb(title="🎉 Giveaway Ended", description="No valid entries.", ctx=ctx))
    except Exception:
        pass

# Counting Start Command
@bot.command(name="start", aliases=["counting"])
@commands.has_permissions(administrator=True)
async def start_counting(ctx, amount: int = 1, channel: discord.TextChannel = None):
    target_channel = channel or ctx.channel
    guild_counting[ctx.guild.id] = {"channel_id": target_channel.id, "next_number": amount, "last_user": 0}
    save_data()
    await ctx.send(embed=emb(title="Counting Initialized", description=f"Counting game started in {target_channel.mention} starting from `{amount}`.", ctx=ctx))

# Spam Command (Admin only)
@bot.command(name="spam")
@commands.has_permissions(administrator=True)
async def spam_cmd(ctx, count: int, *, message: str):
    try: await ctx.message.delete()
    except Exception: pass
    if count > 20: count = 20
    for _ in range(count):
        await ctx.send(message)
        await asyncio.sleep(0.4)

# ==================== BOT START ====================
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
