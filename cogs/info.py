import discord
from discord.ext import commands
import datetime
import platform
import time

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name="botinfo", aliases=["about", "stats"])
    async def botinfo(self, ctx):
        uptime_seconds = int(time.time() - self.start_time)
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
        
        total_members = sum(g.member_count for g in self.bot.guilds)
        total_channels = sum(len(g.channels) for g in self.bot.guilds)

        embed = create_embed(
            ctx.guild,
            title="🌙 Moonlight Heaven • Bot Information",
            description=(
                f"Hello {ctx.author.mention}! I am **Moonlight Heaven**, your advanced celestial companion.\n"
                f"Crafted with absolute dedication and precision by **Zeus**.\n\n"
                f"📊 **System & Performance Metrics:**\n"
                f"• **Developer:** Zeus\n"
                f"• **Python Version:** `{platform.python_version()}`\n"
                f"• **Discord.py Version:** `{discord.__version__}`\n"
                f"• **Uptime:** `{uptime_str}`\n"
                f"• **Latency / Ping:** `{round(self.bot.latency * 1000)}ms`\n\n"
                f"🌐 **Global Reach:**\n"
                f"• **Servers Connected:** `{len(self.bot.guilds)}`\n"
                f"• **Total Users Tracked:** `{total_members}`\n"
                f"• **Total Channels:** `{total_channels}`"
            ),
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", aliases=["si"])
    async def serverinfo(self, ctx):
        guild = ctx.guild
        owner = guild.owner
        
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        total_channels = text_channels + voice_channels + categories
        
        total_members = guild.member_count
        bots = sum(1 for m in guild.members if m.bot)
        humans = total_members - bots
        
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        roles_count = len(guild.roles)
        emojis_count = len(guild.emojis)
        
        created_at = guild.created_at.strftime("%B %d, %Y (%H:%M UTC)")

        embed = create_embed(
            guild,
            title=f"🏰 Server Information • {guild.name}",
            description=(
                f"Here are the complete details and background stats for **{guild.name}**:\n\n"
                f"👑 **Ownership & Identity:**\n"
                f"• **Server Owner:** {owner.mention if owner else 'Unknown'} (`{owner.id if owner else 'N/A'}`)\n"
                f"• **Server ID:** `{guild.id}`\n"
                f"• **Created On:** `{created_at}`\n"
                f"• **Verification Level:** `{str(guild.verification_level).capitalize()}`\n\n"
                f"👥 **Member Statistics:**\n"
                f"• **Total Members:** `{total_members}`\n"
                f"• **Humans:** `{humans}` | **Bots:** `{bots}`\n\n"
                f"📂 **Channel Breakdown (`{total_channels}` Total):**\n"
                f"• **Categories:** `{categories}`\n"
                f"• **Text Channels:** `{text_channels}`\n"
                f"• **Voice Channels:** `{voice_channels}`\n\n"
                f"🚀 **Boost & Perks Status:**\n"
                f"• **Boost Level:** `Level {boost_level}`\n"
                f"• **Total Boosts:** `{boost_count} Boosts`\n\n"
                f"⚙️ **Extras:**\n"
                f"• **Total Roles:** `{roles_count}`\n"
                f"• **Custom Emojis:** `{emojis_count}`"
            ),
            color=discord.Color.blue()
        )
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        await ctx.send(embed=embed)

    @commands.command(name="userinfo", aliases=["ui", "whois"])
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
        roles_str = ", ".join(roles) if roles else "None"
        if len(roles_str) > 1024:
            roles_str = f"{len(roles)} roles assigned."

        created_at = member.created_at.strftime("%B %d, %Y")
        joined_at = member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown"
        
        status = str(member.status).upper() if member.status else "OFFLINE"

        embed = create_embed(
            ctx.guild,
            title=f"👤 User Information • {member.name}",
            description=(
                f"Detailed breakdown profile for {member.mention}:\n\n"
                f"🆔 **General Details:**\n"
                f"• **Username:** `{member}`\n"
                f"• **User ID:** `{member.id}`\n"
                f"• **Current Status:** `{status}`\n"
                f"• **Top Role:** {member.top_role.mention}\n\n"
                f"📅 **Timestamps:**\n"
                f"• **Account Created:** `{created_at}`\n"
                f"• **Server Joined:** `{joined_at}`\n\n"
                f"🛡️ **Assigned Roles ({len(member.roles) - 1}):**\n"
                f"{roles_str}"
            ),
            color=member.color if member.color.value != 0 else discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="roleinfo", aliases=["ri"])
    async def roleinfo(self, ctx, *, role: discord.Role):
        created_at = role.created_at.strftime("%B %d, %Y")
        permissions = [p[0].replace('_', ' ').title() for p in role.permissions if p[1]]
        perms_str = ", ".join(permissions) if permissions else "None"
        if len(perms_str) > 1024:
            perms_str = "Multiple permissions enabled."

        embed = create_embed(
            ctx.guild,
            title=f"🏷️ Role Information • {role.name}",
            description=(
                f"Here are all the details for the role {role.mention}:\n\n"
                f"• **Role ID:** `{role.id}`\n"
                f"• **Color Hex:** `{str(role.color)}`\n"
                f"• **Position:** `{role.position}`\n"
                f"• **Mentionable:** `{'Yes' if role.mentionable else 'No'}`\n"
                f"• **Hoisted (Separated):** `{'Yes' if role.hoist else 'No'}`\n"
                f"• **Members with Role:** `{len(role.members)}`\n"
                f"• **Created On:** `{created_at}`\n\n"
                f"🔑 **Key Permissions:**\n"
                f"`{perms_str}`"
            ),
            color=role.color if role.color.value != 0 else discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command(name="channelinfo", aliases=["ci"])
    async def channelinfo(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        created_at = channel.created_at.strftime("%B %d, %Y")

        embed = create_embed(
            ctx.guild,
            title=f"📺 Channel Information • #{channel.name}",
            description=(
                f"Complete specifications for channel {channel.mention}:\n\n"
                f"• **Channel ID:** `{channel.id}`\n"
                f"• **Topic:** `{channel.topic or 'No topic set.'}`\n"
                f"• **Position:** `{channel.position}`\n"
                f"• **Slowmode Delay:** `{channel.slowmode_delay} seconds`\n"
                f"• **NSFW Enabled:** `{'Yes' if channel.is_nsfw() else 'No'}`\n"
                f"• **Created On:** `{created_at}`"
            ),
            color=discord.Color.teal()
        )
        await ctx.send(embed=embed)

    @commands.command(name="boosters", aliases=["serverboosters"])
    async def boosters(self, ctx):
        boosters_list = ctx.guild.premium_subscribers
        if not boosters_list:
            embed = create_embed(ctx.guild, title="🚀 Server Boosters", description="There are currently no active boosters in this server.", color=discord.Color.orange())
            return await ctx.send(embed=embed)

        booster_names = "\n".join([f"• {b.mention} (`{b}`)" for b in boosters_list])
        embed = create_embed(
            ctx.guild,
            title=f"🚀 Server Boosters ({len(boosters_list)})",
            description=f"A massive thank you to our amazing members boosting **{ctx.guild.name}**:\n\n{booster_names}",
            color=discord.Color.magenta()
        )
        await ctx.send(embed=embed)

    @commands.command(name="emojilist", aliases.append("emojis") if hasattr(aliases := ["emojis"], '__setitem__') else ["emojis"])
    async def emojilist(self, ctx):
        emojis = ctx.guild.emojis
        if not emojis:
            embed = create_embed(ctx.guild, title="😀 Custom Emojis", description="There are no custom emojis in this server.", color=discord.Color.orange())
            return await ctx.send(embed=embed)

        emoji_str = " ".join([str(e) for e in emojis[:50]]) # Displaying up to 50 emojis to prevent text limit overflow
        embed = create_embed(
            ctx.guild,
            title=f"😀 Custom Emojis ({len(emojis)} Total)",
            description=f"Here is a preview of the server's custom emojis:\n\n{emoji_str}",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command(name="ping")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = create_embed(
            ctx.guild,
            title="🏓 Pong!",
            description=f"Current gateway latency response time is **{latency}ms**. All systems are operating smoothly!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Information(bot))
