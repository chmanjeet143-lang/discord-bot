Bilkul, agar aapke Render environment variable mein key ka naam sirf TOKEN rakha hua hai, toh hum code mein bhi wahi change kar dete hain taaki koi mismatch na ho.
Neeche poora code hai, aur sabse last wali line mein DISCORD_TOKEN ki jagah sirf TOKEN kar diya gaya hai:
import os
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

bot = commands.Bot(command_prefix="&", intents=intents)
bot.remove_command("help")

# 3. Bot Ready Event
@bot.event
async def on_ready():
    print(f"----------------------------------------")
    print(f"Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print(f"Status: Online & Ready!")
    print(f"----------------------------------------")


# --- CUSTOM HELP COMMAND ---

@bot.command(name='help')
async def custom_help(ctx):
    """Shows the categorized help menu"""
    embed = discord.Embed(
        title="🤖 Bot Help Menu",
        description="Here are the available commands categorized below:",
        color=discord.Color.blurple()
    )
    
    embed.add_field(
        name="🛡️ Moderation Commands",
        value=(
            "**`&kick [user] [reason]`** - Kick a member from the server.\n"
            "**`&ban [user] [reason]`** - Ban a member from the server.\n"
            "**`&unban [username]`** - Unban a member by name.\n"
            "**`&clear [amount]`** - Delete messages in bulk."
        ),
        inline=False
    )
    
    embed.add_field(
        name="🛠️ Utility Commands",
        value=(
            "**`&say [message]`** - Make the bot say something.\n"
            "**`&reply [message_link] [message]`** - Reply to a specific message link."
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.reply(embed=embed)


# --- MENU COMMAND ---

@bot.command(name='menu')
async def menu(ctx):
    """Shows the complete feature menu of the bot"""
    embed = discord.Embed(
        title="📋 Bot Feature Menu",
        description="Here is everything I can do for you in this server:",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="🛡️ Moderation Tools",
        value=(
            "**`&kick`** - Remove a member from the server.\n"
            "**`&ban`** - Permanently ban a member.\n"
            "**`&unban`** - Revoke a ban from a user.\n"
            "**`&clear`** - Bulk delete chat messages."
        ),
        inline=False
    )
    
    embed.add_field(
        name="🛠️ Utility & Chat Tools",
        value=(
            "**`&say`** - Make the bot repeat your message.\n"
            "**`&reply`** - Send a reply directly to a message link."
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.reply(embed=embed)


# --- UTILITY COMMANDS (Say & Reply) ---

@bot.command(name='say')
async def say(ctx, *, message: str):
    """Make the bot say something"""
    await ctx.message.delete()
    await ctx.send(message)

@bot.command(name='reply')
async def reply_msg(ctx, message_link: str, *, message: str):
    """Reply to a specific message link"""
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


# --- MODERATION COMMANDS (Kick, Ban, Unban, Clear) ---

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Kick a member from the server"""
    await member.kick(reason=reason)
    embed = discord.Embed(
        title="🛡️ Member Kicked",
        description=f"**{member.mention}** has been kicked from the server.",
        color=discord.Color.red()
    )
    await ctx.reply(embed=embed)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Ban a member from the server"""
    await member.ban(reason=reason)
    embed = discord.Embed(
        title="🔨 Member Banned",
        description=f"**{member.mention}** has been banned from the server.",
        color=discord.Color.dark_red()
    )
    await ctx.reply(embed=embed)

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    """Unban a member by name/ID"""
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member_name.split('#') if '#' in member_name else (member_name, None)

    for ban_entry in banned_users:
        user = ban_entry.user
        if user.name == member_name:
            await ctx.guild.unban(user)
            await ctx.reply(f"✅ Unbanned **{user.mention}** from the server.")
            return
    await ctx.reply(f"⚠️ Could not find user {member_name} in ban list.")

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    """Delete messages"""
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Successfully deleted {amount} messages.", delete_after=5)


# 4. Run the Keep-Alive server and Bot
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("TOKEN"))

