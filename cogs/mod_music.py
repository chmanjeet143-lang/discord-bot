import asyncio
import discord
from discord.ext import commands
import yt_dlp

# YT-DLP configurations
yt_dlp.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):

  def __init__(self, source, *, data, volume=0.5):
    super().__init__(source, volume)
    self.data = data
    self.title = data.get('title')
    self.url = data.get('url')

  @classmethod
  async def from_url(cls, url, *, loop=None, stream=True):
    loop = loop or asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None, lambda: ytdl.extract_info(url, download=not stream)
    )

    if 'entries' in data:
      data = data['entries'][0]

    filename = data['url'] if stream else ytdl.prepare_filename(data)
    return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class ModMusicCog(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  # --- MODERATION COMMANDS ---

  @commands.command(name='kick')
  @commands.has_permissions(kick_members=True)
  async def kick(self, ctx, member: discord.Member, *, reason=None):
    """Kisi member ko kick karne ke liye"""
    await member.kick(reason=reason)
    embed = discord.Embed(
        title='🛡️ Member Kicked',
        description=f'**{member.mention}** ko server se kick kar diya gaya hai.',
        color=discord.Color.red(),
    )
    await ctx.reply(embed=embed)

  @commands.command(name='ban')
  @commands.has_permissions(ban_members=True)
  async def ban(self, ctx, member: discord.Member, *, reason=None):
    """Kisi member ko ban karne ke liye"""
    await member.ban(reason=reason)
    embed = discord.Embed(
        title='🔨 Member Banned',
        description=f'**{member.mention}** ko server se ban kar diya gaya hai.',
        color=discord.Color.dark_red(),
    )
    await ctx.reply(embed=embed)

  @commands.command(name='clear')
  @commands.has_permissions(manage_messages=True)
  async def clear(self, ctx, amount: int = 5):
    """Messages delete karne ke liye"""
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(
        f'🧹 {amount} messages delete kar diye gaye hain.', delete_after=5
    )

  # --- MUSIC COMMANDS ---

  @commands.command(name='play')
  async def play(self, ctx, *, query: str):
    """Gaana play karne ke liye"""
    if not ctx.author.voice:
      return await ctx.reply(
          '⚠️ Pehle aapko kisi Voice Channel se connect hona padega!'
      )

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
      await channel.connect()
    else:
      await ctx.voice_client.move_to(channel)

    async with ctx.typing():
      try:
        player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
        ctx.voice_client.play(
            player,
            after=lambda e: print(f'Player error: {e}') if e else None,
        )
      except Exception as e:
        return await ctx.reply(f'❌ Gaana play karne mein error aaya: {e}')

    embed = discord.Embed(
        title='🎵 Now Playing',
        description=f'**{player.title}**',
        color=discord.Color.blue(),
    )
    await ctx.reply(embed=embed)

  @commands.command(name='skip')
  async def skip(self, ctx):
    """Current song skip karne ke liye"""
    if ctx.voice_client and ctx.voice_client.is_playing():
      ctx.voice_client.stop()
      await ctx.reply('🎵 Current song skip kar diya gaya hai!')
    else:
      await ctx.reply('⚠️ Abhi koi gaana play nahi ho raha hai.')

  @commands.command(name='stop')
  async def stop(self, ctx):
    """Music rokne aur bot ko disconnect karne ke liye"""
    if ctx.voice_client:
      await ctx.voice_client.disconnect()
      await ctx.reply(
          '🎵 Music rok diya gaya hai aur bot voice channel se nikal gaya hai.'
      )
    else:
      await ctx.reply('⚠️ Bot kisi voice channel mein nahi hai.')


async def setup(bot):
  await bot.add_cog(ModMusicCog(bot))
