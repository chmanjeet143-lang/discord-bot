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
    """Track clan tags automatically based on douknowluci's exact tag and notify members."""
    def __init__(self, bot):
        self.bot = bot

    def get_guild_config(self, guild_id):
        config = load_config()
        return config.get(str(guild_id), {
            "channel_id": None,
            "msg_use": "{user} ne clan tag add kar liya hai! Family me swagat hai ✨",
            "msg_unuse": "{user} ne clan tag hata diya hai. 🌑"
        })

    def update_guild_config(self, guild_id, key, value):
        config = load_config()
        guild_str = str(guild_id)
        if guild_str not in config:
            config[guild_str] = {
                "channel_id": None,
                "msg_use": "{user} ne clan tag add kar liya hai! Family me swagat hai ✨",
                "msg_unuse": "{user} ne clan tag hata diya hai. 🌑"
            }
        config[guild_str][key] = value
        save_config(config)

    def get_owner_tag(self, guild):
        """douknowluci ki profile se emoji ke baad wala exact clan tag nikalne ka sahi logic"""
        owner_member = discord.utils.find(
            lambda m: m.name.lower() == "douknowluci" or (m.global_name and m.global_name.lower() == "douknowluci"), 
            guild.members
        )
        
        if not owner_member:
            return None

        # 1. Native Discord clan tag check
        if hasattr(owner_member, 'clan') and owner_member.clan:
            clan_tag = getattr(owner_member.clan, 'tag', str(owner_member.clan))
            if clan_tag:
                return clan_tag.strip()

        # 2. Display name se emoji ke baad ka exact tag uthana (jaise 🌸 Moon)
        name = owner_member.display_name or owner_member.name
        
        for emoji in ["🌸", "🌙", "✨", "⭐", "💫", "💎", "🌿"]:
            if emoji in name:
                parts = name.split(emoji)
                if len(parts) > 1:
                    tag_text = parts[-1].strip()
                    if tag_text:
                        return f"{emoji} {tag_text}"

        return None

    def check_user_tag(self, member, target_tag):
        if not target_tag:
            return False
            
        target_tag_lower = target_tag.lower()
        
        # Native clan tag check
        if hasattr(member, 'clan') and member.clan:
            clan_tag = getattr(member.clan, 'tag', str(member.clan))
            if clan_tag and target_tag_lower in clan_tag.lower():
                return True

        # Display name, username, global name, nick check
        names_to_check = [
            getattr(member, 'display_name', ''),
            getattr(member, 'name', ''),
            getattr(member, 'global_name', ''),
            getattr(member, 'nick', '')
        ]
        
        for name in names_to_check:
            if name and target_tag_lower in name.lower():
                return True
                
        return False

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.bot:
            return

        config = self.get_guild_config(after.guild.id)
        target_tag = self.get_owner_tag(after.guild)
        if not target_tag:
            return

        has_tag_before = self.check_user_tag(before, target_tag)
        has_tag_after = self.check_user_tag(after, target_tag)

        if has_tag_before == has_tag_after:
            return

        channel_id = config.get("channel_id")
        if not channel_id:
            return

        channel = after.guild.get_channel(channel_id)
        if not channel:
            return

        if not has_tag_before and has_tag_after:
            text = config["msg_use"].replace("{user}", after.mention).replace("{username}", after.name)
            embed = discord.Embed(title="✨ Clan Tag Added", description=text, color=0x57F287)
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text="Tag Tracker System")
            await channel.send(embed=embed)

        elif has_tag_before and not has_tag_after:
            text = config["msg_unuse"].replace("{user}", after.mention).replace("{username}", after.name)
            embed = discord.Embed(title="🌑 Clan Tag Removed", description=text, color=0xED4245)
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text="Tag Tracker System")
            await channel.send(embed=embed)

    @commands.command(name="tagchannel")
    @commands.has_permissions(administrator=True)
    async def tag_channel(self, ctx, channel: discord.TextChannel):
        """
        Log channel set karne ke liye.
        
        **Example:**
        `&tagchannel #logs`
        """
        self.update_guild_config(ctx.guild.id, "channel_id", channel.id)
        await ctx.send(f"✅ Tag tracker log channel successfully set ho gaya hai {channel.mention} par!")

    @commands.command(name="tagcount")
    async def tag_count(self, ctx):
        """
        Total members check karne ke liye jinke paas tag laga hai.
        
        **Example:**
        `&tagcount`
        """
        target_tag = self.get_owner_tag(ctx.guild)
        if not target_tag:
            await ctx.send("❌ `douknowluci` ki profile se tag detect nahi ho paya!")
            return
            
        count = sum(1 for m in ctx.guild.members if self.check_user_tag(m, target_tag) and not m.bot)
        
        embed = discord.Embed(title="📊 Clan Tag Count", description=f"Total members jo **{target_tag}** tag use kar rahe hain: **{count}**", color=0x5865F2)
        embed.set_footer(text="Tag Tracker System")
        await ctx.send(embed=embed)

    @commands.command(name="taglist")
    async def tag_list(self, ctx):
        """
        List dekhne ke liye ki kis-kis ke paas tag hai.
        
        **Example:**
        `&taglist`
        """
        target_tag = self.get_owner_tag(ctx.guild)
        if not target_tag:
            await ctx.send("❌ `douknowluci` ki profile se tag detect nahi ho paya!")
            return
            
        members = [m.mention for m in ctx.guild.members if self.check_user_tag(m, target_tag) and not m.bot]
        
        if not members:
            await ctx.send(f"❌ Koi bhi member `{target_tag}` tag ke sath nahi mila.")
            return
        
        members_str = ", ".join(members)
        if len(members_str) > 2000:
            members_str = members_str[:1950] + "... (aur bhi hain)"

        embed = discord.Embed(title="📜 Clan Tag Members List", description=members_str, color=0x5865F2)
        embed.set_footer(text=f"Tag: {target_tag} | Total: {len(members)} members")
        await ctx.send(embed=embed)

    @commands.command(name="tagmsguse")
    @commands.has_permissions(administrator=True)
    async def tag_msg_use(self, ctx, *, message: str):
        """
        Tag add hone par notification message customize karne ke liye.
        
        **Example:**
        `&tagmsguse {user} ne tag add kar liya hai!`
        """
        self.update_guild_config(ctx.guild.id, "msg_use", message)
        await ctx.send(f"✅ Tag use message update ho gaya hai!\n\n**Preview:** {message.replace('{user}', ctx.author.mention)}")

    @commands.command(name="tagmsgunuse")
    @commands.has_permissions(administrator=True)
    async def tag_msg_unuse(self, ctx, *, message: str):
        """
        Tag remove hone par notification message customize karne ke liye.
        
        **Example:**
        `&tagmsgunuse {user} ne tag hata diya hai.`
        """
        self.update_guild_config(ctx.guild.id, "msg_unuse", message)
        await ctx.send(f"✅ Tag unuse message update ho gaya hai!\n\n**Preview:** {message.replace('{user}', ctx.author.mention)}")

async def setup(bot):
    await bot.add_cog(TagTracker(bot))
