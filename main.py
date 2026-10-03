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
    return "🤖 Moonlight Heaven Bot is Online & Fully Active!"

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
#                 CLEAN EMBED HELPER
# =====================================================================
def create_embed(title="", description="", ctx=None, color=0x2B2D31):
    embed = discord.Embed(title=title, description=description, color=color)
    if ctx and hasattr(ctx, "author") and ctx.author:
        embed.set_footer(
            text=f"Requested by @{ctx.author.name}", 
            icon_url=ctx.author.display_avatar.url
        )
    else:
        embed.set_footer(text="Moonlight Heaven • Security & Utility")
    return embed

# =====================================================================
#                 INTERACTIVE HELP MENU (BUTTONS & SELECT)
# =====================================================================
class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🏠 Home Menu", description="Main dashboard overview", emoji="🏠"),
            discord.SelectOption(label="🛡 Moderation & Setup", description="Roles, channels, reset tools", emoji="🛡️"),
            discord.SelectOption(label="👤 Member & Stats", description="Messages, voice time, invites & leaderboards", emoji="📊"),
            discord.SelectOption(label="⚙ Utility & Games", description="Say, reply, clone, giveaway, counting", emoji="🎮")
        ]
        super().__init__(placeholder="📂 Select a command category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        embed = discord.Embed(color=0x2B2D31)
        
        if "Home" in val:
            embed.title = "🌟 Moonlight Heaven • Command Center"
            embed.description = "Welcome to the interactive help panel! Select a category from the dropdown menu below."
            embed.add_field(name="Modules Available", value="• Moderation & Reset Tools\n• Member Stats & Leaderboards\n• Utility & Mini Games", inline=False)
        elif "Moderation" in val:
            embed.title = "🛡️ Moderation, Setup & Reset Commands"
            embed.description = "Manage server structures and data resets."
            embed.add_field(name="`&addrole / &removerole`", value="Manage user roles.\n*Usage:* `&addrole @User @Role`", inline=False)
            embed.add_field(name="`&hide / &unhide`", value="Toggle channel visibility.", inline=False)
            embed.add_field(name="`&lock / &unlock`", value="Toggle channel chat permissions.", inline=False)
            embed.add_field(name="`&rm all`", value="Reset all user message tracking data.", inline=False)
            embed.add_field(name="`&rv all`", value="Reset all user voice time tracking data.", inline=False)
            embed.add_field(name="`&ri all`", value="Reset all user invite tracking data.", inline=False)
        elif "Member" in val:
            embed.title = "👤 Member Stats & Leaderboards"
            embed.description = "Track individual activity and check server rankings."
            embed.add_field(name="`&m / &v / &i`", value="Check message, voice time or invite counts.\n*Usage:* `&m` or `&m @User`", inline=False)
            embed.add_field(name="`&lm / &lv / &li`", value="View server leaderboards for messages, voice & invites.", inline=False)
            embed.add_field(name="`&setupbotchannel`", value="Setup prefixless bot channel.", inline=False)
        elif "Utility" in val:
            embed.title = "⚙️ Utility, Fun & Mini Games"
            embed.description = "Broadcast messages, reply, clone, giveaways and counting."
            embed.add_field(name="`&say [message]`", value="Send announcement text.", inline=False)
            embed.add_field(name="`&reply [message_id] [text]`", value="Reply to a specific message.", inline=False)
            embed.add_field(name="`&clone`", value="Clone current channel layout.", inline=False)
            embed.add_field(name="`&giveaway [minutes] [prize]`", value="Start a giveaway.", inline=False)
            embed.add_field(name="`&start [number] [channel] [emoji]`", value="Start counting game.", inline=False)

        embed.set_footer(text=f"Requested by @{interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpSelect())

# =====================================================================
#                      BOT EVENTS & LISTENERS
# =====================================================================
@bot.event
async def on_ready():
    print(f"==========================================")
    print(f" Logged in as: {bot.user.name} ({bot.user.id})")
    print(f" Status: Online with Full Command Suite")
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
            await message.reply(embed=create_embed(title="🎙 Voice Time Report", description=f"{message.author.mention}, you have spent **{hours} hours** and **{minutes} minutes** in voice channels.", ctx=message))
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
            await message.reply(embed=create_embed(title="ℹ️ Bot Channel Guidelines", description="Use these shortcuts here:\n• `m` - Message count\n• `v` - Voice time\n• `i` - Invite count\n• `change nickname [name]` - Change nickname", ctx=message))
            return

    # --- COUNTING SYSTEM ---
    if g_id in guild_counting:
        c_data = guild_counting[g_id]
        if message.channel.id == c_data.get("channel_id"):
            try:
                number = int(content)
                expected = c_data.get("next_number", 1)
                last_user = c_data.get("last_user", 0)
                success_emoji = c_data.get("emoji", "✅")
                
                if number == expected and u_id != last_user:
                    c_data["next_number"] = expected + 1
                    c_data["last_user"] = u_id
                    save_data()
                    try:
                        await message.add_reaction(success_emoji)
                    except Exception:
                        pass
                else:
                    await message.add_reaction("❌")
                    await message.channel.send(embed=create_embed(title="❌ Counting Error", description=f"{message.author.mention}, incorrect number or consecutive message! Next expected number is `{expected}`.", ctx=message), delete_after=6)
            except ValueError:
                pass

    # --- MESSAGE STATS TRACKER ---
    if g_id not in user_messages: 
        user_messages[g_id] = {}
    user_messages[g_id][str(u_id)] = user_messages[g_id].get(str(u_id), 0) + 1
    save_data()

    await bot.process_commands(message)

# =====================================================================
#                      COMMANDS MODULE
# =====================================================================

# 1. HELP / MENU COMMAND
@bot.command(name="menu", aliases=["help"])
async def menu_command(ctx):
    embed = discord.Embed(
        title="🌟 Moonlight Heaven • Command Center", 
        description="Welcome to the interactive help panel! Select a category from the dropdown menu below.",
        color=0x2B2D31
    )
    embed.add_field(name="Modules Available", value="• Moderation & Reset Tools\n• Member Stats & Leaderboards\n• Utility & Mini Games", inline=False)
    embed.set_footer(text=f"Requested by @{ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed, view=HelpView())

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
    await ctx.send(embed=create_embed(title="Bot Channel Initialized", description=f"✅ Successfully configured {existing_channel.mention}!", ctx=ctx))

# 3. ROLE MANAGEMENT
@bot.command(name="addrole", aliases=["giverole"])
@commands.has_permissions(manage_roles=True)
async def add_role_cmd(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await ctx.send(embed=create_embed(title="Role Assigned", description=f"✅ Granted {role.mention} to {member.mention}.", ctx=ctx))
    except Exception as e:
        await ctx.send(embed=create_embed(title="Action Failed", description=str(e), ctx=ctx))

@bot.command(name="removerole", aliases=["takerole"])
@commands.has_permissions(manage_roles=True)
async def remove_role_cmd(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        await ctx.send(embed=create_embed(title="Role Revoked", description=f"❌ Removed {role.mention} from {member.mention}.", ctx=ctx))
    except Exception as e:
        await ctx.send(embed=create_embed(title="Action Failed", description=str(e), ctx=ctx))

# 4. CHANNEL VISIBILITY & PERMISSIONS
@bot.command(name="hide")
@commands.has_permissions(manage_channels=True)
async def hide_channel_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, view_channel=False)
    await ctx.send(embed=create_embed(title="Channel Secured", description=f"🔒 {ch.mention} has been hidden.", ctx=ctx))

@bot.command(name="unhide")
@commands.has_permissions(manage_channels=True)
async def unhide_channel_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, view_channel=True)
    await ctx.send(embed=create_embed(title="Channel Public", description=f"🔓 {ch.mention} is now visible.", ctx=ctx))

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_channel_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=create_embed(title="Channel Locked", description=f"🔒 {ch.mention} has been locked.", ctx=ctx))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_channel_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=create_embed(title="Channel Unlocked", description=f"🔓 {ch.mention} messaging restored.", ctx=ctx))

# 5. USER STATS COMMANDS (`m`, `v`, `i`)
@bot.command(name="m", aliases=["messagecount"])
async def message_stats_cmd(ctx, member: discord.Member = None):
    target = member or ctx.author
    g_id = ctx.guild.id
    count = user_messages.get(g_id, {}).get(str(target.id), 0)
    await ctx.send(embed=create_embed(title="Message Analytics", description=f"📊 {target.mention} has accumulated **{count}** messages.", ctx=ctx))[span_0](start_span)[span_0](end_span)

@bot.command(name="v", aliases=["voicetime", "voice timing count"])
async def voice_stats_cmd(ctx, member: discord.Member = None):
    target = member or ctx.author
    g_id = ctx.guild.id
    total_sec = user_voice_time.get(g_id, {}).get(str(target.id), 0)
    key = (g_id, target.id)
    if key in voice_joindata:
        total_sec += int(time.time() - voice_joindata[key])
    hours, minutes = total_sec // 3600, (total_sec % 3600) // 60
    await ctx.send(embed=create_embed(title="Voice Time Analytics", description=f"🎙️ {target.mention} has logged **{hours}h {minutes}m** in voice channels.", ctx=ctx))[span_1](start_span)[span_1](end_span)

@bot.command(name="i", aliases=["invitecount"])
async def invite_stats_cmd(ctx, member: discord.Member = None):
    target = member or ctx.author
    g_id = ctx.guild.id
    invs = user_invites.get(g_id, {}).get(str(target.id), {}).get("total", 0)
    await ctx.send(embed=create_embed(title="Invite Tracker Analytics", description=f"🎟️ {target.mention} has successfully brought in **{invs}** invites.", ctx=ctx))[span_2](start_span)[span_2](end_span)

# 6. RESET COMMANDS (`rm all`, `rv all`, `ri all`)
@bot.command(name="rm")
@commands.has_permissions(administrator=True)
async def reset_messages_cmd(ctx, option: str = None):
    if option and option.lower() == "all":
        g_id = ctx.guild.id
        if g_id in user_messages:
            user_messages[g_id] = {}
            save_data()
        await ctx.send(embed=create_embed(title="Data Reset Successful", description="✅ All user message logs have been reset to 0.", ctx=ctx))
    else:
        await ctx.send(embed=create_embed(title="Invalid Syntax", description="Please use: `&rm all`", ctx=ctx))

@bot.command(name="rv")
@commands.has_permissions(administrator=True)
async def reset_voice_cmd(ctx, option: str = None):
    if option and option.lower() == "all":
        g_id = ctx.guild.id
        if g_id in user_voice_time:
            user_voice_time[g_id] = {}
            save_data()
        await ctx.send(embed=create_embed(title="Data Reset Successful", description="✅ All user voice time logs have been reset to 0.", ctx=ctx))
    else:
        await ctx.send(embed=create_embed(title="Invalid Syntax", description="Please use: `&rv all`", ctx=ctx))

@bot.command(name="ri")
@commands.has_permissions(administrator=True)
async def reset_invites_cmd(ctx, option: str = None):
    if option and option.lower() == "all":
        g_id = ctx.guild.id
        if g_id in user_invites:
            user_invites[g_id] = {}
            save_data()
        await ctx.send(embed=create_embed(title="Data Reset Successful", description="✅ All user invite logs have been reset to 0.", ctx=ctx))
    else:
        await ctx.send(embed=create_embed(title="Invalid Syntax", description="Please use: `&ri all`", ctx=ctx))

# 7. LEADERBOARDS (`lm`, `lv`, `li`)
@bot.command(name="lm", aliases=["leaderboard msg"])
async def leaderboard_messages_cmd(ctx):
    g_id = ctx.guild.id
    data = user_messages.get(g_id, {})
    if not data: return await ctx.send(embed=create_embed(title="Leaderboards", description="No message logs available yet.", ctx=ctx))[span_3](start_span)[span_3](end_span)
    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "".join([f"`#{idx}` <@{uid}> — **{count}** messages\n" for idx, (uid, count) in enumerate(sorted_users, 1)])
    await ctx.send(embed=create_embed(title="🏆 Message Activity Leaderboard", description=desc, ctx=ctx))[span_4](start_span)[span_4](end_span)

@bot.command(name="lv", aliases=["leaderboard voice"])
async def leaderboard_voice_cmd(ctx):
    g_id = ctx.guild.id
    data = user_voice_time.get(g_id, {})
    if not data: return await ctx.send(embed=create_embed(title="Leaderboards", description="No voice time logs available yet.", ctx=ctx))[span_5](start_span)[span_5](end_span)
    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = ""
    for idx, (uid, sec) in enumerate(sorted_users, 1):
        h, m = sec // 3600, (sec % 3600) // 60
        desc += f"`#{idx}` <@{uid}> — **{h}h {m}m**\n"
    await ctx.send(embed=create_embed(title="🏆 Voice Activity Leaderboard", description=desc, ctx=ctx))[span_6](start_span)[span_6](end_span)

@bot.command(name="li", aliases=["leaderboard invite"])
async def leaderboard_invites_cmd(ctx):
    g_id = ctx.guild.id
    data = user_invites.get(g_id, {})
    if not data: return await ctx.send(embed=create_embed(title="Leaderboards", description="No invite logs available yet.", ctx=ctx))[span_7](start_span)[span_7](end_span)
    sorted_users = sorted(data.items(), key=lambda x: x[1].get("total", 0), reverse=True)[:10]
    desc = "".join([f"`#{idx}` <@{uid}> — **{d.get('total', 0)}** invites\n" for idx, (uid, d) in enumerate(sorted_users, 1)])
    await ctx.send(embed=create_embed(title="🏆 Invite Tracking Leaderboard", description=desc, ctx=ctx))[span_8](start_span)[span_8](end_span)

# 8. UTILITIES & GAMES (`say`, `reply`, `clone`, `giveaway`, `start`)
@bot.command(name="say")
@commands.has_permissions(manage_messages=True)
async def say_command(ctx, *, message: str):
    try: await ctx.message.delete()
    except Exception: pass
    await ctx.send(message)

@bot.command(name="reply")
@commands.has_permissions(manage_messages=True)
async def reply_command(ctx, message_id: int, *, text: str):
    try:
        msg = await ctx.channel.fetch_message(message_id)
        await msg.reply(text)
        try: await ctx.message.delete()
        except Exception: pass
    except Exception as e:
        await ctx.send(embed=create_embed(title="Reply Failed", description=f"Could not find message ID: {e}", ctx=ctx), delete_after=5)

@bot.command(name="clone")
@commands.has_permissions(manage_channels=True)
async def clone_channel_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    new_ch = await ch.clone()
    await ctx.send(embed=create_embed(title="Channel Cloned", description=f"✅ Successfully duplicated into {new_ch.mention}!", ctx=ctx))

@bot.command(name="giveaway")
@commands.has_permissions(manage_guild=True)
async def giveaway_command(ctx, minutes: int, *, prize: str):
    embed = create_embed(title="🎉 SERVER GIVEAWAY", description=f"Prize: **{prize}**\nDuration: `{minutes} minutes`\nReact with 🎉 to enter!", ctx=ctx)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")
    await asyncio.sleep(minutes * 60)
    try:
        refreshed = await ctx.channel.fetch_message(msg.id)
        users = [u async for u in refreshed.reactions[0].users() if not u.bot]
        if users:
            winner = random.choice(users)
            await ctx.send(embed=create_embed(title="🎉 Giveaway Concluded", description=f"Congratulations {winner.mention}! You won **{prize}**!", ctx=ctx))
        else:
            await ctx.send(embed=create_embed(title="🎉 Giveaway Concluded", description="No valid participants entered.", ctx=ctx))
    except Exception:
        pass

@bot.command(name="start")
@commands.has_permissions(administrator=True)
async def start_counting_cmd(ctx, number: int, channel: discord.TextChannel, emoji: str):
    guild_counting[ctx.guild.id] = {
        "channel_id": channel.id, 
        "next_number": number, 
        "last_user": 0,
        "emoji": emoji
    }
    save_data()
    await ctx.send(embed=create_embed(title="Counting Module Started", description=f"✅ Counting game successfully initialized in {channel.mention} starting from `{number}` with success emoji {emoji}.", ctx=ctx))

# =====================================================================
#                      BOT EXECUTION LAUNCHER
# =====================================================================
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("TOKEN")
    if TOKEN:
        bot.run(TOKEN)
