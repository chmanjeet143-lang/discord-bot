import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "tag_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class TagTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_channel_id(self, guild_id):
        config = load_config()
        return config.get(str(guild_id), {}).get("channel_id", None)

    def set_channel_id(self, guild_id, channel_id):
        config = load_config()
        if str(guild_id) not in config:
            config[str(guild_id)] = {}
        config[str(guild_id)]["channel_id"] = channel_id
        save_config(config)

    def check_user_tag(self, member, guild):
        if hasattr(member, 'clan') and member.clan:
            # Check karo ki member ka clan is guild se match karta hai ya nahi
            if hasattr(guild, 'clan') and guild.clan:
                if member.clan == guild.clan:
                    return True
            if getattr(member.clan, 'id', None) == guild.id:
                return True
        return False

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.bot:
            return

        guild = after.guild
        guild_id = guild.id
        
        has_tag_before = self.check_user_tag(before, guild)
        has_tag_after = self.check_user_tag(after, guild)

        if has_tag_before == has_tag_after:
            return

        channel_id = self.get_channel_id(guild_id)
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        if not has_tag_before and has_tag_after:
            text = f"Thanks for using our server tag bsss! {after.mention} ✨"
            embed = discord.Embed(title="✨ Server Clan Tag Added", description=text, color=0x57F287)
            await channel.send(embed=embed)

        elif has_tag_before and not has_tag_after:
            text = f"{after.mention} ne hamara server clan tag hata diya. 🌑"
            embed = discord.Embed(title="🌑 Server Clan Tag Removed", description=text, color=0xED4245)
            await channel.send(embed=embed)

    @commands.command(name="tagchannel")
    @commands.has_permissions(administrator=True)
    async def tag_channel(self, ctx, channel: discord.TextChannel):
        """Log channel set karne ke liye."""
        self.set_channel_id(ctx.guild.id, channel.id)
        await ctx.send(f"✅ Log channel set ho gaya hai {channel.mention} par!")

    @commands.command(name="internalid")
    @commands.has_permissions(administrator=True)
    async def internal_id(self, ctx):
        """Server ke clan ki internal ID aur details check karne ke liye."""
        guild = ctx.guild
        msg = f"🔍 **Server Info:**\n- Guild Name: `{guild.name}`\n- Guild ID: `{guild.id}`\n"
        
        if hasattr(guild, 'clan') and guild.clan:
            msg += f"- Guild Clan Object: `{guild.clan}`\n"
        else:
            msg += f"- Guild Clan: `Direct attribute available nahi hai (Normal behavior)`\n"
            
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(TagTracker(bot))
