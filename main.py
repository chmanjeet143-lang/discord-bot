import os
import time
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# 1. Flask server to keep the bot alive on Render 24/7
app = Flask('')

@app.route('/')
def home():
    return "🤖 Bot is Alive and Running!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Bot Intents & Configuration (All Intents Enabled for Full Logging)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True
intents.guilds = True
intents.bans = True

bot = commands.Bot(command_prefix="&", intents=intents)
bot.remove_command("help")

# Data Storage
user_messages = {}
user_invites = {}
user_voice_time = {}
voice_join_timestamps = {}
afk_users = {}

# Guild wise log channels storage: {guild_id: {type: channel_id}}
guild_logs = {}

# 3. Bot Ready Event
@bot.event
async def on_ready():
    print(f"----------------------------------------")
    print(f"Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print(f"Status: Online & Ready!")
    print(f"----------------------------------------")


# --- ADVANCED LOGGING EVENTS ---

def get_log_channel(guild_id, log_type):
    if guild_id in guild_logs and log_type in guild_logs[guild_id]:
        guild = bot.get_guild(guild_id)
        if guild:
            return guild.get_channel(guild_logs[guild_id][log_type])
    return None

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    author_id = message.author.id
    user_messages[author_id] = user_messages.get(author_id, 0) + 1

    # AFK Logic
    if author_id in afk_users:
        del afk_users[author_id]
        await message.channel.send(f"Welcome back {message.author.mention}, I removed your AFK status!", delete_after=5)

    for user in message.mentions:
        if user.id in afk_users:
            reason = afk_users[user.id]
            await message.reply(f"💤 **{user.name}** is currently AFK: {reason}")

    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return
    channel = get_log_channel(message.guild.id, 'message')
    if channel:
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            description=f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Content:** {message.content or '[Embed/Attachment]'}",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or not before.guild or before.content == after.content:
        return
    channel = get_log_channel(before.guild.id, 'message')
    if channel:
        embed = discord.Embed(
            title="✏️ Message Edited",
            description=f"**Author:** {before.author.mention}\n**Channel:** {before.channel.mention}\n**Before:** {before.content}\n**After:** {after.content}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    channel = get_log_channel(member.guild.id, 'member')
    if channel:
        embed = discord.Embed(
            title="📥 Member Joined",
            description=f"**User:** {member.mention} ({member.name})\n**Created At:** {member.created_at.strftime('%Y-%m-%d')}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = get_log_channel(member.guild.id, 'member')
    if channel:
        embed = discord.Embed(
            title="📤 Member Left",
            description=f"**User:** {member.mention} ({member.name})",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    # Timeout log
    if before.timed_out_until != after.timed_out_until and after.timed_out_until is not None:
        channel = get_log_channel(after.guild.id, 'mod')
        if channel:
            embed = discord.Embed(
                title="🔇 Member Timed Out",
                description=f"**User:** {after.mention}\n**Until:** {after.timed_out_until}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await channel.send(embed=embed)

@bot.event
async def on_guild_channel_create(channel_obj):
    channel = get_log_channel(channel_obj.guild.id, 'channel')
    if channel:
        embed = discord.Embed(
            title="📁 Channel Created",
            description=f"**Name:** {channel_obj.name} ({channel_obj.type})",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel_obj):
    channel = get_log_channel(channel_obj.guild.id, 'channel')
    if channel:
        embed = discord.Embed(
            title="❌ Channel Deleted",
            description=f"**Name:** {channel_obj.name}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)

@bot.event
async def on_guild_role_create(role):
    channel = get_log_channel(role.guild.id, 'role')
    if channel:
        embed = discord.Embed(
            title="✨ Role Created",
            description=f"**Role:** {role.mention}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)

@bot.event
async def on_guild_role_delete(role):
    channel = get_log_channel(role.guild.id, 'role')
    if channel:
        embed = discord.Embed(
            title="🗑️ Role Deleted",
            description=f"**Role Name:** {role.name}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    user_id = member.id
    guild = member.guild
    channel = get_log_channel(guild.id, 'voice')

    # Voice Time tracking logic
    if before.channel is None and after.channel is not None:
        voice_join_timestamps[user_id] = time.time()
        if channel:
            embed = discord.Embed(title="🎙️ Voice Join", description=f"**User:** {member.mention} joined **{after.channel.name}**", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
            await channel.send(embed=embed)
    elif before.channel is not None and after.channel is None:
        if user_id in voice_join_timestamps:
            duration = int(time.time() - voice_join_timestamps[user_id])
            user_voice_time[user_id] = user_voice_time.get(user_id, 0) + duration
            del voice_join_timestamps[user_id]
        if channel:
            embed = discord.Embed(title="🎙️ Voice Leave", description=f"**User:** {member.mention} left **{before.channel.name}**", color=discord.Color.orange(), timestamp=discord.utils.utcnow())
            await channel.send(embed=embed)


# --- AUTO SETUP COMMAND (`&setup`) ---

@bot.command(name='setup')
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """Automatically creates all requested log channels"""
    guild = ctx.guild
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }

    try:
        member_ch = await guild.create_text_channel('member-logs', overwrites=overwrites)
        msg_ch = await guild.create_text_channel('message-logs', overwrites=overwrites)
        mod_ch = await guild.create_text_channel('moderation-logs', overwrites=overwrites)
        channel_ch = await guild.create_text_channel('channel-logs', overwrites=overwrites)
        role_ch = await guild.create_text_channel('role-logs', overwrites=overwrites)
        voice_ch = await guild.create_text_channel('voice-logs', overwrites=overwrites)

        guild_logs[guild.id] = {
            'member': member_ch.id,
            'message': msg_ch.id,
            'mod': mod_ch.id,
            'channel': channel_ch.id,
            'role': role_ch.id,
            'voice': voice_ch.id
        }

        embed = discord.Embed(
            title="⚙️ All Logs Setup Complete Successfully!",
            description=(
                f"✅ Created channels:\n"
                f"• {member_ch.mention}\n"
                f"• {msg_ch.mention}\n"
                f"• {mod_ch.mention}\n"
                f"• {channel_ch.mention}\n"
                f"• {role_ch.mention}\n"
                f"• {voice_ch.mention}"
            ),
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed)
    except Exception as e:
        await ctx.reply(f"❌ Error during setup: {e}")


# --- CUSTOM HELP & MENU ---

@bot.command(name='help')
async def custom_help(ctx):
    embed = discord.Embed(title="🤖 Bot Help Menu", color=discord.Color.blurple())
    embed.add_field(name="🛡️ Moderation & Setup", value="`&setup`, `&timeout`, `&kick`, `&ban`, `&unban`, `&clear`", inline=False)
    embed.add_field(name="📊 Stats & Utility", value="`&m`, `&i`, `&v`, `&afk`, `&say`, `&reply`", inline=False)
    await ctx.reply(embed=embed)

@bot.command(name='menu')
async def menu(ctx):
    embed = discord.Embed(title="📋 Bot Feature Menu", color=discord.Color.green())
    embed.add_field(name="⚙️ Setup", value="`&setup` (Creates all 6 log channels automatically)", inline=False)
    embed.add_field(name="🛡️ Moderation", value="`&timeout`, `&kick`, `&ban`, `&unban`, `&clear`", inline=False)
    embed.add_field(name="📊 Stats & Reset", value="`&m`, `&i`, `&v`, `&afk` | Reset: `&rm`, `&ri`, `&rv`", inline=False)
    await ctx.reply(embed=embed)


# --- STATS & RESET COMMANDS ---

@bot.command(name='m')
async def check_messages(ctx, member: discord.Member = None):
    target = member or ctx.author
    await ctx.reply(f"💬 **{target.name}** has sent **{user_messages.get(target.id, 0)}** messages.")

@bot.command(name='i')
async def check_invites(ctx, member: discord.Member = None):
    target = member or ctx.author
    await ctx.reply(f"✉️ **{target.name}** has brought **{user_invites.get(target.id, 0)}** invites.")

@bot.command(name='v')
async def check_voice(ctx, member: discord.Member = None):
    target = member or ctx.author
    secs = user_voice_time.get(target.id, 0)
    if target.id in voice_join_timestamps:
        secs += int(time.time() - voice_join_timestamps[target.id])
    await ctx.reply(f"🎙️ **{target.name}** spent **{secs // 3600}h {(secs % 3600) // 60}m** in voice.")

@bot.command(name='rm')
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, member: discord.Member):
    user_messages[member.id] = 0
    await ctx.reply(f"🔄 Reset messages for **{member.name}**.")

@bot.command(name='ri')
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, member: discord.Member):
    user_invites[member.id] = 0
    await ctx.reply(f"🔄 Reset invites for **{member.name}**.")

@bot.command(name='rv')
@commands.has_permissions(administrator=True)
async def reset_voice(ctx, member: discord.Member):
    user_voice_time[member.id] = 0
    await ctx.reply(f"🔄 Reset voice time for **{member.name}**.")


# --- MODERATION COMMANDS ---

@bot.command(name='timeout')
@commands.has_permissions(moderate_members=True)
async def timeout_member(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    duration = discord.utils.utcnow() + discord.utils.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.reply(f"🔇 **{member.mention}** has been timed out for {minutes} minutes.")

@bot.command(name='afk')
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.reply(f"💤 **{ctx.author.name}** is now AFK: {reason}")

@bot.command(name='say')
async def say(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command(name='reply')
async def reply_msg(ctx, message_link: str, *, message: str):
    try:
        parts = message_link.split('/')
        channel = bot.get_channel(int(parts[-2])) or await bot.fetch_channel(int(parts[-2]))
        target_message = await channel.fetch_message(int(parts[-1]))
        await target_message.reply(message)
        await ctx.message.delete()
    except Exception as e:
        await ctx.reply(f"❌ Error: {e}")

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    channel = get_log_channel(ctx.guild.id, 'mod')
    if channel:
        await channel.send(f"🛡️ **{member}** was kicked by {ctx.author.mention}. Reason: {reason}")
    await ctx.reply(f"🛡️ **{member.mention}** has been kicked.")

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    channel = get_log_channel(ctx.guild.id, 'mod')
    if channel:
        await channel.send(f"🔨 **{member}** was banned by {ctx.author.mention}. Reason: {reason}")
    await ctx.reply(f"🔨 **{member.mention}** has been banned.")

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    banned_users = await ctx.guild.bans()
    for ban_entry in banned_users:
        if ban_entry.user.name == member_name:
            await ctx.guild.unban(ban_entry.user)
            await ctx.reply(f"✅ Unbanned **{ban_entry.user.mention}**.")
            return
    await ctx.reply(f"⚠️ User not found.")

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted {amount} messages.", delete_after=5)


# 4. Run Bot
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("TOKEN"))
