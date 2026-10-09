import discord
from discord.ext import commands
import platform
import time

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

# Professional Embed Builder (Zynrax / Moonlight Heaven Style)
def create_embed(title="", description="", color=0x2B2D31, thumbnail=None):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail or DEFAULT_AVATAR)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    # 1. Avatar Command (.avatar)
    @commands.command(name="avatar", aliases=["av"])
    async def avatar_cmd(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        embed = create_embed(
            title=f"Avatar for {target.name}",
            description=f"[PNG]({target.display_avatar.with_format('png').url}) | [JPG]({target.display_avatar.with_format('jpg').url}) | [WEBP]({target.display_avatar.with_format('webp').url})",
            thumbnail=target.display_avatar.url
        )
        embed.set_image(url=target.display_avatar.url)
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 2. User Info Command (.userinfo)
    @commands.command(name="userinfo", aliases=["ui"])
    async def userinfo_cmd(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        roles = [role.mention for role in target.roles if role != ctx.guild.default_role]
        roles_text = ", ".join(roles) if roles else "None"

        embed = create_embed(title=f"User Information: {target.name}", thumbnail=target.display_avatar.url)
        embed.add_field(name="General", value=f"**ID:** {target.id}\n**Display Name:** {target.display_name}\n**Bot:** {'Yes' if target.bot else 'No'}\n**Status:** {target.status}", inline=False)
        embed.add_field(name="Dates", value=f"**Account Created:** <t:{int(target.created_at.timestamp())}:R>\n**Joined Server:** <t:{int(target.joined_at.timestamp())}:R>" if target.joined_at else "", inline=False)
        embed.add_field(name="Roles", value=roles_text[:1024], inline=False)
        
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 3. Server Info Command (.serverinfo)
    @commands.command(name="serverinfo", aliases=["si"])
    async def serverinfo_cmd(self, ctx):
        guild = ctx.guild
        embed = create_embed(title=f"Server Information: {guild.name}", thumbnail=guild.icon.url if guild.icon else DEFAULT_AVATAR)
        embed.add_field(name="Overview", value=f"**ID:** {guild.id}\n**Owner:** {guild.owner}\n**Created On:** <t:{int(guild.created_at.timestamp())}:R>", inline=False)
        embed.add_field(name="Counts", value=f"**Members:** {guild.member_count}\n**Channels:** {len(guild.channels)}\n**Roles:** {len(guild.roles)}", inline=False)
        
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 4. Bot Info Command (.botinfo)
    @commands.command(name="botinfo", aliases=["bi"])
    async def botinfo_cmd(self, ctx):
        uptime_seconds = int(time.time() - self.start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        embed = create_embed(title="Hey, I'm Moonlight Heaven™", description="A powerful multipurpose bot developed by Zeus with advanced modules.", thumbnail=self.bot.user.display_avatar.url)
        embed.add_field(name="Platform", value=f"**OS:** {platform.system()}\n**Python:** {platform.python_version()}\n**Discord.py:** {discord.__version__}", inline=False)
        embed.add_field(name="Network & Uptime", value=f"**Ping:** {round(self.bot.latency * 1000)}ms\n**Uptime:** {hours}h {minutes}m\n**Guilds:** {len(self.bot.guilds)}", inline=False)
        embed.add_field(name="Developer", value="**Developed By:** Zeus", inline=False)
        
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

async def setup(bot):
    await bot.add_cog(Info(bot))
