from datetime import datetime, timedelta
import aiosqlite
import discord
from discord.ext import commands, tasks

DB_NAME = "bump_data.db"
DEFAULT_BUMP_CHANNEL_ID = 1533503384903094444
DEFAULT_BUMP_ROLE_ID = 1535745141296463893

DEFAULT_REMINDER_MSG = (
    "⏰ **2 hours** are up! Time to bump **Love Heaven** again! 💖\n"
    "Drop `/bump` right now to push **Love Heaven** to the top!"
)

DEFAULT_BUMP_MSG = (
    "✨ **Love Heaven** has been bumped! ✨\n"
    "Come hang out, make new friends, and enjoy great vibes in our community! 💖\n"
    "👉 Next bump will be ready in **2 hours**."
)

DEFAULT_THANKS_MSG = (
    "🎉 Huge thanks, {user}! 🎉\n"
    "You just helped **Love Heaven** grow with a fresh bump—we truly appreciate your support! 💖"
)


class Bump(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.db_path = DB_NAME
    self.bump_checker.start()

  async def ensure_db(self):
    """Ensure database and table always exist."""
    async with aiosqlite.connect(self.db_path) as db:
      await db.execute(f"""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER DEFAULT {DEFAULT_BUMP_CHANNEL_ID},
                    role_id INTEGER DEFAULT {DEFAULT_BUMP_ROLE_ID},
                    custom_msg TEXT DEFAULT {DEFAULT_REMINDER_MSG!r},
                    thanks_msg TEXT DEFAULT {DEFAULT_THANKS_MSG!r},
                    next_bump_time TEXT
                )
            """)
      try:
        await db.execute(
            "ALTER TABLE guild_settings ADD COLUMN thanks_msg TEXT DEFAULT"
            f" {DEFAULT_THANKS_MSG!r}"
        )
      except Exception:
        pass
      await db.commit()

  async def ensure_default_for_guild(self, guild: discord.Guild):
    """Ensure default channel, role, and 2-hour fallback timer exist on startup/restart."""
    if not guild:
      return

    await self.ensure_db()
    now_iso = (datetime.utcnow() + timedelta(hours=2)).isoformat()

    async with aiosqlite.connect(self.db_path) as db:
      async with db.execute(
          "SELECT channel_id, role_id, custom_msg, thanks_msg, next_bump_time"
          " FROM guild_settings WHERE guild_id = ?",
          (guild.id,),
      ) as cursor:
        row = await cursor.fetchone()

      if not row:
        await db.execute(
            """
                    INSERT INTO guild_settings (
                        guild_id, channel_id, role_id, custom_msg, thanks_msg, next_bump_time
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
            (
                guild.id,
                DEFAULT_BUMP_CHANNEL_ID,
                DEFAULT_BUMP_ROLE_ID,
                DEFAULT_REMINDER_MSG,
                DEFAULT_THANKS_MSG,
                now_iso,
            ),
        )
      else:
        channel_id = row[0] or DEFAULT_BUMP_CHANNEL_ID
        role_id = row[1] or DEFAULT_BUMP_ROLE_ID
        custom_msg = row[2] or DEFAULT_REMINDER_MSG
        thanks_msg = row[3] or DEFAULT_THANKS_MSG
        next_bump_time = row[4] or now_iso

        await db.execute(
            """
                    UPDATE guild_settings
                    SET channel_id = ?, role_id = ?, custom_msg = ?, thanks_msg = ?, next_bump_time = ?
                    WHERE guild_id = ?
                    """,
            (
                channel_id,
                role_id,
                custom_msg,
                thanks_msg,
                next_bump_time,
                guild.id,
            ),
        )

      await db.commit()

  async def seed_all_guilds(self):
    for guild in self.bot.guilds:
      await self.ensure_default_for_guild(guild)

  def cog_unload(self):
    self.bump_checker.cancel()

  @commands.Cog.listener()
  async def on_ready(self):
    await self.seed_all_guilds()

  @commands.Cog.listener()
  async def on_guild_join(self, guild: discord.Guild):
    await self.ensure_default_for_guild(guild)

  # --- BACKGROUND LOOP: 2-hour timer & auto cycle ---
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
            target_channel_id = channel_id or DEFAULT_BUMP_CHANNEL_ID
            target_role_id = role_id or DEFAULT_BUMP_ROLE_ID
            reminder_text = custom_msg or DEFAULT_REMINDER_MSG

            if guild:
              channel = guild.get_channel(target_channel_id)
              if channel:
                role_mention = f"<@&{target_role_id}>" if target_role_id else ""
                final_msg = (
                    f"{role_mention}\n{reminder_text}"
                    if role_mention
                    else reminder_text
                )
                await channel.send(final_msg)

            # Next 2-hour reminder timer automatically schedule
            new_next_bump = (datetime.utcnow() + timedelta(hours=2)).isoformat()
            await db.execute(
                "UPDATE guild_settings SET next_bump_time = ? WHERE"
                " guild_id = ?",
                (new_next_bump, guild_id),
            )
            await db.commit()
    except Exception as e:
      print(f"Error in bump_checker loop: {e}")

  @bump_checker.before_loop
  async def before_bump_checker(self):
    await self.bot.wait_until_ready()
    await self.seed_all_guilds()

  # --- EVENT: Disboard Success Detection ---
  @commands.Cog.listener()
  async def on_message(self, message: discord.Message):
    if message.author.id == 302050872383242240:  # Disboard Bot ID
      if message.embeds:
        embed = message.embeds[0]
        desc = embed.description or ""
        if "Bump done" in desc or "Server bumped successfully" in desc:
          guild = message.guild
          if not guild:
            return

          await self.ensure_default_for_guild(guild)

          async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT channel_id, thanks_msg FROM guild_settings WHERE"
                " guild_id = ?",
                (guild.id,),
            ) as cursor:
              row = await cursor.fetchone()

          channel_id = (row[0] if row and row[0] else DEFAULT_BUMP_CHANNEL_ID)
          thanks_template = (
              row[1] if row and row[1] else DEFAULT_THANKS_MSG
          )

          target_channel = guild.get_channel(channel_id) or message.channel

          user_mention = ""
          if message.interaction and message.interaction.user:
            user_mention = message.interaction.user.mention

          if "{user}" in thanks_template:
            final_thanks = thanks_template.replace(
                "{user}", user_mention or "there"
            )
          else:
            final_thanks = (
                f"{thanks_template}\n{user_mention}"
                if user_mention
                else thanks_template
            )

          await target_channel.send(DEFAULT_BUMP_MSG)
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
    """Set the channel for bump reminders and thank you messages."""
    await self.ensure_default_for_guild(ctx.guild)
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
      await ctx.send(f"❌ Error occurred: `{e}`")

  @commands.command(name="setbumprole")
  async def setbumprole(self, ctx, role: discord.Role):
    """Set the role to be pinged during bump reminders."""
    await self.ensure_default_for_guild(ctx.guild)
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
      await ctx.send(f"❌ Error occurred: `{e}`")

  @commands.command(name="setbumpmsg")
  async def setbumpmsg(self, ctx, *, message: str):
    """Customize the reminder message sent after 2 hours."""
    await self.ensure_default_for_guild(ctx.guild)
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
          f"✅ Reminder message successfully updated:\n\n> {message}"
      )
    except Exception as e:
      await ctx.send(f"❌ Error occurred: `{e}`")

  @commands.command(name="setthanksmsg")
  async def setthanksmsg(self, ctx, *, message: str):
    """Customize the thank you message sent when someone bumps."""
    await self.ensure_default_for_guild(ctx.guild)
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
          f"✅ Thank you message successfully updated:\n\n> {message}\n(Use"
          " `{user}` wherever you want the member mention)"
      )
    except Exception as e:
      await ctx.send(f"❌ Error occurred: `{e}`")

  @commands.command(name="bumptime")
  async def bumptime(self, ctx):
    """Check how much cooldown time is remaining for the next bump."""
    await self.ensure_default_for_guild(ctx.guild)
    try:
      async with aiosqlite.connect(self.db_path) as db:
        async with db.execute(
            "SELECT next_bump_time FROM guild_settings WHERE guild_id = ?",
            (ctx.guild.id,),
        ) as cursor:
          row = await cursor.fetchone()

      if not row or not row[0]:
        await ctx.send(
            "🚀 There is no active bump timer! You can use `/bump` right now."
        )
        return

      next_bump = datetime.fromisoformat(row[0])
      now = datetime.utcnow()

      if now >= next_bump:
        await ctx.send(
            "🚀 Bump cooldown has finished! You can use `/bump` now."
        )
      else:
        remaining = next_bump - now
        mins = int(remaining.total_seconds() // 60)
        hours = mins // 60
        m = mins % 60
        await ctx.send(
            f"⏳ Next bump will be available in **{hours} hours and {m}"
            " minutes**."
        )
    except Exception as e:
      await ctx.send(f"❌ Error occurred: `{e}`")


async def setup(bot):
  await bot.add_cog(Bump(bot))
