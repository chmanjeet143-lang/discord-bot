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
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class TagTracker(commands.Cog, name="TagTracker"):
    """Tracks native Discord clan tags purely like Sapphire bot."""
    def __init__(self, bot):
        self.bot = bot

    def get_guild_config(self, guild_id):
        config = load_config()
        return config.get(str(guild_id), {
            "channel_id": None,
            "msg_use": "{user} Thanks for wearing our server tag!",
            "msg_unuse": "{user} removed the server tag."
        })

    def update_guild_config(self, guild_id, key, value):
        config = load_config()
        guild_str = str(guild_id)
        if guild_str not in config:
            config[guild_str] = {
                "channel_id": None,
                "msg_use": "{user} Thanks for wearing our server tag!",
                "msg_unuse": "{user} removed the server tag."
            }
        config[guild_str][key] = value
        save_config(config)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.bot:
            return

        # Check if native clan tag status changed
        has_clan_before = bool(hasattr(before, 'clan') and before.clan)
        has_clan_after = bool(hasattr(after, 'clan') and after.clan)

        if has_clan_before == has_clan_after:
            return

        config = self.get_guild_config(after.guild.id)
        channel_id = config.get("channel_id")
        if not channel_id:
            return

        channel = after.guild.get_channel(channel_id)
        if not channel:
            return

        if not has_clan_before and has_clan_after:
            text = config["msg_use"].replace("{user}", after.mention).replace("{username}", after.name)
            embed = discord.Embed(title="Guild Tag Added", description=text, color=0x57F287)
            await channel.send(embed=embed)

        elif has_clan_before and not has_clan_after:
            text = config["msg_unuse"].replace("{user}", after.mention).replace("{username}", after.name)
            embed = discord.Embed(title="Guild Tag Removed", description=text, color=0xED4245)
            await channel.send(embed=embed)

    @commands.command(name="tagchannel")
    @commands.has_permissions(administrator=True)
    async def tag_channel(self, ctx, channel: discord.TextChannel):
        """Log channel set karne ke liye."""
        self.update_guild_config(ctx.guild.id, "channel_id", channel.id)
        await ctx.send(f"✅ Log channel set ho gaya hai {channel.mention} par!")

    @commands.command(name="tagcount")
    async def tag_count(self, ctx):
        """Native clan tag wale total members check karne ke liye."""
        count = sum(1 for m in ctx.guild.members if hasattr(m, 'clan') and m.clan and not m.bot)
        await ctx.send(f"📊 Total members wearing native guild tag: **{count}**")

    @commands.command(name="taglist")
    async def tag_list(self, ctx):
        """Native clan tag wale members ki list dekhne ke liye."""
        members = [m.mention for m in ctx.guild.members if hasattr(m, 'clan') and m.clan and not m.bot]
        if not members:
            await ctx.send("❌ Koi bhi member native guild tag ke sath nahi mila.")
            return
        members_str = ", ".join(members)
        if len(members_str) > 2000:
            members_str = members_str[:1950] + "..."
        await ctx.send(f"📜 **Native Tag Members ({len(members)}):**\n{members_str}")

async def setup(bot):
    await bot.add_cog(TagTracker(bot))
