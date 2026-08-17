import os
import time
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# 1. Flask server to keep bot alive 24/7
app = Flask('')

@app.route('/')
def home():
    return "🤖 Bot is Alive and Running!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Bot Intents & Configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.bans = True
intents.invites = True

bot = commands.Bot(command_prefix="&", intents=intents)
bot.remove_command("help")

# Data Storage
user_messages = {}
user_invites = {}
user_voice_time = {}
voice_join_timestamps = {}
afk_users = {}
guild_logs = {}

def get_log_channel(guild_id, log_type):
    if guild_id in guild_logs and log_type in guild_logs[guild_id]:
        guild = bot.get_guild(guild_id)
        if guild:
            return guild.get_channel(guild_logs[guild_id][log_type])
    return None

@bot.event
async def on_ready():
    print(f"----------------------------------------")
    print(f"Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print(f"Status: Online & Ready!")
    print(f"----------------------------------------")


# --- TRACKING & LOG EVENTS ---

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
            embed = discord.Embed(
                title="💤 AFK Notice",
                description=f"**{user.name}** is currently AFK: {afk_users[user.id]}",
                color=discord.Color.blue()
            )
            await message.reply(embed=embed)

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
async def on_member_join(member):
    channel = get_log_channel(member.guild.id, 'member')
    if channel:
        embed = discord.Embed(
            title="📥 Member Joined",
            description=f"**User:** {member.mention} ({member.name})",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
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
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    user_id = member.id
    guild = member.guild
    channel = get_log_channel(guild.id, 'voice')

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


# --- SETUP COMMAND ---

@bot.command(name='setup')
@commands.has_permissions(administrator=True)
async def setup(ctx):
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
            title="⚙️ Setup Complete Successfully!",
            description=(
                f"✅ Created all 6 log channels:\n"
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
        await ctx.reply(embed=discord.Embed(title="❌ Error", description=str(e), color=discord.Color.red()))


# --- HELP & MENU COMMANDS ---

@bot.command(name='menu')
async def menu(ctx):
    embed = discord.Embed(title="📋 Ultimate Bot Menu", color=discord.Color.green())
    embed.add_field(name="⚙️ Setup", value="`&setup` (Auto creates all log channels)", inline=False)
    embed.add_field(name="📊 Stats", value="`&m`, `&i`, `&v`", inline=False)
    embed.add_field(name="🔄 Resets (Admin)", value="`&rm`, `&ri`, `&rv`", inline=False)
    embed.add_field(name="🛡️ Moderation", value="`&timeout`, `&kick`, `&ban`, `&unban`, `&clear`", inline=False)
    embed.add_field(name="💤 Utility", value="`&afk`", inline=False)
    await ctx.reply(embed=embed)


# --- STATS COMMANDS (Embed) ---

@bot.command(name='m')
async def check_messages(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = user_messages.get(target.id, 0)
    embed = discord.Embed(title="💬 Message Stats", description=f"**{target.mention}** has sent **{count}** messages.", color=discord.Color.blurple())
    await ctx.reply(embed=embed)

@bot.command(name='i')
async def check_invites(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = user_invites.get(target.id, 0)
    embed = discord.Embed(title="✉️ Invite Stats", description=f"**{target.mention}** has brought **{count}** invites.", color=discord.Color.green())
    await ctx.reply(embed=embed)

@bot.command(name='v')
async def check_voice(ctx, member: discord.Member = None):
    target = member or ctx.author
    secs = user_voice_time.get(target.id, 0)
    if target.id in voice_join_timestamps:
        secs += int(time.time() - voice_join_timestamps[target.id])
    hours, minutes = secs // 3600, (secs % 3600) // 60
    embed = discord.Embed(title="🎙️ Voice Time Stats", description=f"**{target.mention}** has spent **{hours}h {minutes}m** in voice.", color=discord.Color.gold())
    await ctx.reply(embed=embed)


# --- RESET COMMANDS (Admin Only, Embed) ---

@bot.command(name='rm')
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, member: discord.Member):
    user_messages[member.id] = 0
    embed = discord.Embed(title="🔄 Message Reset", description=f"Reset message count for **{member.mention}**.", color=discord.Color.orange())
    await ctx.reply(embed=embed)

@bot.command(name='ri')
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, member: discord.Member):
    user_invites[member.id] = 0
    embed = discord.Embed(title="🔄 Invite Reset", description=f"Reset invite count for **{member.mention}**.", color=discord.Color.orange())
    await ctx.reply(embed=embed)

@bot.command(name='rv')
@commands.has_permissions(administrator=True)
async def reset_voice(ctx, member: discord.Member):
    user_voice_time[member.id] = 0
    if member.id in voice_join_timestamps:
        voice_join_timestamps[member.id] = time.time()
    embed = discord.Embed(title="🔄 Voice Time Reset", description=f"Reset voice time for **{member.mention}**.", color=discord.Color.orange())
    await ctx.reply(embed=embed)


# --- MODERATION & UTILITY COMMANDS (Embed) ---

@bot.command(name='timeout')
@commands.has_permissions(moderate_members=True)
async def timeout_member(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    duration = discord.utils.utcnow() + discord.utils.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    embed = discord.Embed(title="🔇 Member Timed Out", description=f"**{member.mention}** has been timed out for **{minutes}m**.\nReason: {reason}", color=discord.Color.red())
    await ctx.reply(embed=embed)

@bot.command(name='afk')
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    embed = discord.Embed(title="💤 AFK Status Set", description=f"**{ctx.author.name}** is now AFK: {reason}", color=discord.Color.blue())
    await ctx.reply(embed=embed)

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    embed = discord.Embed(title="🛡️ Member Kicked", description=f"**{member.mention}** has been kicked.\nReason: {reason or 'None'}", color=discord.Color.orange())
    await ctx.reply(embed=embed)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 Member Banned", description=f"**{member.mention}** has been banned.\nReason: {reason or 'None'}", color=discord.Color.dark_red())
    await ctx.reply(embed=embed)

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    banned_users = await ctx.guild.bans()
    for ban_entry in banned_users:
        if ban_entry.user.name == member_name:
            await ctx.guild.unban(ban_entry.user)
            embed = discord.Embed(title="✅ Member Unbanned", description=f"Successfully unbanned **{ban_entry.user.mention}**.", color=discord.Color.green())
            await ctx.reply(embed=embed)
            return
    await ctx.reply(embed=discord.Embed(title="⚠️ Warning", description="User not found in ban list.", color=discord.Color.orange()))

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    embed = discord.Embed(title="🧹 Messages Cleared", description=f"Successfully deleted **{amount}** messages.", color=discord.Color.green())
    await ctx.send(embed=embed, delete_after=5)


# 4. Run Bot
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("TOKEN"))
