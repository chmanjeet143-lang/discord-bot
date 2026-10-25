import os
import time
import json
import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread

# 1. Flask server to keep bot alive on hosting (Replit etc.)
app = Flask('')

@app.route('/')
def home():
    return "🤖 Moonlight Heaven is Alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()

# 2. Bot Intents & Configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # Zaroori hai member/nickname update events ke liye!

bot = commands.Bot(command_prefix="&", intents=intents)

CONFIG_FILE = "tag_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_guild_config(guild_id):
    config = load_config()
    return config.get(str(guild_id), {
        "channel_id": None,
        "custom_tag": "Moon",  # Default fallback text tag
        "msg_use": "{user} ne clan tag add kar liya hai! Family me swagat hai ✨",
        "msg_unuse": "{user} ne clan tag hata diya hai. 🌑"
    })

def update_guild_config(guild_id, key, value):
    config = load_config()
    guild_str = str(guild_id)
    if guild_str not in config:
        config[guild_str] = {
            "channel_id": None,
            "custom_tag": "Moon",
            "msg_use": "{user} ne clan tag add kar liya hai! Family me swagat hai ✨",
            "msg_unuse": "{user} ne clan tag hata diya hai. 🌑"
        }
    config[guild_str][key] = value
    save_config(config)

def check_user_tag(member, guild_id):
    # 1. Check official native clan feature
    if hasattr(member, 'clan') and member.clan:
        return True

    # 2. Fallback check for display name / nickname text tag
    config = get_guild_config(guild_id)
    target_tag = config.get("custom_tag", "Moon").lower()
    
    names_to_check = [
        getattr(member, 'display_name', ''),
        getattr(member, 'nick', ''),
        getattr(member, 'name', '')
    ]
    
    for name in names_to_check:
        if name and target_tag in name.lower():
            return True
            
        return False

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready and online!")

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.bot:
        return

    guild_id = after.guild.id
    has_tag_before = check_user_tag(before, guild_id)
    has_tag_after = check_user_tag(after, guild_id)

    print(f"[DEBUG] Update: {after.name} | Before: {has_tag_before} | After: {has_tag_after}")

    if has_tag_before == has_tag_after:
        return

    config = get_guild_config(guild_id)
    channel_id = config.get("channel_id")
    if not channel_id:
        return

    channel = after.guild.get_channel(channel_id)
    if not channel:
        return

    if not has_tag_before and has_tag_after:
        text = config["msg_use"].replace("{user}", after.mention).replace("{username}", after.name)
        embed = discord.Embed(title="✨ Clan Tag Added", description=text, color=0x57F287)
        await channel.send(embed=embed)

    elif has_tag_before and not has_tag_after:
        text = config["msg_unuse"].replace("{user}", after.mention).replace("{username}", after.name)
        embed = discord.Embed(title="🌑 Clan Tag Removed", description=text, color=0xED4245)
        await channel.send(embed=embed)

@bot.command(name="tagchannel")
@commands.has_permissions(administrator=True)
async def tag_channel(ctx, channel: discord.TextChannel):
    """Log channel set karne ke liye."""
    update_guild_config(ctx.guild.id, "channel_id", channel.id)
    await ctx.send(f"✅ Log channel set ho gaya hai {channel.mention} par!")

@bot.command(name="settag")
@commands.has_permissions(administrator=True)
async def set_tag(ctx, *, tag: str):
    """Text tag set karne ke liye. Example: &settag Moon"""
    update_guild_config(ctx.guild.id, "custom_tag", tag.strip())
    await ctx.send(f"✅ Clan tag successfully set ho gaya hai: **{tag.strip()}**")

@bot.command(name="tagcount")
async def tag_count(ctx):
    """Total tagged members check karne ke liye."""
    guild_id = ctx.guild.id
    count = sum(1 for m in ctx.guild.members if check_user_tag(m, guild_id) and not m.bot)
    await ctx.send(f"📊 Total members wearing the tag: **{count}**")

@bot.command(name="taglist")
async def tag_list(ctx):
    """Tagged members ki list dekhne ke liye."""
    guild_id = ctx.guild.id
    members = [m.mention for m in ctx.guild.members if check_user_tag(m, guild_id) and not m.bot]
    if not members:
        await ctx.send("❌ Koi bhi member tagged nahi mila.")
        return
    members_str = ", ".join(members)
    if len(members_str) > 2000:
        members_str = members_str[:1950] + "..."
    await ctx.send(f"📜 **Tagged Members ({len(members)}):**\n{members_str}")

if __name__ == "__main__":
    keep_alive()
    # Apna bot token yahan daalein ya environment variable use karein
    bot.run(os.environ.get("DISCORD_TOKEN"))
