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
    """Track clan tags automatically based on douknowluci's profile and notify members."""
    def __init__(self, bot):
        self.bot = bot

    def get_guild_config(self, guild_id):
        config = load_config()
        return config.get(str(guild_id), {
            "channel_id": None,
            "msg_use": "{user} added the clan tag! Welcome to the family 🌙",
            "msg_unuse": "{user} removed the clan tag. 🌑"
        })

    def update_guild_config(self, guild_id, key, value):
        config = load_config()
        guild_str = str(guild_id)
        if guild_str not in config:
            config[guild_str] = {
                "channel_id": None,
                "msg_use": "{user} added the clan tag! Welcome to the family 🌙",
                "msg_unuse": "{user} removed the clan tag. 🌑"
            }
        config[guild_str][key] = value
        save_config(config)

    def get_owner_tag(self, guild):
        """Internal method to fetch the clan tag dynamically from douknowluci's profile"""
        owner_member = discord.utils.find(
            lambda m: m.name.lower() == "douknowluci" or (m.global_name and m.global_name.lower() == "douknowluci"), 
            guild.members
        )
        
        if not owner_member:
            return "Moon"  # Default fallback if douknowluci is not found in cache

        # 1. Check native Discord clan tag
        if hasattr(owner_member, 'clan') and owner_member.clan:
            clan_tag = getattr(owner_member.clan, 'tag', str(owner_member.clan))
            if clan_tag:
                return clan_tag.strip()

        # 2. Check bracket format in display name or nickname (e.g., [Moon])
        name = owner_member.display_name or owner_member.name
        if "[" in name and "]" in name:
            start = name.find("[") + 1
            end = name.find("]")
            if end > start:
                return name[start:end].strip()

        # 3. Fallback to display name text or default
        return name

    def check_user_tag(self, member, target_tag):
        target_tag_lower = target_tag.lower()
        
        # Check all possible name fields and native clan attribute
        names_to_check = [
            getattr(member, 'display_name', ''),
            getattr(member, 'name', ''),
            getattr(member, 'global_name', ''),
            getattr(member, 'nick', '')
        ]
        
        for name in names_to_check:
            if name and target_tag_lower in name.lower():
                return True

        if hasattr(member, 'clan') and member.clan:
            clan_tag = getattr(member.clan, 'tag', str(member.clan))
            if clan_tag and target_tag_lower in clan_tag.lower():
                return True
                
        return False

    # Real-time Clan Tag tracking event
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.bot:
            return

        config = self.get_guild_config(after.guild.id)
        target_tag = self.get_owner_tag(after.guild)

        has_tag_before = self.check_user_tag(before, target_tag)
        has_tag_after = self.check_user_tag(after, target_tag)

        if has_tag_before == has_tag_after:
            return  # No change in tag status

        channel_id = config.get("channel_id")
        if not channel_id:
            return

        channel = after.guild.get_channel(channel_id)
        if not channel:
            return

        # When user adds the clan tag
        if not has_tag_before and has_tag_after:
            text = config["msg_use"].replace("{user}", after.mention).replace("{username}", after.name)
            embed = discord.Embed(title="🌙 Clan Tag Added", description=text, color=0x57F287)
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text="Moonlight Heaven • Tag Tracker")
            await channel.send(embed=embed)

        # When user removes the clan tag
        elif has_tag_before and not has_tag_after:
            text = config["msg_unuse"].replace("{user}", after.mention).replace("{username}", after.name)
            embed = discord.Embed(title="🌑 Clan Tag Removed", description=text, color=0xED4245)
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text="Moonlight Heaven • Tag Tracker")
            await channel.send(embed=embed)

    # Individual Commands with Descriptions & Examples (Directly visible in help menu)

    @commands.command(name="tagchannel")
    @commands.has_permissions(administrator=True)
    async def tag_channel(self, ctx, channel: discord.TextChannel):
        """
        Set the specific log channel where clan tag notifications will be sent.
        
        **Example:**
        `&tagchannel #tag-logs`
        """
        self.update_guild_config(ctx.guild.id, "channel_id", channel.id)
        await ctx.send(f"✅ Tag tracker log channel successfully set to {channel.mention}!")

    @commands.command(name="tagcount")
    async def tag_count(self, ctx):
        """
        Check the total number of members wearing douknowluci's clan tag.
        
        **Example:**
        `&tagcount`
        """
        target_tag = self.get_owner_tag(ctx.guild)
        count = sum(1 for m in ctx.guild.members if self.check_user_tag(m, target_tag) and not m.bot)
        
        embed = discord.Embed(title="📊 Clan Tag Count", description=f"Total members currently wearing **{target_tag}** (detected from `douknowluci`): **{count}**", color=0x5865F2)
        embed.set_footer(text="Moonlight Heaven • Tag Tracker")
        await ctx.send(embed=embed)

    @commands.command(name="taglist")
    async def tag_list(self, ctx):
        """
        View the complete list of members wearing douknowluci's clan tag.
        
        **Example:**
        `&taglist`
        """
        target_tag = self.get_owner_tag(ctx.guild)
        members = [m.mention for m in ctx.guild.members if self.check_user_tag(m, target_tag) and not m.bot]
        
        if not members:
            await ctx.send(f"❌ No members found wearing the clan tag detected from `douknowluci` (`{target_tag}`) currently.")
            return
        
        members_str = ", ".join(members)
        if len(members_str) > 2000:
            members_str = members_str[:1950] + "... (and more)"

        embed = discord.Embed(title="📜 Clan Tag Members List", description=members_str, color=0x5865F2)
        embed.set_footer(text=f"Tag: {target_tag} | Total: {len(members)} members | Moonlight Heaven")
        await ctx.send(embed=embed)

    @commands.command(name="tagmsguse")
    @commands.has_permissions(administrator=True)
    async def tag_msg_use(self, ctx, *, message: str):
        """
        Customize the notification message when a user adds the clan tag.
        
        **Example:**
        `&tagmsguse {user} added the clan tag! Welcome!`
        """
        self.update_guild_config(ctx.guild.id, "msg_use", message)
        await ctx.send(f"✅ Tag use message updated successfully!\n\n**Preview:** {message.replace('{user}', ctx.author.mention)}")

    @commands.command(name="tagmsgunuse")
    @commands.has_permissions(administrator=True)
    async def tag_msg_unuse(self, ctx, *, message: str):
        """
        Customize the notification message when a user removes the clan tag.
        
        **Example:**
        `&tagmsgunuse {user} removed the clan tag.`
        """
        self.update_guild_config(ctx.guild.id, "msg_unuse", message)
        await ctx.send(f"✅ Tag unuse message updated successfully!\n\n**Preview:** {message.replace('{user}', ctx.author.mention)}")

async def setup(bot):
    await bot.add_cog(TagTracker(bot))
