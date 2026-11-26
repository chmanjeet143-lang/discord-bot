from datetime import datetime, timezone
import time
import aiosqlite
import discord
from discord.ext import commands

DB_PATH = "utility_data.db"


class Utility(commands.Cog):
    """Server utilities, stats, counting, AFK, invites, aur prefix management."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.vc_join_times: dict[tuple[int, int], float] = {}
        self.invite_cache: dict[int, dict[str, int]] = {}

    async def cog_load(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT,
                    count_channel_id INTEGER,
                    last_count INTEGER DEFAULT 0,
                    last_counter_id INTEGER
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS afk_users (
                    guild_id INTEGER,
                    user_id INTEGER,
                    reason TEXT,
                    since INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_stats (
                    guild_id INTEGER,
                    user_id INTEGER,
                    msg_count INTEGER DEFAULT 0,
                    today_msg_count INTEGER DEFAULT 0,
                    last_msg_date TEXT,
                    tracked_since INTEGER,
                    vc_seconds INTEGER DEFAULT 0,
                    inv_count INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
                """
            )
            # Purane database tables ke liye safe migration columns
            for alter_sql in [
                "ALTER TABLE user_stats ADD COLUMN today_msg_count INTEGER DEFAULT 0",
                "ALTER TABLE user_stats ADD COLUMN last_msg_date TEXT",
                "ALTER TABLE user_stats ADD COLUMN tracked_since INTEGER",
            ]:
                try:
                    await db.execute(alter_sql)
                except aiosqlite.OperationalError:
                    pass

            await db.commit()

        for guild in self.bot.guilds:
            await self._cache_guild_invites(guild)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Process Denied !",
                description="❌ You don't have permission to use this command!",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Process Denied !",
                description="❌ Invalid argument provided! Please check your input and try again.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        raise error

    async def _cache_guild_invites(self, guild: discord.Guild):
        try:
            invites = await guild.invites()
            self.invite_cache[guild.id] = {inv.code: (inv.uses or 0) for inv in invites}
        except (discord.Forbidden, discord.HTTPException):
            self.invite_cache[guild.id] = {}

    @staticmethod
    def _today_key() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def _format_duration(seconds: int) -> str:
        seconds = max(0, int(seconds))
        hours, rem = divmod(seconds, 3600)
        minutes, secs = divmod(rem, 60)
        parts = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

    @staticmethod
    def _format_avg_daily(total_msgs: int, tracked_since: int | None) -> str:
        if total_msgs <= 0:
            return "0.00"
        if not tracked_since:
            return f"{float(total_msgs):.2f}"
        elapsed_days = max(1.0, (time.time() - tracked_since) / 86400.0)
        return f"{total_msgs / elapsed_days:.2f}"

    def _build_info_embed(
        self,
        title: str,
        description: str = None,
        color: discord.Color = discord.Color.blurple(),
        thumbnail_url: str = None,
    ) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        return embed

    async def _flush_vc_session(self, guild_id: int, user_id: int):
        key = (guild_id, user_id)
        joined_at = self.vc_join_times.pop(key, None)
        if joined_at is None:
            return
        elapsed = int(time.time() - joined_at)
        if elapsed <= 0:
            return

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO user_stats (guild_id, user_id, vc_seconds)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id, user_id)
                DO UPDATE SET vc_seconds = user_stats.vc_seconds + excluded.vc_seconds
                """,
                (guild_id, user_id, elapsed),
            )
            await db.commit()

    # -------------------- Listeners (AFK, Msg, VC, Counting, Invites) --------------------

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self._cache_guild_invites(guild)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if invite.guild:
            guild_invites = self.invite_cache.setdefault(invite.guild.id, {})
            guild_invites[invite.code] = invite.uses or 0

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        if invite.guild and invite.guild.id in self.invite_cache:
            self.invite_cache[invite.guild.id].pop(invite.code, None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        guild = member.guild
        old_cache = self.invite_cache.get(guild.id, {})
        used_inviter_id = None

        try:
            current_invites = await guild.invites()
            new_cache = {}
            for inv in current_invites:
                uses = inv.uses or 0
                new_cache[inv.code] = uses
                prev_uses = old_cache.get(inv.code, 0)
                if uses > prev_uses and inv.inviter:
                    used_inviter_id = inv.inviter.id
            self.invite_cache[guild.id] = new_cache
        except (discord.Forbidden, discord.HTTPException):
            pass

        if used_inviter_id:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    """
                    INSERT INTO user_stats (guild_id, user_id, inv_count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(guild_id, user_id)
                    DO UPDATE SET inv_count = user_stats.inv_count + 1
                    """,
                    (guild.id, used_inviter_id),
                )
                await db.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        if member.bot:
            return
        guild_id = member.guild.id
        user_id = member.id

        if before.channel is None and after.channel is not None:
            self.vc_join_times[(guild_id, user_id)] = time.time()
        elif before.channel is not None and after.channel is None:
            await self._flush_vc_session(guild_id, user_id)
        elif before.channel != after.channel:
            await self._flush_vc_session(guild_id, user_id)
            if after.channel is not None:
                self.vc_join_times[(guild_id, user_id)] = time.time()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        user_id = message.author.id
        today = self._today_key()
        now_ts = int(time.time())

        async with aiosqlite.connect(DB_PATH) as db:
            # 1. Remove AFK if sender was AFK (and not running the afk command)
            ctx = await self.bot.get_context(message)
            is_afk_cmd = ctx.valid and ctx.command and ctx.command.name == "afk"

            if not is_afk_cmd:
                cur = await db.execute(
                    "SELECT 1 FROM afk_users WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id),
                )
                if await cur.fetchone():
                    await db.execute(
                        "DELETE FROM afk_users WHERE guild_id = ? AND user_id = ?",
                        (guild_id, user_id),
                    )
                    await db.commit()
                    welcome_embed = self._build_info_embed(
                        title="▸ Welcome Back !",
                        description=f"▸ **User** : {message.author.mention}\n▸ **Status** : AFK removed",
                        color=discord.Color.green(),
                        thumbnail_url=message.author.display_avatar.url,
                    )
                    await message.reply(embed=welcome_embed, mention_author=False)

            # 2. Notify if any mentioned user is AFK
            if message.mentions:
                for mentioned in message.mentions:
                    if mentioned.id == user_id or mentioned.bot:
                        continue
                    cur = await db.execute(
                        "SELECT reason, since FROM afk_users WHERE guild_id = ? AND user_id = ?",
                        (guild_id, mentioned.id),
                    )
                    row = await cur.fetchone()
                    if row:
                        reason, since = row
                        since_text = f"<t:{since}:R>" if since else "recently"
                        afk_embed = self._build_info_embed(
                            title="▸ User is AFK !",
                            description=(
                                f"▸ **User** : {mentioned.mention}\n"
                                f"▸ **Reason** : {reason}\n"
                                f"▸ **AFK Since** : {since_text}"
                            ),
                            color=discord.Color.blurple(),
                            thumbnail_url=mentioned.display_avatar.url,
                        )
                        await message.reply(embed=afk_embed, mention_author=False)

            # 3. Increment total + today's message count
            cur_stat = await db.execute(
                "SELECT today_msg_count, last_msg_date, tracked_since FROM user_stats WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            )
            stat_row = await cur_stat.fetchone()
            if stat_row is None:
                await db.execute(
                    """
                    INSERT INTO user_stats (
                        guild_id, user_id, msg_count, today_msg_count, last_msg_date, tracked_since
                    )
                    VALUES (?, ?, 1, 1, ?, ?)
                    """,
                    (guild_id, user_id, today, now_ts),
                )
            else:
                prev_today, prev_date, tracked_since = stat_row
                next_today = ((prev_today or 0) + 1) if prev_date == today else 1
                next_since = tracked_since or now_ts
                await db.execute(
                    """
                    UPDATE user_stats
                    SET msg_count = msg_count + 1,
                        today_msg_count = ?,
                        last_msg_date = ?,
                        tracked_since = ?
                    WHERE guild_id = ? AND user_id = ?
                    """,
                    (next_today, today, next_since, guild_id, user_id),
                )

            # 4. Counting game check
            cur = await db.execute(
                "SELECT count_channel_id, last_count, last_counter_id FROM guild_settings WHERE guild_id = ?",
                (guild_id,),
            )
            settings = await cur.fetchone()
            if settings and settings[0] == message.channel.id:
                _, last_count, last_counter_id = settings
                expected = (last_count or 0) + 1
                content = message.content.strip()

                if not content.isdigit():
                    await db.commit()
                    return

                num = int(content)
                if last_counter_id == user_id or num != expected:
                    try:
                        await message.add_reaction("❌")
                    except discord.HTTPException:
                        pass
                    await db.execute(
                        "UPDATE guild_settings SET last_count = 0, last_counter_id = NULL WHERE guild_id = ?",
                        (guild_id,),
                    )
                    await db.commit()
                    reason_text = (
                        "One user cannot count twice in a row!"
                        if last_counter_id == user_id
                        else f"Wrong number! Expected **{expected}**."
                    )
                    count_err_embed = self._build_info_embed(
                        title="▸ Counting Reset !",
                        description=(
                            f"▸ **User** : {message.author.mention}\n"
                            f"▸ **Reason** : {reason_text}\n"
                            f"▸ **Next Count** : **1**"
                        ),
                        color=discord.Color.red(),
                    )
                    await message.channel.send(embed=count_err_embed)
                    return

                try:
                    await message.add_reaction("✅")
                except discord.HTTPException:
                    pass
                await db.execute(
                    "UPDATE guild_settings SET last_count = ?, last_counter_id = ? WHERE guild_id = ?",
                    (num, user_id, guild_id),
                )

            await db.commit()

    # -------------------- Commands --------------------

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Websocket, Message aur API latency embed mein dikhata hai."""
        start = time.perf_counter()
        ws_ms = round(self.bot.latency * 1000)
        msg_ms = round((time.perf_counter() - ctx.message.created_at.timestamp()) * 1000)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name="☁️ Bot's Latency")
        embed.description = (
            f"__**Websocket Latency :**__ `{ws_ms} ms`\n"
            f"__**Message Latency :**__ `{max(1, msg_ms)} ms`\n"
            f"__**API Latency :**__ `{ws_ms} ms`"
        )
        thumb = ctx.guild.icon.url if (ctx.guild and ctx.guild.icon) else self.bot.user.display_avatar.url
        embed.set_thumbnail(url=thumb)

        api_start = time.perf_counter()
        sent = await ctx.send(embed=embed)
        api_ms = max(1, round((time.perf_counter() - api_start) * 1000))

        embed.description = (
            f"__**Websocket Latency :**__ `{ws_ms} ms`\n"
            f"__**Message Latency :**__ `{max(1, msg_ms)} ms`\n"
            f"__**API Latency :**__ `{api_ms} ms`"
        )
        await sent.edit(embed=embed)

    @commands.command(name="setcountchannel")
    @commands.has_permissions(manage_channels=True)
    async def setcountchannel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Counting game ke liye channel set karta hai."""
        target = channel or ctx.channel
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO guild_settings (guild_id, count_channel_id, last_count, last_counter_id)
                VALUES (?, ?, 0, NULL)
                ON CONFLICT(guild_id)
                DO UPDATE SET count_channel_id = excluded.count_channel_id, last_count = 0, last_counter_id = NULL
                """,
                (ctx.guild.id, target.id),
            )
            await db.commit()

        embed = self._build_info_embed(
            title="▸ Counting Channel Set",
            description=(
                f"▸ **Channel** : {target.mention}\n"
                f"▸ **Start From** : **1**\n"
                f"▸ **Set By** : {ctx.author.mention}"
            ),
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="afk")
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        """Optional reason ke saath AFK status set karta hai."""
        now_ts = int(time.time())
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO afk_users (guild_id, user_id, reason, since)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id)
                DO UPDATE SET reason = excluded.reason, since = excluded.since
                """,
                (ctx.guild.id, ctx.author.id, reason, now_ts),
            )
            await db.commit()

        embed = self._build_info_embed(
            title="▸ User is AFK !",
            description=(
                f"▸ **User** : {ctx.author.mention}\n"
                f"▸ **Reason** : {reason}\n"
                f"▸ **AFK Since** : <t:{now_ts}:R>"
            ),
            color=discord.Color.blurple(),
            thumbnail_url=ctx.author.display_avatar.url,
        )
        await ctx.send(embed=embed)

    @commands.command(name="msg")
    async def msg(self, ctx: commands.Context, member: discord.Member = None):
        """Message Tracker embed dikhata hai (User, Total Messages, Today's Messages, Avg. Daily)."""
        target = member or ctx.author
        today = self._today_key()

        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                """
                SELECT msg_count, today_msg_count, last_msg_date, tracked_since
                FROM user_stats
                WHERE guild_id = ? AND user_id = ?
                """,
                (ctx.guild.id, target.id),
            )
            row = await cur.fetchone()

        total_msgs = row[0] if (row and row[0]) else 0
        today_msgs = row[1] if (row and row[2] == today and row[1]) else 0
        tracked_since = row[3] if row else None
        avg_daily = self._format_avg_daily(total_msgs, tracked_since)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name="▸ Message Tracker")
        embed.description = (
            f"▸ **User:** {target.mention}\n"
            f"▸ **Total Messages:** `{total_msgs}`\n"
            f"▸ **Today's Messages:** `{today_msgs}`\n"
            f"▸ **Avg. Daily:** `{avg_daily}`"
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="vc")
    async def vc(self, ctx: commands.Context, member: discord.Member = None):
        """Voice time tracker embed dikhata hai."""
        target = member or ctx.author
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "SELECT vc_seconds FROM user_stats WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, target.id),
            )
            row = await cur.fetchone()

        total_seconds = row[0] if (row and row[0]) else 0
        active_join = self.vc_join_times.get((ctx.guild.id, target.id))
        if active_join is not None:
            total_seconds += int(time.time() - active_join)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name="▸ Voice Tracker")
        embed.description = (
            f"▸ **User:** {target.mention}\n"
            f"▸ **Total Voice Time:** `{self._format_duration(total_seconds)}`"
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="inv")
    async def inv(self, ctx: commands.Context, member: discord.Member = None):
        """Invite tracker embed dikhata hai."""
        target = member or ctx.author
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "SELECT inv_count FROM user_stats WHERE guild_id = ? AND user_id = ?",
                (ctx.guild.id, target.id),
            )
            row = await cur.fetchone()
        invites = row[0] if (row and row[0]) else 0

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name="▸ Invite Tracker")
        embed.description = (
            f"▸ **User:** {target.mention}\n"
            f"▸ **Total Invites:** `{invites}`"
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    async def _build_leaderboard(self, ctx: commands.Context, column: str, title: str, formatter):
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                f"""
                SELECT user_id, {column}
                FROM user_stats
                WHERE guild_id = ? AND {column} > 0
                ORDER BY {column} DESC
                LIMIT 10
                """,
                (ctx.guild.id,),
            )
            rows = await cur.fetchall()

        if not rows:
            embed = self._build_info_embed(
                title=f"▸ {title}",
                description="▸ **Status** : No leaderboard data available yet.",
                color=discord.Color.blurple(),
                thumbnail_url=ctx.guild.icon.url if ctx.guild.icon else None,
            )
            await ctx.send(embed=embed)
            return

        lines = []
        for idx, (uid, val) in enumerate(rows, start=1):
            member = ctx.guild.get_member(uid)
            name = member.mention if member else f"User (`{uid}`)"
            lines.append(f"▸ **`#{idx}`** {name} — `{formatter(val)}`")

        embed = discord.Embed(
            description="\n".join(lines),
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(name=f"▸ {title}")
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @commands.command(name="lbmsg")
    async def lbmsg(self, ctx: commands.Context):
        """Message leaderboard embed dikhata hai."""
        await self._build_leaderboard(ctx, "msg_count", "Message Leaderboard", lambda v: f"{v} msgs")

    @commands.command(name="lbvc")
    async def lbvc(self, ctx: commands.Context):
        """Voice time leaderboard embed dikhata hai."""
        await self._build_leaderboard(
            ctx, "vc_seconds", "Voice Time Leaderboard", self._format_duration
        )

    @commands.command(name="lbinv")
    async def lbinv(self, ctx: commands.Context):
        """Invite leaderboard embed dikhata hai."""
        await self._build_leaderboard(ctx, "inv_count", "Invite Leaderboard", lambda v: f"{v} invites")

    @commands.command(name="resetmsg")
    @commands.has_permissions(administrator=True)
    async def resetmsg(self, ctx: commands.Context, member: discord.Member = None):
        """Ek user ya sabhi users ke message stats reset karta hai."""
        async with aiosqlite.connect(DB_PATH) as db:
            if member:
                await db.execute(
                    """
                    UPDATE user_stats
                    SET msg_count = 0, today_msg_count = 0, tracked_since = NULL
                    WHERE guild_id = ? AND user_id = ?
                    """,
                    (ctx.guild.id, member.id),
                )
                desc = f"▸ **Target** : {member.mention}\n▸ **Stat Reset** : Message stats"
            else:
                await db.execute(
                    """
                    UPDATE user_stats
                    SET msg_count = 0, today_msg_count = 0, tracked_since = NULL
                    WHERE guild_id = ?
                    """,
                    (ctx.guild.id,),
                )
                desc = "▸ **Target** : All server members\n▸ **Stat Reset** : Message stats"
            await db.commit()

        embed = self._build_info_embed(
            title="▸ Message Stats Reset",
            description=desc,
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="resetvc")
    @commands.has_permissions(administrator=True)
    async def resetvc(self, ctx: commands.Context, member: discord.Member = None):
        """Ek user ya sabhi users ke voice stats reset karta hai."""
        async with aiosqlite.connect(DB_PATH) as db:
            if member:
                self.vc_join_times.pop((ctx.guild.id, member.id), None)
                await db.execute(
                    "UPDATE user_stats SET vc_seconds = 0 WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, member.id),
                )
                desc = f"▸ **Target** : {member.mention}\n▸ **Stat Reset** : Voice stats"
            else:
                keys_to_remove = [k for k in self.vc_join_times if k[0] == ctx.guild.id]
                for k in keys_to_remove:
                    self.vc_join_times.pop(k, None)
                await db.execute(
                    "UPDATE user_stats SET vc_seconds = 0 WHERE guild_id = ?",
                    (ctx.guild.id,),
                )
                desc = "▸ **Target** : All server members\n▸ **Stat Reset** : Voice stats"
            await db.commit()

        embed = self._build_info_embed(
            title="▸ Voice Stats Reset",
            description=desc,
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="resetinv")
    @commands.has_permissions(administrator=True)
    async def resetinv(self, ctx: commands.Context, member: discord.Member = None):
        """Ek user ya sabhi users ke invite stats reset karta hai."""
        async with aiosqlite.connect(DB_PATH) as db:
            if member:
                await db.execute(
                    "UPDATE user_stats SET inv_count = 0 WHERE guild_id = ? AND user_id = ?",
                    (ctx.guild.id, member.id),
                )
                desc = f"▸ **Target** : {member.mention}\n▸ **Stat Reset** : Invite stats"
            else:
                await db.execute(
                    "UPDATE user_stats SET inv_count = 0 WHERE guild_id = ?",
                    (ctx.guild.id,),
                )
                desc = "▸ **Target** : All server members\n▸ **Stat Reset** : Invite stats"
            await db.commit()

        embed = self._build_info_embed(
            title="▸ Invite Stats Reset",
            description=desc,
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="say")
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx: commands.Context, *, text: str):
        """Bot se embed message bhejwata hai."""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        embed = discord.Embed(description=text, color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.command(name="reply")
    @commands.has_permissions(manage_messages=True)
    async def reply(self, ctx: commands.Context, target_message: discord.Message = None, *, text: str = None):
        """Kisi message ka reply embed ke saath bot ke zariye bhejwata hai."""
        ref_msg = target_message or (ctx.message.reference.resolved if ctx.message.reference else None)
        if not isinstance(ref_msg, discord.Message) and ctx.message.reference and ctx.message.reference.message_id:
            try:
                ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.HTTPException:
                ref_msg = None

        if not ref_msg or not text:
            err_embed = self._build_info_embed(
                title="Process Denied !",
                description="❌ Reply a message with text or provide `<message_id_or_link> <text>`.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=err_embed)
            return

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        reply_embed = discord.Embed(description=text, color=discord.Color.blurple())
        await ref_msg.reply(embed=reply_embed, mention_author=False)

    @commands.command(name="invite")
    @commands.has_permissions(create_instant_invite=True)
    async def invite(self, ctx: commands.Context, max_age: int = 86400, max_uses: int = 0):
        """Server ke liye naya invite link embed mein banata hai."""
        try:
            inv = await ctx.channel.create_invite(max_age=max_age, max_uses=max_uses)
            embed = self._build_info_embed(
                title="▸ Server Invite Created",
                description=(
                    f"▸ **Invite Link** : {inv.url}\n"
                    f"▸ **Channel** : {ctx.channel.mention}"
                ),
                color=discord.Color.blurple(),
                thumbnail_url=ctx.guild.icon.url if ctx.guild.icon else None,
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            err_embed = self._build_info_embed(
                title="Process Denied !",
                description="❌ Bot does not have permission to create an invite link.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=err_embed)

    @commands.command(name="setprefix")
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx: commands.Context, new_prefix: str):
        """Is server ke liye bot ka prefix embed confirmation ke saath badalta hai."""
        if len(new_prefix) > 10:
            err_embed = self._build_info_embed(
                title="Process Denied !",
                description="❌ Prefix must be 10 characters or fewer.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=err_embed)
            return

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO guild_settings (guild_id, prefix)
                VALUES (?, ?)
                ON CONFLICT(guild_id)
                DO UPDATE SET prefix = excluded.prefix
                """,
                (ctx.guild.id, new_prefix),
            )
            await db.commit()

        embed = self._build_info_embed(
            title="▸ Prefix Updated",
            description=(
                f"▸ **New Prefix** : `{new_prefix}`\n"
                f"▸ **Updated By** : {ctx.author.mention}"
            ),
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
