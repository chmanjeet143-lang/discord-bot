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

class TagTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_guild_config(self, guild_id):
        config = load_config()
        return config.get(str(guild_id), {
            "channel_id": None,
            "tag": "🌸Moon",  # Default exact server tag
            "msg_use": "{user} added the tag to their name! Welcome to the family 🌙",
            "msg_unuse": "{user} removed the tag from their name. 🌑"
        })

    def update_guild_config(self, guild_id, key, value):
        config = load_config()
        guild_str = str(guild_id)
        if guild_str not in config:
            config[guild_str] = {
                "channel_id": None,
                "tag": "🌸Moon",
                "msg_use": "{user} added the tag to their name! Welcome to the family 🌙",
                "msg_unuse": "{user} removed the tag from their name. 🌑"
            }
        config[guild_str][key] = value
        save_config(config)

    # Real-time Tag tracking event
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.bot:
            return

        config = self.get_guild_config(after.guild.id)
        target_tag = config.get("tag", "🌸Moon").lower()

        before_name = before.display_name.lower()
        after_name = after.display_name.lower()

        has_tag_before = target_tag in before_name
        has_tag_after = target_tag in after_name

        if has_tag_before == has_tag_after:
            return  # No change in tag status

        channel_id = config.get("channel_id")
        if not channel_id:
            return

        channel = after.guild.get_channel(channel_id)
        if not channel:
            return

        # When user adds the tag
        if not has_tag_before and has_tag_after:
            text = config["msg_use"].replace("{user}", after.mention).replace("{username}", after.name)
            embed = discord.Embed(title="🌙 Tag Added", description=text, color=0x57F287)
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text="Moonlight Heaven • Tag Tracker")
            await channel.send(embed=embed)

        # When user removes the tag
        elif has_tag_before and not has_tag_after:
            text = config["msg_unuse"].replace("{user}", after.mention).replace("{username}", after.name)
            embed = discord.Embed(title="🌑 Tag Removed", description=text, color=0xED4245)
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text="Moonlight Heaven • Tag Tracker")
            await channel.send(embed=embed)

    # Main Command Group with Detailed Help Menu
    @commands.group(name="tag", invoke_without_command=True)
    async def tag(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        current_tag = config.get("tag", "🌸Moon")
        
        embed = discord.Embed(
            title="🏷️ Tag Tracker",
            description=(
                f"Here are all the available commands under **Tag Tracker**:\n"
                f"Current Server Tag: `{current_tag}`\n\n"
                "• `&tag settag <tag>` - Set your exact server tag (Admin Only).\n"
                "• `&tag channel #channel` - Set the specific log channel for notifications (Admin Only).\n"
                "• `&tag count` - Check the total number of members wearing the tag.\n"
                "• `&tag list` - View the complete list of members wearing the tag.\n"
                "• `&tag msguse <message>` - Customize message when a user adds the tag (Admin Only).\n"
                "• `&tag msgunuse <message>` - Customize message when a user removes the tag (Admin Only)."
            ),
            color=0x2B2D31
        )
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

    @tag.command(name="settag")
    @commands.has_permissions(administrator=True)
    async def tag_settag(self, ctx, *, new_tag: str):
        self.update_guild_config(ctx.guild.id, "tag", new_tag)
        await ctx.send(f"✅ Server tag successfully updated to: `{new_tag}`")

    @tag.command(name="channel")
    @commands.has_permissions(administrator=True)
    async def tag_channel(self, ctx, channel: discord.TextChannel):
        self.update_guild_config(ctx.guild.id, "channel_id", channel.id)
        await ctx.send(f"✅ Tag tracker log channel successfully set to {channel.mention}!")

    @tag.command(name="count")
    async def tag_count(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        target_tag = config.get("tag", "🌸Moon").lower()
        
        count = sum(1 for m in ctx.guild.members if target_tag in m.display_name.lower() and not m.bot)
        embed = discord.Embed(
            title="📊 Tag Count",
            description=f"Total members currently wearing the **{config.get('tag')}** tag: **{count}**",
            color=0x5865F2
        )
        embed.set_footer(text="Moonlight Heaven • Tag Tracker")
        await ctx.send(embed=embed)

    @tag.command(name="list")
    async def tag_list(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        target_tag = config.get("tag", "🌸Moon").lower()

        members = [m.mention for m in ctx.guild.members if target_tag in m.display_name.lower() and not m.bot]
        if not members:
            await ctx.send(f"❌ No members found wearing the `{config.get('tag')}` tag currently.")
            return
        
        members_str = ", ".join(members)
        if len(members_str) > 2000:
            members_str = members_str[:1950] + "... (and more)"

        embed = discord.Embed(
            title="📜 Tag Members List",
            description=members_str,
            color=0x5865F2
        )
        embed.set_footer(text=f"Total: {len(members)} members | Moonlight Heaven")
        await ctx.send(embed=embed)

    @tag.command(name="msguse")
    @commands.has_permissions(administrator=True)
    async def tag_msg_use(self, ctx, *, message: str):
        self.update_guild_config(ctx.guild.id, "msg_use", message)
        await ctx.send(f"✅ Tag use message updated successfully!\n\n**Preview:** {message.replace('{user}', ctx.author.mention)}")

    @tag.command(name="msgunuse")
    @commands.has_permissions(administrator=True)
    async def tag_msg_unuse(self, ctx, *, message: str):
        self.update_guild_config(ctx.guild.id, "msg_unuse", message)
        await ctx.send(f"✅ Tag unuse message updated successfully!\n\n**Preview:** {message.replace('{user}', ctx.author.mention)}")

async def setup(bot):
    await bot.add_cog(TagTracker(bot))
