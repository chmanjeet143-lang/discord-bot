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
    """Tracks both Native Clan Tags and Custom Display Name Tags seamlessly."""
    def __init__(self, bot):
        self.bot = bot

    def get_guild_config(self, guild_id):
        config = load_config()
        return config.get(str(guild_id), {
            "channel_id": None,
            "custom_tag": "Moon",  # Text tag fallback for existing members
            "msg_use": "{user} ne clan tag add kar liya hai! Family me swagat hai ✨",
            "msg_unuse": "{user} ne clan tag hata diya hai. 🌑"
        })

    def update_guild_config(self, guild_id, key, value):
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

    def check_user_tag(self, member, guild_id):
        # 1. Check official native clan feature
        if hasattr(member, 'clan') and member.clan:
            return True

        # 2. Fallback check for display name / nickname text tag
        config = self.get_guild_config(guild_id)
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

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.bot:
            return

        guild_id = after.guild.id
        has_tag_before = self.check_user_tag(before, guild_id)
        has_tag_after = self.check_user_tag(after, guild_id)

        if has_tag_before == has_tag_after:
            return

        config = self.get_guild_config(guild_id)
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

    @commands.command(name="tagchannel")
    @commands.has_permissions(administrator=True)
    async def tag_channel(self, ctx, channel: discord.TextChannel):
        """Log channel set karne ke liye."""
        self.update_guild_config(ctx.guild.id, "channel_id", channel.id)
        await ctx.send(f"✅ Log channel set ho gaya hai {channel.mention} par!")

    @commands.command(name="settag")
    @commands.has_permissions(administrator=True)
    async def set_tag(self, ctx, *, tag: str):
        """Text tag set karne ke liye agar koi nickname me use kar raha ho. Example: &settag Moon"""
        self.update_guild_config(ctx.guild.id, "custom_tag", tag.strip())
        await ctx.send(f"✅ Fallback text tag set ho gaya hai: **{tag.strip()}**")

    @commands.command(name="tagcount")
    async def tag_count(self, ctx):
        """Native ya text tag wale total members check karne ke liye."""
        guild_id = ctx.guild.id
        count = sum(1 for m in ctx.guild.members if self.check_user_tag(m, guild_id) and not m.bot)
        await ctx.send(f"📊 Total members wearing the tag (Native + Nickname): **{count}**")

    @commands.command(name="taglist")
    async def tag_list(self, ctx):
        """Sabhi tagged members ki list dekhne ke liye."""
        guild_id = ctx.guild.id
        members = [m.mention for m in ctx.guild.members if self.check_user_tag(m, guild_id) and not m.bot]
        if not members:
            await ctx.send("❌ Koi bhi member tagged nahi mila.")
            return
        members_str = ", ".join(members)
        if len(members_str) > 2000:
            members_str = members_str[:1950] + "..."
        await ctx.send(f"📜 **Tagged Members ({len(members)}):**\n{members_str}")

async def setup(bot):
    await bot.add_cog(TagTracker(bot))
