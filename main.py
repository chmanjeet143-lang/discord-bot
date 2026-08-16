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

# 2. Bot Intents & Configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True

bot = commands.Bot(command_prefix="&", intents=intents)
bot.remove_command("help")

# Data Storage
user_messages = {}
user_invites = {}
user_voice_time = {} 
voice_join_timestamps = {}
afk_users = {}

# 3. Bot Ready Event
@bot.event
async def on_ready():
    print(f"----------------------------------------")
    print(f"Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print(f"Status: Online & Ready!")
    print(f"----------------------------------------")


# --- EVENTS FOR TRACKING STATS & AFK ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    author_id = message.author.id
    user_messages[author_id] = user_messages.get(author_id, 0) + 1

    if author_id in afk_users:
        del afk_users[author_id]
        await message.channel.send(f"Welcome back {message.author.mention}, I removed your AFK status!", delete_after=5)

    for user in message.mentions:
        if user.id in afk_users:
            reason = afk_users[user.id]
            await message.reply(f"💤 **{user.name}** is currently AFK: {reason}")

    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    user_id = member.id

    if before.channel is None and after.channel is not None:
        voice_join_timestamps[user_id] = time.time()
    elif before.channel is not None and after.channel is None:
        if user_id in voice_join_timestamps:
            duration = int(time.time() - voice_join_timestamps[user_id])
            user_voice_time[user_id] = user_voice_time.get(user_id, 0) + duration
            del voice_join_timestamps[user_id]


# --- CUSTOM HELP COMMAND ---

@bot.command(name='help')
async def custom_help(ctx):
    embed = discord.Embed(
        title="🤖 Bot Help Menu",
        description="Here are the available commands categorized below:",
        color=discord.Color.blurple()
    )
    
    embed.add_field(
        name="🛡️ Moderation Commands",
        value=(
            "**`&kick [user] [reason]`** - Kick a member.\n"
            "**`&ban [user] [reason]`** - Ban a member.\n"
            "**`&unban [username]`** - Unban a member.\n"
            "**`&clear [amount]`** - Delete messages."
        ),
        inline=False
    )
    
    embed.add_field(
        name="📊 Stats & Utility Commands",
        value=(
            "**`&m [user]`** - Check message count.\n"
            "**`&i [user]`** - Check invite count.\n"
            "**`&v [user]`** - Check voice channel time.\n"
            "**`&afk [reason]`** - Set your AFK status.\n"
            "**`&say [msg]`** - Bot repeats your text.\n"
            "**`&reply [link] [msg]`** - Reply to a message link."
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.reply(embed=embed)


# --- MENU COMMAND ---

@bot.command(name='menu')
async def menu(ctx):
    embed = discord.Embed(
        title="📋 Bot Feature Menu",
        description="Here is everything I can do for you in this server:",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="🛡️ Moderation Tools",
        value="**`&kick`** | **`&ban`** | **`&unban`** | **`&clear`**",
        inline=False
    )
    
    embed.add_field(
        name="📊 Stats & Tracking Tools",
        value="**`&m`** (Messages) | **`&i`** (Invites) | **`&v`** (Voice Time) | **`&afk`** (AFK Setup)",
        inline=False
    )

    embed.add_field(
        name="🛠️ Reset Tools (Admin)",
        value="**`&rm`** (Reset Messages) | **`&ri`** (Reset Invites) | **`&rv`** (Reset Voice Time)",
        inline=False
    )
    
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.reply(embed=embed)


# --- STATS COMMANDS (&m, &i, &v) - [AESTHETIC EMBED UPDATED] ---

@bot.command(name='m')
async def check_messages(ctx, member: discord.Member = None):
    """Check message count in a stylish embed"""
    target = member or ctx.author
    count = user_messages.get(target.id, 0)
    
    # Server total messages (approximation ya storage ke mutabiq)
    total_server_msgs = sum(user_messages.values())

    embed = discord.Embed(
        title="💬 Message Stats",
        description=f"» 🤍 **{target.name}**'s Messages",
        color=0x00b0b0
    )
    embed.add_field(
        name="\u200b",
        value=f"• **All time:** `{total_server_msgs}` messages in this server !\n• **Today / User Total:** `{count}` messages sent.",
        inline=False
    )
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.name} • Today")
    await ctx.reply(embed=embed)

@bot.command(name='i')
async def check_invites(ctx, member: discord.Member = None):
    """Check invite count in a stylish embed (Jaise image mein hai)"""
    target = member or ctx.author
    count = user_invites.get(target.id, 0)

    embed = discord.Embed(
        title="Invite log",
        description=f"» 🤍 **{target.name}** has **{count}** invites",
        color=0x00b0b0
    )
    embed.add_field(
        name="\u200b",
        value=f"• Joins : **{count}**\n• Left : **0**\n• Fake : **0**\n• Rejoins : **0** *(7d)*",
        inline=False
    )
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.name} • Today")
    await ctx.reply(embed=embed)

@bot.command(name='v')
async def check_voice(ctx, member: discord.Member = None):
    target = member or ctx.author
    total_seconds = user_voice_time.get(target.id, 0)
    
    if target.id in voice_join_timestamps:
        total_seconds += int(time.time() - voice_join_timestamps[target.id])

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    embed = discord.Embed(
        title="🎙️ Voice Channel Stats",
        description=f"» 🎙️ **{target.name}** Voice Activity",
        color=0x00b0b0
    )
    embed.add_field(
        name="\u200b",
        value=f"• **Total Time:** **{hours} hours and {minutes} minutes**",
        inline=False
    )
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    await ctx.reply(embed=embed)


# --- RESET COMMANDS (&rm, &ri, &rv) ---

@bot.command(name='rm')
@commands.has_permissions(administrator=True)
async def reset_messages(ctx, member: discord.Member):
    user_messages[member.id] = 0
    await ctx.reply(f"🔄 Successfully reset message count for **{member.name}**.")

@bot.command(name='ri')
@commands.has_permissions(administrator=True)
async def reset_invites(ctx, member: discord.Member):
    user_invites[member.id] = 0
    await ctx.reply(f"🔄 Successfully reset invite count for **{member.name}**.")

@bot.command(name='rv')
@commands.has_permissions(administrator=True)
async def reset_voice(ctx, member: discord.Member):
    user_voice_time[member.id] = 0
    if member.id in voice_join_timestamps:
        voice_join_timestamps[member.id] = time.time()
    await ctx.reply(f"🔄 Successfully reset voice time for **{member.name}**.")


# --- AFK COMMAND ---

@bot.command(name='afk')
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.reply(f"💤 **{ctx.author.name}** is now AFK: {reason}")


# --- UTILITY COMMANDS (Say & Reply) ---

@bot.command(name='say')
async def say(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command(name='reply')
async def reply_msg(ctx, message_link: str, *, message: str):
    try:
        parts = message_link.split('/')
        channel_id = int(parts[-2])
        message_id = int(parts[-1])
        
        channel = bot.get_channel(channel_id)
        if not channel:
            channel = await bot.fetch_channel(channel_id)
            
        target_message = await channel.fetch_message(message_id)
        await target_message.reply(message)
        await ctx.message.delete()
    except Exception as e:
        await ctx.reply(f"❌ Could not process link or error occurred: {e}")


# --- MODERATION COMMANDS ---

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.reply(f"🛡️ **{member.mention}** has been kicked.")

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
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
    await ctx.reply(f"⚠️ User not found in ban list.")

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted {amount} messages.", delete_after=5)


# 4. Run the Keep-Alive server and Bot
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("TOKEN"))
