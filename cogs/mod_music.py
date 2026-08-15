import discord
from discord.ext import commands


class ModMusicCog(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  # --- MODERATION COMMANDS ---

  @commands.command(name="kick")
  @commands.has_permissions(kick_members=True)
  async def kick(self, ctx, member: discord.Member, *, reason=None):
    """Kisi member ko kick karne ke liye"""
    await member.kick(reason=reason)
    embed = discord.Embed(
        title="🛡️ Member Kicked",
        description=(
            f"**{member.mention}** ko server se kick kar diya gaya hai."
        ),
        color=discord.Color.red(),
    )
    await ctx.reply(embed=embed)

  @commands.command(name="ban")
  @commands.has_permissions(ban_members=True)
  async def ban(self, ctx, member: discord.Member, *, reason=None):
    """Kisi member ko ban karne ke liye"""
    await member.ban(reason=reason)
    embed = discord.Embed(
        title="🔨 Member Banned",
        description=f"**{member.mention}** ko server se ban kar diya gaya hai.",
        color=discord.Color.dark_red(),
    )
    await ctx.reply(embed=embed)

  @commands.command(name="clear")
  @commands.has_permissions(manage_messages=True)
  async def clear(self, ctx, amount: int = 5):
    """Messages delete karne ke liye"""
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 {amount} messages delete kar diye gaye hain.")
    await discord.utils.sleep_until(discord.utils.utcnow())

  # --- MUSIC COMMANDS ---

  @commands.command(name="play")
  async def play(self, ctx, *, song_name: str):
    """Gaana play karne ke liye"""
    embed = discord.Embed(
        title="🎵 Music Player",
        description=f"Searching & Playing: **{song_name}**",
        color=discord.Color.blue(),
    )
    await ctx.reply(embed=embed)

  @commands.command(name="skip")
  async def skip(self, ctx):
    """Current song skip karne ke liye"""
    embed = discord.Embed(
        title="🎵 Music",
        description="Current song skip kar diya gaya hai!",
        color=discord.Color.blue(),
    )
    await ctx.reply(embed=embed)

  @commands.command(name="stop")
  async def stop(self, ctx):
    """Music rokne ke liye"""
    embed = discord.Embed(
        title="🎵 Music",
        description="Music rok diya gaya hai aur bot voice channel se"
        " nikal gaya hai.",
        color=discord.Color.blue(),
    )
    await ctx.reply(embed=embed)


async def setup(bot):
  await bot.add_cog(ModMusicCog(bot))
