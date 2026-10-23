import asyncio
from datetime import datetime, timedelta
import aiosqlite
import discord
from discord.ext import commands, tasks

DB_NAME = "bump_data.db"


class Bump(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.db_path = "bump_data.db"
    self.bump_checker.start()

  async def ensure_db(self):
    """Ensure database and table always exist"""
    async with aiosqlite.connect(self.db_path) as db:
      await db.execute("""
                CREATE TABLE IF NOT EXISTS bump_settings (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    role_id INTEGER,
                    custom_msg TEXT DEFAULT 'It''s time to bump! 🔔\nDrop that \`/bump\` right now to push Moonlight Heaven 🌙 to the top!',
                    thanks_msg TEXT DEFAULT 'Thank you for the bump legend! You''re keeping Moonlight Heaven 🌙 active ❤️',
                    next_bump_time TEXT
                )
            """)
      try:
        await db.execute(
            "ALTER TABLE bump_settings ADD COLUMN thanks_msg TEXT DEFAULT"
            " 'Thank you for the bump legend! You''re keeping Moonlight"
            " Heaven 🌙 active ❤️'"
        )
      except Exception:
        pass
      await db.commit()

  def cog_unload(self):
    self.bump_checker.cancel()

  # --- BACKGROUND LOOP: Timer check karne ke liye ---
  @tasks.loop(seconds=30)
  async def bump_checker(self):
    await self.bot.wait_until_ready()
    await self.ensure_db()
    now = datetime.utcnow()

    try:
      async with aiosqlite.connect(self.db_path) as db:
        async with db.execute(
            "SELECT guild_id, channel_id, role_id, custom_msg, next_bump_time"
            " FROM guild_settings WHERE next_bump_time IS NOT NULL"
        ) as cursor:
          rows = await cursor.fetchall()

          for guild_id, channel_id, role_id, custom_msg, next_bump_str in rows:
            next_bump_time = datetime.fromisoformat(next_bump_str)

            if now >= next_bump_time:
              guild = self.bot.get_guild(guild_id)
              if guild:
                channel = guild.get_channel(channel_id)
                if channel:
                  role_mention = f"<@&{role_id}>" if role_id else ""
                  final_msg = (
                      f"{role_mention}\n{custom_msg}" if role_id else custom_msg
                  )
                  await channel.send(final_msg)

              await db.execute(
                  "UPDATE guild_settings SET next_bump_time = NULL WHERE"
                  " guild_id = ?",
                  (guild_id,),
              )
              await db.commit()
    except Exception as e:
      print(f"Error in bump_checker loop: {e}")

  @bump_checker.before_loop
  async def before_bump_checker(self):
    await self.bot.wait_until_ready()

  # --- EVENT: Disboard Success Detection ---
  @commands.Cog.listener()
  async def on_message(self, message):
    if message.author.id == 302050872383242240:  # Disboard Bot ID
      if message.embeds:
        embed = message.embeds[0]
        desc = embed.description or ""
        if "Bump done" in desc or "Server bumped successfully" in desc:
          guild = message.guild
          await self.ensure_db()

          async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT channel_id, thanks_msg FROM guild_settings WHERE"
                " guild_id = ?",
                (guild.id,),
            ) as cursor:
              row = await cursor.fetchone()

          channel_id = row[0] if row else None
          thanks_msg = (
              row[1]
              if row and row[1]
              else "Thank you for the bump legend! You're keeping Moonlight"
              " Heaven 🌙 active ❤️"
          )

          target_channel = guild.get_channel(channel_id) or message.channel

          user_mention = ""
          if message.interaction and message.interaction.user:
            user_mention = message.interaction.user.mention

          final_thanks = (
              f"{thanks_msg}\n{user_mention}" if user_mention else thanks_msg
          )
          await target_channel.send(final_thanks)

          next_time = (datetime.utcnow() + timedelta(hours=2)).isoformat()
          async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE guild_settings SET next_bump_time = ? WHERE"
                " guild_id = ?",
                (next_time, guild.id),
            )
            await db.commit()

  # --- PREFIX COMMANDS ---

  @commands.command(name="setbumpchannel")
  async def setbumpchannel(self, ctx, channel: discord.TextChannel):
    """Bump reminder aur thank you message ka channel set karein"""
    await self.ensure_db()
    try:
      async with aiosqlite.connect(self.db_path) as db:
        await db.execute(
            """
                    INSERT INTO guild_settings (guild_id, channel_id) VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET channel_id = excluded.channel_id
                """,
            (ctx.guild.id, channel.id),
        )
        await db.commit()
      await ctx.send(
          f"✅ Bump channel successfully set to {channel.mention}!"
      )
    except Exception as e:
      await ctx.send(f"❌ Error aa gaya: `{e}`")

  @commands.command(name="setbumprole")
  async def setbumprole(self, ctx, role: discord.Role):
    """Reminder ke waqt kaunsa role ping ho set karein"""
    await self.ensure_db()
    try:
      async with aiosqlite.connect(self.db_path) as db:
        await db.execute(
            """
                    INSERT INTO guild_settings (guild_id, role_id) VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET role_id = excluded.role_id
                """,
            (ctx.guild.id, role.id),
        )
        await db.commit()
      await ctx.send(f"✅ Bump ping role successfully set to {role.mention}!")
    except Exception as e:
      await ctx.send(f"❌ Error aa gaya: `{e}`")

  @commands.command(name="setbumpmsg")
  async def setbumpmsg(self, ctx, *, message: str):
    """Reminder message ko change karne ke liye"""
    await self.ensure_db()
    try:
      async with aiosqlite.connect(self.db_path) as db:
        await db.execute(
            """
                    INSERT INTO guild_settings (guild_id, custom_msg) VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET custom_msg = excluded.custom_msg
                """,
            (ctx.guild.id, message),
        )
        await db.commit()
      await ctx.send(
          f"✅ Reminder message successfully update ho gaya hai:\n\n> {message}"
      )
    except Exception as e:
      await ctx.send(f"❌ Error aa gaya: `{e}`")

  @commands.command(name="setthanksmsg")
  async def setthanksmsg(self, ctx, *, message: str):
    """Thank you message ko change karne ke liye"""
    await self.ensure_db()
    try:
      async with aiosqlite.connect(self.db_path) as db:
        await db.execute(
            """
                    INSERT INTO guild_settings (guild_id, thanks_msg) VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET thanks_msg = excluded.thanks_msg
                """,
            (ctx.guild.id, message),
        )
        await db.commit()
      await ctx.send(
          f"✅ Thank you message successfully update ho gaya"
          f" hai:\n\n> {message}\n(Sath me user mention bhi aayega)"
      )
    except Exception as e:
      await ctx.send(f"❌ Error aa gaya: `{e}`")

  @commands.command(name="bumptime")
  async def bumptime(self, ctx):
    """Check karein ki agla bump kab kar sakte hain"""
    await self.ensure_db()
    try:
      async with aiosqlite.connect(self.db_path) as db:
        async with db.execute(
            "SELECT next_bump_time FROM guild_settings WHERE guild_id = ?",
            (ctx.guild.id,),
        ) as cursor:
          row = await cursor.fetchone()

      if not row or not row[0]:
        await ctx.send(
            "🚀 Abhi koi active bump timer nahi hai! Aap abhi `/bump` kar sakte"
            " hain."
        )
        return

      next_bump = datetime.fromisoformat(row[0])
      now = datetime.utcnow()

      if now >= next_bump:
        await ctx.send(
            "🚀 Bump cooldown khatam ho chuka hai! Aap `/bump` kar sakte hain."
        )
      else:
        remaining = next_bump - now
        mins = int(remaining.total_seconds() // 60)
        hours = mins // 60
        m = mins % 60
        await ctx.send(
            f"⏳ Agla bump **{hours} ghante {m} minute** baad kiya ja sakega."
        )
    except Exception as e:
      await ctx.send(f"❌ Error aa gaya: `{e}`")


async def setup(bot):
  await bot.add_cog(Bump(bot))
