from datetime import datetime, timezone
import discord
from discord.ext import commands


class Utility(commands.Cog):
    """Server aur members ke liye helpful utility commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Bot ki latency check karta hai."""
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: **{latency_ms}ms**")

    @commands.command(name="serverinfo", aliases=["si"])
    async def serverinfo(self, ctx: commands.Context):
        """Server ki basic details dikhata hai."""
        guild = ctx.guild
        if not guild:
            return

        created_at = discord.utils.format_dt(guild.created_at, style="R")
        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Server ID", value=str(guild.id), inline=True)
        embed.add_field(
            name="Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=True,
        )
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Text Channels", value=str(len(guild.text_channels)), inline=True)
        embed.add_field(name="Voice Channels", value=str(len(guild.voice_channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Created", value=created_at, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="userinfo", aliases=["ui", "whois"])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """Kisi member ki profile aur join details dikhata hai."""
        target = member or ctx.author
        embed = discord.Embed(
            title=f"User Info — {target}",
            color=target.top_role.color if target.top_role.color.value else discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="ID", value=str(target.id), inline=True)
        embed.add_field(name="Bot?", value="Yes" if target.bot else "No", inline=True)
        embed.add_field(
            name="Top Role",
            value=target.top_role.mention if target.top_role else "None",
            inline=True,
        )
        embed.add_field(
            name="Account Created",
            value=discord.utils.format_dt(target.created_at, style="R"),
            inline=True,
        )
        if isinstance(target, discord.Member) and target.joined_at:
            embed.add_field(
                name="Joined Server",
                value=discord.utils.format_dt(target.joined_at, style="R"),
                inline=True,
            )

        await ctx.send(embed=embed)

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """User ka avatar bade size mein dikhata hai."""
        target = member or ctx.author
        embed = discord.Embed(
            title=f"{target.display_name}'s Avatar",
            color=discord.Color.blurple(),
        )
        embed.set_image(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="membercount", aliases=["mc"])
    async def membercount(self, ctx: commands.Context):
        """Total members aur bots ki ginti dikhata hai."""
        guild = ctx.guild
        if not guild:
            return

        total = guild.member_count or 0
        bots = sum(1 for m in guild.members if m.bot)
        humans = total - bots

        embed = discord.Embed(
            title=f"{guild.name} — Member Count",
            color=discord.Color.teal(),
        )
        embed.add_field(name="Total", value=str(total), inline=True)
        embed.add_field(name="Humans", value=str(humans), inline=True)
        embed.add_field(name="Bots", value=str(bots), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="say")
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx: commands.Context, *, message: str):
        """Bot ke zariye message bhejwata hai (Manage Messages permission ke saath)."""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await ctx.send(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
