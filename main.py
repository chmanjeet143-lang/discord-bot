import os
import time
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# 1. Flask server to keep bot alive on Render 24/7
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


# --- EVENTS & NICKNAME CHANNEL LOGIC (No Message Delete) ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else None

    # Nickname change channel: Message will NOT be deleted, user message is kept, bot replies nicely with embed
    if guild_id and guild_id in guild_logs and 'nickname' in guild_logs[guild_id]:
        if message.channel.id == guild_logs[guild_id]['nickname']:
            try:
                new_nick = message.content
                await message.author.edit(nick=new_nick)
                
                # Clean, professional style embed matching your requested theme
                embed = discord.Embed(
                    title="Nickname Updated",
                    description=(
                        f"• **User** : {message.author.mention}\n"
                        f"• **New Nickname** : `{new_nick}`\n"
                        f"• **Status** : Successfully Changed ✨"
                    ),
                    color=discord.Color.from_rgb(40, 40, 40) # Clean dark/neutral accent matching screenshot vibe
                )
                await message.reply(embed=embed, delete_after=10)
                return
            except Exception as e:
                embed = discord.Embed(
                    title="Nickname Update Failed",
                    description=f"• **Reason** : `{e}`",
                    color=discord.Color.from_rgb(200, 50, 50)
                )
                await message.reply(embed=embed, delete_after=10)
                return

    author_id = message.author.id
    user_messages[author_id] = user_messages.get(author_id, 0) + 1

    # AFK Logic
    if author_id in afk_users:
        del afk_users[author_id]
        welcome_embed = discord.Embed(
            title="AFK Status Removed",
            description=f"• **Welcome Back** : {message.author.mention}\n• **Status** : AFK mode deactivated.",
            color=discord.Color.from_rgb(40, 40, 40)
        )
        await message.channel.send(embed=welcome_embed, delete_after=5)

    for user in message.mentions:
        if user.id in afk_users:
            embed = discord.Embed(
                title="User is AFK",
                description=f"• **User** : {user.mention}\n• **Reason** : {afk_users[user.id]}",
                color=discord.Color.from_rgb(40, 40, 40)
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
            title="Message Deleted",
            description=f"• **Author** : {message.author.mention}\n• **Channel** : {message.channel.mention}\n• **Content** : {message.content or '[Embed/Attachment]'}",
            color=discord.Color.from_rgb(40, 40, 40),
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    channel = get_log_channel(member.guild.id, 'member')
    if channel:
        embed = discord.Embed(
            title="Member Joined",
            description=f"• **User** : {member.mention}\n• **Name** : {member.name}",
            color=discord.Color.from_rgb(40, 40, 40),
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = get_log_channel(member.guild.id, 'member')
    if channel:
        embed = discord.Embed(
            title="Member Left",
            description=f"• **User** : {member.mention}\n• **Name** : {member.name}",
            color=discord.Color.from_rgb(40, 40, 40),
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
            embed = discord.Embed(title="Voice Join", description=f"• **User** : {member.mention}\n• **Channel** : {after.channel.name}", color=discord.Color.from_rgb(40, 40, 40), timestamp=discord.utils.utcnow())
            await channel.send(embed=embed)
    elif before.channel is not None and after.channel is None:
        if user_id in voice_join_timestamps:
            duration = int(time.time() - voice_join_timestamps[user_id])
            user_voice_time[user_id] = user_voice_time.get(user_id, 0) + duration
            del voice_join_timestamps[user_id]
        if channel:
            embed = discord.Embed(title="Voice Leave", description=f"• **User** : {member.mention}\n• **Channel** : {before.channel.name}", color=discord.Color.from_rgb(40, 40, 40), timestamp=discord.utils.utcnow())
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
        logs_ch = await guild.create_text_channel('logs', overwrites=overwrites)
        
        nick_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_nicknames=True)
        }
        nick_ch = await guild.create_text_channel('nickname-change', overwrites=nick_overwrites)

        guild_logs[guild.id] = {
            'member': member_ch.id,
            'message': msg_ch.id,
            'mod': mod_ch.id,
            'channel': channel_ch.id,
            'role': role_ch.id,
            'voice': voice_ch.id,
            'logs': logs_ch.id,
            'nickname': nick_ch.id
        }

        embed = discord.Embed(
            title="Setup Complete",
            description=(
                f"• **Status** : All channels created successfully.\n"
                f"• **Channels** : {member_ch.mention}, {msg_ch.mention}, {mod_ch.mention}, {channel_ch.mention}, {role_ch.mention}, {voice_ch.mention}, {logs_ch.mention}, {nick_ch.mention}"
            ),
            color=discord.Color.from_rgb(40, 40, 40)
        )
        await ctx.reply(embed=embed)
    except Exception as e:
        await ctx.reply(embed=discord.Embed(title="Error", description=f"• **Details** : `{e}`", color=discord.Color.from_rgb(200, 50, 50)))


# --- NICKNAMESETUP COMMAND ---

@bot.command(name='nicknamesetup')
@commands.has_permissions(administrator=True)
async def nicknamesetup(ctx):
    guild = ctx.guild
    nick_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_nicknames=True)
    }
    try:
        nick_ch = await guild.create_text_channel('nickname-change', overwrites=nick_overwrites)
        if guild.id not in guild_logs:
            guild_logs[guild.id] = {}
        guild_logs[guild.id]['nickname'] = nick_ch.id

        embed = discord.Embed(
            title="Nickname Setup Complete",
            description=f"• **Channel Created** : {nick_ch.mention}\n• **Usage** : Type your new nickname here directly.",
            color=discord.Color.from_rgb(40, 40, 40)
        )
        await ctx.reply(embed=embed)
    except Exception as e:
        await ctx.reply(embed=discord.Embed(title="Error", description=f"• **Details** : `{e}`", color=discord.Color.from_rgb(200, 50, 50)))


# --- MENU & SERVERINFO COMMANDS (Clean Theme) ---

@bot.command(name='menu')
async def menu(ctx):
    embed = discord.Embed(
        title="Bot Command Menu",
        description=(
            f"• **Setups** : `&setup`, `&nicknamesetup`\n"
            f"• **Information** : `&si`\n"
            f"• **Statistics** : `&m`, `&i`, `&v`\n"
            f"• **Admin Resets** : `&rm`, `&ri`, `&rv`\n"
            f"• **Moderation** : `&timeout`, `&kick`, `&ban`, `&unban`, `&clear`\n"
            f"• **Utility** : `&afk`, `&say`, `&reply`"
        ),
        color=discord.Color.from_rgb(40, 40, 40)
    )
    await ctx.reply(embed=embed)

@bot.command(name='si')
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title="Server Information",
        description=(
            f"• **Server Name** : `{guild.name}`\n"
            f"• **Server ID** : `{guild.id}`\n"
            f"• **Owner** : {guild.owner.mention if guild.owner else 'Unknown'}\n"
            f"• **Total Members** : `{guild.member_count}`\n"
            f"• **Verification Level** : `{str(guild.verification_level).capitalize()}`"
        ),
        color=discord.Color.from_rgb(40, 40, 40),
        timestamp=discord.utils.utcnow()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.reply(embed=embed)


# --- STATS COMMANDS ---

@bot.command(name='m')
async def check_messages(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = user_messages.get(target.id, 0)
    embed = discord.Embed(
        title="Message Statistics",
        description=f"• **User** : {target.mention}\n• **Total Messages** : `{count}`",
        color=discord.Color.from_rgb(40, 40, 40)
    )
    await ctx.reply(embed=embed)

@bot.command(name='i')
async def check_invites(ctx, member: discord.Member = None):
    target = member or ctx.author
    count = user_invites.get(target.id, 0)
    embed = discord.Embed(
        title="Invite Statistics",
        description=f"• **User** : {target.mention}\n• **Total Invites** : `{count}`",
        color=discord.Color.from_rgb(40, 40, 40)
    )
    await ctx.reply(embed=embed)

@bot.command(name='v')
async def check_voice(ctx, member: discord.Member = None):
    target = member or ctx.author
    secs = user_voice_time.get(target.id, 0)
    if target.id in voice_join_timestamps:
        secs += int(time.time() - voice_join_timestamps[target.id])
    hours, minutes = secs // 3600, (secs % 3600) // 60
    embed = discord.Embed(
        title="Voice Time Statistics",
        description=f"• **User** : {target.mention}\n• **Time Spent** : `{hours}h {minutes}m`",
        color=discord.Color.from_rgb(40, 40, 40)
    )
    await ctx.reply(embed=embed)


# --- RESET COMMANDS ---

@bot.command(name='rm')
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, member: discord.Member):
    user_messages[member.id] = 0
    embed = discord.Embed(title="Message Reset", description=f"• **User** : {member.mention}\n• **Status** : Count reset to 0.", color=discord.Color.from_rgb(40, 40, 40))
    await ctx.reply(embed=embed)

@bot.command(name='ri')
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, member: discord.Member):
    user_invites[member.id] = 0
    embed = discord.Embed(title="Invite Reset", description=f"• **User** : {member.mention}\n• **Status** : Count reset to 0.", color=discord.Color.from_rgb(40, 40, 40))
    await ctx.reply(embed=embed)

@bot.command(name='rv')
@commands.has_permissions(administrator=True)
async def reset_voice(ctx, member: discord.Member):
    user_voice_time[member.id] = 0
    if member.id in voice_join_timestamps:
        voice_join_timestamps[member.id] = time.time()
    embed = discord.Embed(title="Voice Time Reset", description=f"• **User** : {member.mention}\n• **Status** : Time reset to 0.", color=discord.Color.from_rgb(40, 40, 40))
    await ctx.reply(embed=embed)


# --- UTILITY & MODERATION COMMANDS ---

@bot.command(name='say')
async def say(ctx, *, message: str):
    await ctx.message.delete()
    embed = discord.Embed(description=f"• **Announcement** :\n{message}", color=discord.Color.from_rgb(40, 40, 40))
    await ctx.send(embed=embed)

@bot.command(name='reply')
async def reply_msg(ctx, message_link: str, *, message: str):
    try:
        parts = message_link.split('/')
        channel = bot.get_channel(int(parts[-2])) or await bot.fetch_channel(int(parts[-2]))
        target_message = await channel.fetch_message(int(parts[-1]))
        embed = discord.Embed(description=f"• **Reply** :\n{message}", color=discord.Color.from_rgb(40, 40, 40))
        await target_message.reply(embed=embed)
        await ctx.message.delete()
    except Exception as e:
        embed = discord.Embed(title="Error", description=f"• **Details** : `{e}`", color=discord.Color.from_rgb(200, 50, 50))
        await ctx.reply(embed=embed)

@bot.command(name='timeout')
@commands.has_permissions(moderate_members=True)
async def timeout_member(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    duration = discord.utils.utcnow() + discord.utils.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    embed = discord.Embed(title="Member Timed Out", description=f"• **User** : {member.mention}\n• **Duration** : `{minutes} minutes`\n• **Reason** : {reason}", color=discord.Color.from_rgb(40, 40, 40))
    await ctx.reply(embed=embed)

@bot.command(name='afk')
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    embed = discord.Embed(title="AFK Mode Activated", description=f"• **User** : {ctx.author.mention}\n• **Reason** : {reason}", color=discord.Color.from_rgb(40, 40, 40))
    await ctx.reply(embed=embed)

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    embed = discord.Embed(title="Member Kicked", description=f"• **User** : {member.mention}\n• **Reason** : {reason or 'None'}", color=discord.Color.from_rgb(40, 40, 40))
    await ctx.reply(embed=embed)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    embed = discord.Embed(title="Member Banned", description=f"• **User** : {member.mention}\n• **Reason** : {reason or 'None'}", color=discord.Color.from_rgb(40, 40, 40))
    await ctx.reply(embed=embed)

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    banned_users = await ctx.guild.ans() if hasattr(ctx.guild, 'bans') else await ctx.guild.bans()
    for ban_entry in banned_users:
        if ban_entry.user.name == member_name:
            await ctx.guild.unban(ban_entry.user)
            embed = discord.Embed(title="Member Unbanned", description=f"• **User** : {ban_entry.user.mention}", color=discord.Color.from_rgb(40, 40, 40))
            await ctx.reply(embed=embed)
            return
    embed = discord.Embed(title="Warning", description="• **Status** : User not found in ban list.", color=discord.Color.from_rgb(200, 50, 50))
    await ctx.reply(embed=embed)

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    embed = discord.Embed(title="Messages Cleared", description=f"• **Deleted** : `{amount}` messages.", color=discord.Color.from_rgb(40, 40, 40))
    await ctx.send(embed=embed, delete_after=5)


# 4. Run Bot
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("TOKEN"))
