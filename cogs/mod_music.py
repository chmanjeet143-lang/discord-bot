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

  # --- MODERATION COMMANDS (English Output) ---

  @commands.command(name='kick')
  @commands.has_permissions(kick_members=True)
  async def kick(self, ctx, member: discord.Member, *, reason=None):
    """Kick a member from the server"""
    await member.kick(reason=reason)
    embed = discord.Embed(
        title='🛡️ Member Kicked',
        description=f'**{member.mention}** has been kicked from the server.',
        color=discord.Color.red(),
    )
    await ctx.reply(embed=embed)

  @commands.command(name='ban')
  @commands.has_permissions(ban_members=True)
  async def ban(self, ctx, member: discord.Member, *, reason=None):
    """Ban a member from the server"""
    await member.ban(reason=reason)
    embed = discord.Embed(
        title='🔨 Member Banned',
        description=f'**{member.mention}** has been banned from the server.',
        color=discord.Color.dark_red(),
    )
    await ctx.reply(embed=embed)

  @commands.command(name='clear')
  @commands.has_permissions(manage_messages=True)
  async def clear(self, ctx, amount: int = 5):
    """Delete messages"""
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(
        f'🧹 Successfully deleted {amount} messages.', delete_after=5
    )

  # --- SAY & REPLY COMMANDS (English Output) ---

  @commands.command(name='say')
  async def say(self, ctx, *, message: str):
    """Make the bot say something"""
    await ctx.message.delete()
    await ctx.send(message)

  @commands.command(name='reply')
  async def reply_msg(self, ctx, message_link: str, *, message: str):
    """Reply to a specific message link"""
    try:
      parts = message_link.split('/')
      channel_id = int(parts[-2])
      message_id = int(parts[-1])

      channel = self.bot.get_channel(channel_id)
      if not channel:
        channel = await self.bot.fetch_channel(channel_id)

      target_message = await channel.fetch_message(message_id)
      await target_message.reply(message)
      await ctx.message.delete()
    except Exception as e:
      await ctx.reply(f'❌ Could not process link or error occurred: {e}')

  # --- MUSIC COMMANDS (English Output) ---

  @commands.command(name='play')
  async def play(self, ctx, *, query: str):
    """Play a song"""
    if not ctx.author.voice:
      return await ctx.reply(
          '⚠️ You need to connect to a Voice Channel first!'
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
        return await ctx.reply(f'❌ An error occurred: ```py\n{e}\n```')

    embed = discord.Embed(
        title='🎵 Now Playing',
        description=f'**{player.title}**',
        color=discord.Color.blue(),
    )
    await ctx.reply(embed=embed)

  @commands.command(name='skip')
  async def skip(self, ctx):
    """Skip the current song"""
    if ctx.voice_client and ctx.voice_client.is_playing():
      ctx.voice_client.stop()
      await ctx.reply('🎵 Skipped the current song!')
    else:
      await ctx.reply('⚠️ No song is currently playing.')

  @commands.command(name='stop')
  async def stop(self, ctx):
    """Stop music and disconnect the bot"""
    if ctx.voice_client:
      await ctx.voice_client.disconnect()
      await ctx.reply('🎵 Stopped music and disconnected from the voice channel.')
    else:
      await ctx.reply('⚠️ The bot is not in a voice channel.')


async def setup(bot):
  await bot.add_cog(ModMusicCog(bot))
