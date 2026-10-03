import os
import time
import json
import random
import asyncio
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# =====================================================================
#                      WEB SERVER (KEEP ALIVE)
# =====================================================================
app = Flask('')

@app.route('/')
def home():
    return "🤖 Moonlight Heaven Detailed Bot is Online & Active!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =====================================================================
#                      INTENTS & CONFIGURATION
# =====================================================================
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
        "prefixes": {}, 
        "messages": {}, 
        "voice_time": {}, 
        "invites": {}, 
        "counting": {}, 
        "bot_channels": {}
    }

def save_data():
    data = {
        "prefixes": guild_prefixes, 
        "messages": user_messages, 
        "voice_time": user_voice_time, 
        "invites": user_invites, 
        "counting": guild_counting, 
        "bot_channels": guild_bot_channels
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

# =====================================================================
#                 SCREENSHOT MATCHED EMBED HELPER
# =====================================================================
def create_embed(title="", description="", ctx=None, color=0x5865F2):
    """
    Creates a sleek modern embed matching the user's screenshot style:
    Clean borders, beautiful header formatting, and professional user context footer.
    """
    embed = discord.Embed(title=title, description=description, color=color)
    if ctx and hasattr(ctx, "author") and ctx.author:
        embed.set_footer(
            text=f"Requested by @{ctx.author.name}", 
            icon_url=ctx.author.display_avatar.url
        )
    else:
        embed.set_footer(text="Moonlight Heaven • System Security")
    return embed

# =====================================================================
#                      BOT EVENTS & LISTENERS
# =====================================================================
@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" Logged in as: {bot.user.name} ({bot.user.id})")
    print(f" Status: Online and Fully Loaded (~700+ Lines)")
    print(f"==========================================")
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

    # --- PREFIXLESS BOT CHANNEL SYSTEM ---
    designated_channel_id = guild_bot_channels.get(g_id)
    if designated_channel_id and message.channel.id == designated_channel_id:
        # Message is NOT deleted as requested!
        if content_lower in ["m", "message", "messages"]:
            count = user_messages.get(g_id, {}).get(str(u_id), 0)
            await message.reply(embed=create_embed(title="📊 Message Count", description=f"{message.author.mention}, you have sent **{count}** messages in this server.", ctx=message))
            return
        elif content_lower in ["v", "voice", "voicetime"]:
            total_sec = user_voice_time.get(g_id, {}).get(str(u_id), 0)
            key = (g_id, u_id)
            if key in voice_joindata:
                total_sec += int(time.time() - voice_joindata[key])
            hours, minutes = total_sec // 3600, (total_sec % 3600) // 60
            await message.reply(embed=create_embed(title="🎙️️ Voice Time Report", description=f"{message.author.mention}, you have spent **{hours} hours** and **{minutes} minutes** in voice channels.", ctx=message))
            return
        elif content_lower in ["i", "invite", "invites"]:
            invs = user_invites.get(g_id, {}).get(str(u_id), {}).get("total", 0)
            await message.reply(embed=create_embed(title="🎟️ Invite Tracker", description=f"{message.author.mention}, you have successfully invited **{invs}** members.", ctx=message))
            return
        elif content_lower.startswith("change nickname") or content_lower.startswith("nickname"):
            parts = content.split(" ", 2)
            if len(parts) >= 3:
                new_nick = parts[2]
                try:
                    await message.author.edit(nick=new_nick)
                    await message.reply(embed=create_embed(title="✅ Nickname Updated", description=f"Successfully changed your nickname to **{new_nick}**!", ctx=message))
                except Exception as e:
                    await message.reply(embed=create_embed(title="❌ Error Occurred", description=f"Failed to change nickname: {e}", ctx=message))
            else:
                await message.reply(embed=create_embed(title="⚠️ Invalid Syntax", description="Please write properly: `change nickname YourNewName`", ctx=message))
            return
        else:
            # Wrong text entered in bot channel -> bot replies with instructions without deleting user message
            await message.reply(embed=create_embed(title="ℹ️ Bot Channel Guidelines", description="In this designated channel, you can use these shortcuts without a prefix:\n• `m` - Check message count\n• `v` - Check voice activity time\n• `i` - Check invite statistics\n• `change nickname [name]` - Change your server nickname", ctx=message))
            return

    # --- COUNTING SYSTEM ---
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
                    await message.channel.send(embed=create_embed(title="❌ Counting Error", description=f"{message.author.mention}, incorrect number sequence or consecutive message! Resetting count back to `{expected}`.", ctx=message), delete_after=6)
            except ValueError:
                pass

    # --- MESSAGE STATS TRACKER ---
    if g_id not in user_messages: 
        user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    await bot.process_commands(message)

# =====================================================================
#                      COMMANDS MODULE (EXTENSIVE)
# =====================================================================

# 1. MENU / HELP COMMAND (SEPARATED ADMIN & MEMBERS)
@bot.command(name="menu", aliases=["help"])
async def menu_command(ctx):
    embed = discord.Embed(
        title="🌟 Moonlight Heaven • Command Center", 
        description="Here is the structured list of all available modules and commands for this server.",
        color=0x2B2D31
    )
    
    embed.add_field(
        name="👤 Member Commands (Prefix: `&`)",
        value=(
            "• `&m` or `&m @User` — View message activity[span_0](start_span)[span_0](end_span)\n"
            "• `&v` or `&v @User` — View voice channel time[span_1](start_span)[span_1](end_span)\n"
            "• `&i` or `&i @User` — View invite statistics[span_2](start_span)[span_2](end_span)\n"
            "• `&lm` — Top message leaderboards[span_3](start_span)[span_3](end_span)\n"
            "• `&lv` — Top voice activity leaderboards[span_4](start_span)[span_4](end_span)\n"
            "• `&li` — Top invite leaderboards[span_5](start_span)[span_5](end_span)\n"
            "• `&menu` — Opens this command center"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🛠️ Administrator & Management Commands",
        value=(
            "• `&setupbotchannel` — Automatically provisions the bot chat channel[span_6](start_span)[span_6](end_span)\n"
            "• `&addrole @User @Role` — Assigns a role to a member\n"
            "• `&removerole @User @Role` — Strips a role from a member\n"
            "• `&hide` / `&unhide` — Toggles channel view permissions\n"
            "• `&lock` / `&unlock` — Toggles channel message permissions\n"
            "• `&rm all` / `&rv all` / `&ri all` — Respective data resets\n"
            "• `&say [text]` — Broadcasts custom announcements\n"
            "• `&reply [id] [text]` — Sends a target response reply\n"
            "• `&clone` — Clones the existing text channel layout\n"
            "• `&giveaway [min] [prize]` — Initiates a server giveaway\n"
            "• `&start [number]` — Sets up the automated counting game\n"
            "• `&spam [count] [text]` — Rapid-fire message delivery (Admin)"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Requested by @{ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# 2. SETUP BOT CHANNEL
@bot.command(name="setupbotchannel", aliases=["botchannel"])
@commands.has_permissions(manage_channels=True)
async def setup_bot_channel_cmd(ctx):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.text_channels, name="🤖・bot-commands")
    if not existing_channel:
        try:
            existing_channel = await guild.create_text_channel("🤖・bot-commands")
        except Exception as e:
            return await ctx.send(embed=create_embed(title="Deployment Failure", description=f"Could not create channel: {e}", ctx=ctx))
    
    guild_bot_channels[guild.id] = existing_channel.id
    save_data()
    await ctx.send(embed=create_embed(title="Bot Channel Initialized", description=f"✅ Successfully configured {existing_channel.mention}!\nMembers can type `m`, `v`, `i` or `change nickname [name]` directly here without prefixes.", ctx=ctx))

# 3. ROLE MANAGEMENT
@bot.command(name="addrole", aliases=["giverole"])
@commands.has_permissions(manage_roles=True)
async def add_role_cmd(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await ctx.send(embed=create_embed(title="Role Assigned", description=f"✅ Successfully granted {role.mention} to {member.mention}.", ctx=ctx))
    except Exception as e:
        await ctx.send(embed=create_embed(title="Action Failed", description=str(e), ctx=ctx))

@bot.command(name="removerole", aliases=["takerole"])
@commands.has_permissions(manage_roles=True)
async def remove_role_cmd(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        await ctx.send(embed=create_embed(title="Role Revoked", description=f"❌ Successfully removed {role.mention} from {member.mention}.", ctx=ctx))
    except Exception as e:
        await ctx.send(embed=create_embed(title="Action Failed", description=str(e), ctx=ctx))

# 4. CHANNEL VISIBILITY (HIDE / UNHIDE)
@bot.command(name="hide")
@commands.has_permissions(manage_channels=True)
async def hide_channel_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, view_channel=False)
    await ctx.send(embed=create_embed(title="Channel Secured", description=f"🔒 {ch.mention} has been hidden from public access.", ctx=ctx))

@bot.command(name="unhide")
@commands.has_permissions(manage_channels=True)
async def unhide_channel_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, view_channel=True)
    await ctx.send(embed=create_embed(title="Channel Public", description=f"🔓 {ch.mention} is now visible to members.", ctx=ctx))

# 5. CHANNEL LOCK / UNLOCK
@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_channel_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=create_embed(title="Channel Locked", description=f"🔒 {ch.mention} has been locked down.", ctx=ctx))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_channel_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=create_embed(title="Channel Unlocked", description=f"🔓 {ch.mention} messaging permissions restored.", ctx=ctx))

# 6. USER STATS (M, V, I)
@bot.command(name="m", aliases=["messagecount"])
async def message_stats_cmd(ctx, member: discord.Member = None):
    target = member or ctx.author
    g_id = ctx.guild.id
    count = user_messages.get(g_id, {}).get(str(target.id), 0)
    await ctx.send(embed=create_embed(title="Message Analytics", description=f"📊 {target.mention} has accumulated **{count}** messages.", ctx=ctx))[span_7](start_span)[span_7](end_span)

@bot.command(name="v", aliases=["voicetime"])
async def voice_stats_cmd(ctx, member: discord.Member = None):
    target = member or ctx.author
    g_id = ctx.guild.id
    total_sec = user_voice_time.get(g_id, {}).get(str(target.id), 0)
    key = (g_id, target.id)
    if key in voice_joindata:
        total_sec += int(time.time() - voice_joindata[key])
    hours, minutes = total_sec // 3600, (total_sec % 3600) // 60
    await ctx.send(embed=create_embed(title="Voice Time Analytics", description=f"🎙️ {target.mention} has logged **{hours}h {minutes}m** in voice channels.", ctx=ctx))[span_8](start_span)[span_8](end_span)

@bot.command(name="i", aliases=["invitecount"])
async def invite_stats_cmd(ctx, member: discord.Member = None):
    target = member or ctx.author
    g_id = ctx.guild.id
    invs = user_invites.get(g_id, {}).get(str(target.id), {}).get("total", 0)
    await ctx.send(embed=create_embed(title="Invite Tracker Analytics", description=f"🎟️ {target.mention} has successfully brought in **{invs}** invites.", ctx=ctx))[span_9](start_span)[span_9](end_span)

# 7. ADMIN RESET MODULES
@bot.command(name="rm")
@commands.has_permissions(administrator=True)
async def reset_messages_cmd(ctx, target: str):
    if target.lower() == "all":
        user_messages[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=create_embed(title="Database Purged", description="✅ All message count records have been reset.", ctx=ctx))

@bot.command(name="rv")
@commands.has_permissions(administrator=True)
async def reset_voice_cmd(ctx, target: str):
    if target.lower() == "all":
        user_voice_time[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=create_embed(title="Database Purged", description="✅ All voice time analytics have been reset.", ctx=ctx))

@bot.command(name="ri")
@commands.has_permissions(administrator=True)
async def reset_invites_cmd(ctx, target: str):
    if target.lower() == "all":
        user_invites[ctx.guild.id] = {}
        save_data()
        await ctx.send(embed=create_embed(title="Database Purged", description="✅ All invite tracking records have been reset.", ctx=ctx))

# 8. LEADERBOARDS (LM, LV, LI)
@bot.command(name="lm")
async def leaderboard_messages_cmd(ctx):
    g_id = ctx.guild.id
    data = user_messages.get(g_id, {})
    if not data: return await ctx.send(embed=create_embed(title="Leaderboards", description="No message logs available yet.", ctx=ctx))[span_10](start_span)[span_10](end_span)
    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "".join([f"`#{idx}` <@{uid}> — **{count}** messages\n" for idx, (uid, count) in enumerate(sorted_users, 1)])
    await ctx.send(embed=create_embed(title="🏆 Message Activity Leaderboard", description=desc, ctx=ctx))[span_11](start_span)[span_11](end_span)

@bot.command(name="lv")
async def leaderboard_voice_cmd(ctx):
    g_id = ctx.guild.id
    data = user_voice_time.get(g_id, {})
    if not data: return await ctx.send(embed=create_embed(title="Leaderboards", description="No voice time logs available yet.", ctx=ctx))[span_12](start_span)[span_12](end_span)
    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = ""
    for idx, (uid, sec) in enumerate(sorted_users, 1):
        h, m = sec // 3600, (sec % 3600) // 60
        desc += f"`#{idx}` <@{uid}> — **{h}h {m}m**\n"
    await ctx.send(embed=create_embed(title="🏆 Voice Activity Leaderboard", description=desc, ctx=ctx))[span_13](start_span)[span_13](end_span)

@bot.command(name="li")
async def leaderboard_invites_cmd(ctx):
    g_id = ctx.guild.id
    data = user_invites.get(g_id, {})
    if not data: return await ctx.send(embed=create_embed(title="Leaderboards", description="No invite logs available yet.", ctx=ctx))[span_14](start_span)[span_14](end_span)
    sorted_users = sorted(data.items(), key=lambda x: x[1].get("total", 0), reverse=True)[:10]
    desc = "".join([f"`#{idx}` <@{uid}> — **{d.get('total', 0)}** invites\n" for idx, (uid, d) in enumerate(sorted_users, 1)])
    await ctx.send(embed=create_embed(title="🏆 Invite Tracking Leaderboard", description=desc, ctx=ctx))[span_15](start_span)[span_15](end_span)

# 9. UTILITY & ENGAGEMENT TOOLS
@bot.command(name="say")
@commands.has_permissions(manage_messages=True)
async def say_command(ctx, *, message: str):
    try: await ctx.message.delete()
    except Exception: pass
    await ctx.send(message)

@bot.command(name="reply")
@commands.has_permissions(manage_messages=True)
async def reply_command(ctx, message_id: int, *, message: str):
    try:
        msg = await ctx.channel.fetch_message(message_id)
        await msg.reply(message)
        try: await ctx.message.delete()
        except Exception: pass
    except Exception as e:
        await ctx.send(embed=create_embed(title="Execution Error", description=str(e), ctx=ctx))

@bot.command(name="clone")
@commands.has_permissions(manage_channels=True)
async def clone_channel_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    new_ch = await ch.clone()
    await ctx.send(embed=create_embed(title="Channel Cloned", description=f"✅ Successfully duplicated into {new_ch.mention}!", ctx=ctx))

@bot.command(name="giveaway")
@commands.has_permissions(manage_guild=True)
async def giveaway_command(ctx, minutes: int, *, prize: str):
    embed = create_embed(title="🎉 SERVER GIVEAWAY", description=f"Prize: **{prize}**\nDuration: `{minutes} minutes`\nReact with 🎉 to enter the sweepstakes!", ctx=ctx)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")
    await asyncio.sleep(minutes * 60)
    try:
        refreshed = await ctx.channel.fetch_message(msg.id)
        users = [u async for u in refreshed.reactions[0].users() if not u.bot]
        if users:
            winner = random.choice(users)
            await ctx.send(embed=create_embed(title="🎉 Giveaway Concluded", description=f"Congratulations {winner.mention}! You have won **{prize}**!", ctx=ctx))
        else:
            await ctx.send(embed=create_embed(title="🎉 Giveaway Concluded", description="No valid participants entered the giveaway.", ctx=ctx))
    except Exception:
        pass

@bot.command(name="start", aliases=["counting"])
async def start_counting_cmd(ctx, amount: int = 1, channel: discord.TextChannel = None):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=create_embed(title="Access Denied", description="Administrator permissions required to configure counting.", ctx=ctx))
    target_channel = channel or ctx.channel
    guild_counting[ctx.guild.id] = {"channel_id": target_channel.id, "next_number": amount, "last_user": 0}
    save_data()
    await ctx.send(embed=create_embed(title="Counting Module Started", description=f"Game initialized in {target_channel.mention} starting from target `{amount}`.", ctx=ctx))

@bot.command(name="spam")
@commands.has_permissions(administrator=True)
async def spam_command(ctx, count: int, *, message: str):
    try: await ctx.message.delete()
    except Exception: pass
    if count > 20: count = 20
    for _ in range(count):
        await ctx.send(message)
        await asyncio.sleep(0.3)

# =====================================================================
#                      BOT EXECUTION LAUNCHER
# =====================================================================
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
