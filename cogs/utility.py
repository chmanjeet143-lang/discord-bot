import asyncio
import datetime
import io
import json
import os
import re
import aiohttp
import discord
from discord import ui
from discord.ext import commands

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"
IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1532422031650455655/"
    "1573473889915502682/IMG_3099.png"
    "?ex=6b022341&is=6b00d1c1&hm=30f2f09afc213ed06927a0d470e0c00f59cddbe2158d58632a47cd1e3f59f422&"
)
BOT_CREDIT = "Bot Made By : Zeus"
SERVER_BRAND = "Love heaven"
PREFIX_FILE = "prefixes.json"
DATA_FILE = "utility_data.json"

HAS_COMPONENTS_V2 = (
    hasattr(discord.ui, "LayoutView")
    and hasattr(discord.ui, "Container")
    and hasattr(discord.ui, "Section")
    and hasattr(discord.ui, "MediaGallery")
)


def load_json(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def save_json(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


def load_prefixes() -> dict:
    return load_json(PREFIX_FILE)


def save_prefixes(prefixes: dict) -> None:
    save_json(PREFIX_FILE, prefixes)


async def get_prefix(bot, message: discord.Message):
    if not message.guild:
        return "&"
    prefixes = load_prefixes()
    return prefixes.get(str(message.guild.id), "&")


def format_time(seconds: int) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"


def today_key() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def get_thumb_url(target=None, bot=None, guild=None) -> str:
    if target is not None and getattr(target, "display_avatar", None):
        return target.display_avatar.url
    if bot is not None and getattr(bot, "user", None) and getattr(bot.user, "display_avatar", None):
        return bot.user.display_avatar.url
    if guild is not None and getattr(guild, "icon", None) and guild.icon:
        return guild.icon.url
    return DEFAULT_AVATAR


def build_card_embed(
    title: str = "",
    description: str = "",
    color: int = 0x2B2D31,
    thumb_url: str | None = None,
    banner_url: str | None = None,
) -> discord.Embed:
    heading = f"### ▸ {title}\n" if title else ""
    embed = discord.Embed(
        description=f"{heading}{description}".strip(),
        color=color,
    )
    if thumb_url:
        embed.set_thumbnail(url=thumb_url)
    if banner_url:
        embed.set_image(url=banner_url)
    embed.set_footer(text=f"{SERVER_BRAND} • {BOT_CREDIT}")
    return embed


def build_card_v2(
    title: str,
    body: str,
    thumb_url: str | None = None,
    banner_url: str | None = None,
    accent_color: int = 0x2B2D31,
) -> ui.LayoutView:
    children: list[discord.ui.Item] = []

    if banner_url:
        children.append(discord.ui.MediaGallery(discord.MediaGalleryItem(media=banner_url)))

    header_text = f"### ▸ {title}\n{body}".strip() if title else body
    if thumb_url:
        children.append(
            discord.ui.Section(
                discord.ui.TextDisplay(header_text),
                accessory=discord.ui.Thumbnail(media=thumb_url),
            )
        )
    else:
        children.append(discord.ui.TextDisplay(header_text))

    children.append(discord.ui.Separator())
    children.append(discord.ui.TextDisplay(f"-# {SERVER_BRAND} • {BOT_CREDIT}"))

    view = ui.LayoutView(timeout=None)
    view.add_item(discord.ui.Container(*children, accent_color=accent_color))
    return view


async def send_card(
    destination,
    title: str = "",
    body: str = "",
    color: int = 0x2B2D31,
    thumb_url: str | None = None,
    banner_url: str | None = None,
    delete_after: float | None = None,
    allowed_mentions: discord.AllowedMentions | None = None,
):
    if HAS_COMPONENTS_V2:
        view = build_card_v2(
            title=title,
            body=body,
            thumb_url=thumb_url,
            banner_url=banner_url,
            accent_color=color,
        )
        kwargs = {"view": view}
        if delete_after is not None:
            kwargs["delete_after"] = delete_after
        if allowed_mentions is not None:
            kwargs["allowed_mentions"] = allowed_mentions
        return await destination.send(**kwargs)

    embed = build_card_embed(
        title=title,
        description=body,
        color=color,
        thumb_url=thumb_url,
        banner_url=banner_url,
    )
    kwargs = {"embed": embed}
    if delete_after is not None:
        kwargs["delete_after"] = delete_after
    if allowed_mentions is not None:
        kwargs["allowed_mentions"] = allowed_mentions
    return await destination.send(**kwargs)


def create_embed(guild, title: str = "", description: str = "", color=0x2B2D31) -> discord.Embed:
    color_int = color.value if isinstance(color, discord.Color) else int(color)
    thumb = guild.icon.url if (guild and getattr(guild, "icon", None) and guild.icon) else DEFAULT_AVATAR
    return build_card_embed(title=title, description=description, color=color_int, thumb_url=thumb)


def default_guild_record() -> dict:
    return {
        "counting": {
            "channel_id": None,
            "current_count": 1,
            "success_emoji": "✅",
            "last_user_id": None,
        },
        "message_counts": {},
        "daily_messages": {},
        "first_seen": {},
        "invite_counts": {},
        "invite_links": {},  # code -> {"inviter_id": int, "uses": int, "owner_name": str}
        "voice_time_seconds": {},
        "vc_joins": {},
        "afk_users": {},
    }


class Utility(commands.Cog, name="Utility"):
    """Explore all commands related to Utility and Games."""

    def __init__(self, bot):
        self.bot = bot
        self.data = load_json(DATA_FILE)
        self.invite_cache: dict[int, dict[str, int]] = {}

    def save(self) -> None:
        save_json(DATA_FILE, self.data)

    def gdata(self, guild_id: int | str) -> dict:
        gid = str(guild_id)
        base = default_guild_record()
        if gid not in self.data or not isinstance(self.data[gid], dict):
            self.data[gid] = base
            return self.data[gid]

        entry = self.data[gid]
        for k, v in base.items():
            if k not in entry or not isinstance(entry[k], type(v)):
                entry[k] = v if not isinstance(v, dict) else dict(v)
        if isinstance(entry.get("counting"), dict):
            for ck, cv in base["counting"].items():
                if ck not in entry["counting"]:
                    entry["counting"][ck] = cv
        return entry

    def _record_user_message(self, guild_id: int | str, user_id: int | str):
        g = self.gdata(guild_id)
        uid = str(user_id)
        today = today_key()

        g["message_counts"][uid] = int(g["message_counts"].get(uid, 0)) + 1

        day_map = g["daily_messages"].setdefault(today, {})
        day_map[uid] = int(day_map.get(uid, 0)) + 1

        if uid not in g["first_seen"]:
            g["first_seen"][uid] = today

    def _calc_daily_avg(self, g: dict, uid: str, total_msgs: int) -> str:
        if total_msgs <= 0:
            return "0.00"
        seen_str = g.get("first_seen", {}).get(uid)
        days = 1
        if seen_str:
            try:
                start_dt = datetime.datetime.strptime(seen_str, "%Y-%m-%d").date()
                now_dt = datetime.datetime.now(datetime.timezone.utc).date()
                days = max(1, (now_dt - start_dt).days + 1)
            except Exception:
                days = 1
        return f"{total_msgs / days:.2f}"

    async def _refresh_guild_invites(self, guild: discord.Guild):
        try:
            invites = await guild.invites()
            self.invite_cache[guild.id] = {inv.code: int(inv.uses or 0) for inv in invites}
            g = self.gdata(guild.id)
            for inv in invites:
                if inv.code in g["invite_links"]:
                    g["invite_links"][inv.code]["uses"] = int(inv.uses or 0)
            self.save()
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.gdata(guild.id)
            await self._refresh_guild_invites(guild)
        self.save()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.gdata(guild.id)
        await self._refresh_guild_invites(guild)
        self.save()

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if not invite.guild:
            return
        cache = self.invite_cache.setdefault(invite.guild.id, {})
        cache[invite.code] = int(invite.uses or 0)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot or not member.guild:
            return

        guild = member.guild
        g = self.gdata(guild.id)
        old_counts = self.invite_cache.get(guild.id, {})

        try:
            current_invites = await guild.invites()
        except Exception:
            return

        used_invite = None
        new_cache: dict[str, int] = {}
        for inv in current_invites:
            uses = int(inv.uses or 0)
            new_cache[inv.code] = uses
            prev_uses = int(old_counts.get(inv.code, 0))
            if uses > prev_uses and used_invite is None:
                used_invite = inv

        self.invite_cache[guild.id] = new_cache

        if used_invite:
            inviter_id = None
            link_info = g["invite_links"].get(used_invite.code)
            if link_info and link_info.get("inviter_id"):
                inviter_id = int(link_info["inviter_id"])
                link_info["uses"] = int(used_invite.uses or 0)
            elif used_invite.inviter and not used_invite.inviter.bot:
                inviter_id = int(used_invite.inviter.id)

            if inviter_id:
                iid_str = str(inviter_id)
                g["invite_counts"][iid_str] = int(g["invite_counts"].get(iid_str, 0)) + 1
                self.save()

    @commands.Cog.listener()
    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, (commands.MissingPermissions, commands.BotMissingPermissions)):
            await send_card(
                ctx,
                title="Process Denied !",
                body="❌ You don't have permission to use this command!",
                color=0xED4245,
                thumb_url=get_thumb_url(target=ctx.author, bot=self.bot, guild=ctx.guild),
                delete_after=6,
            )

    # --- Counting Commands ---
    @commands.command(name="setcountchannel", help="Set the channel for the counting game.")
    @commands.has_permissions(manage_channels=True)
    async def set_count_channel(self, ctx, channel: discord.TextChannel = None):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        target_ch = channel or ctx.channel
        g = self.gdata(ctx.guild.id)
        g["counting"]["channel_id"] = target_ch.id
        self.save()

        await send_card(
            ctx,
            title="Counting Channel Set",
            body=f"▸ **Channel** : {target_ch.mention}\n▸ **Current Count** : `{g['counting']['current_count']}`",
            color=0x2ECC71,
            thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            delete_after=4,
        )

    @commands.command(name="count", hidden=True, help="Start or configure the counting game.")
    @commands.has_permissions(manage_channels=True)
    async def count_command(self, ctx, number: int, channel: discord.TextChannel = None, emoji: str = "✅"):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        target_ch = channel or ctx.channel
        g = self.gdata(ctx.guild.id)
        g["counting"]["current_count"] = int(number)
        g["counting"]["channel_id"] = target_ch.id
        g["counting"]["success_emoji"] = emoji.strip()
        g["counting"]["last_user_id"] = None
        self.save()

        await send_card(
            ctx,
            title="Counting Game Started !",
            body=f"▸ **Start Number** : `{number}`\n▸ **Channel** : {target_ch.mention}\n▸ **Emoji** : {emoji.strip()}",
            color=0x2ECC71,
            thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            delete_after=4,
        )

    async def _current_prefixes(self, message: discord.Message) -> tuple[str, ...]:
        custom = load_prefixes().get(str(message.guild.id), "&")
        prefixes = {custom, "&"}
        if callable(self.bot.command_prefix):
            try:
                res = self.bot.command_prefix(self.bot, message)
                if asyncio.iscoroutine(res):
                    res = await res
                if isinstance(res, str):
                    prefixes.add(res)
                elif isinstance(res, (list, tuple, set)):
                    for p in res:
                        if isinstance(p, str):
                            prefixes.add(p)
            except Exception:
                pass
        elif isinstance(self.bot.command_prefix, str):
            prefixes.add(self.bot.command_prefix)
        return tuple(p for p in prefixes if p)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        author_id = message.author.id
        g = self.gdata(guild_id)
        counting = g["counting"]
        count_ch_id = counting.get("channel_id")

        if count_ch_id and message.channel.id == int(count_ch_id):
            prefixes = await self._current_prefixes(message)
            if prefixes and message.content.startswith(prefixes):
                return

            try:
                number = int(message.content.strip())
            except ValueError:
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass
                return

            current_num = int(counting.get("current_count", 1))
            last_uid = counting.get("last_user_id")
            emoji = counting.get("success_emoji", "✅")

            if last_uid is not None and int(last_uid) == author_id:
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass
                err_msg = await send_card(
                    message.channel,
                    title="Counting Error",
                    body=f"❌ {message.author.mention}, you cannot count twice in a row!",
                    color=0xED4245,
                    thumb_url=get_thumb_url(target=message.author, bot=self.bot, guild=message.guild),
                )
                await asyncio.sleep(4)
                try:
                    await err_msg.delete()
                except discord.HTTPException:
                    pass
                return

            if number != current_num:
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass
                err_msg = await send_card(
                    message.channel,
                    title="Counting Error",
                    body=f"❌ {message.author.mention}, wrong number! Next number is `{current_num}`.",
                    color=0xED4245,
                    thumb_url=get_thumb_url(target=message.author, bot=self.bot, guild=message.guild),
                )
                await asyncio.sleep(4)
                try:
                    await err_msg.delete()
                except discord.HTTPException:
                    pass
                return

            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                pass

            counting["current_count"] = current_num + 1
            counting["last_user_id"] = author_id
            self._record_user_message(guild_id, author_id)
            self.save()
            return

        afk_users = g["afk_users"]
        if message.mentions:
            for mention in message.mentions:
                mid_str = str(mention.id)
                if mid_str in afk_users:
                    afk_data = afk_users[mid_str]
                    afk_data.setdefault("mentions", []).append({
                        "author": message.author.name,
                        "channel_id": message.channel.id,
                        "time": datetime.datetime.now(datetime.timezone.utc).timestamp(),
                        "content": message.content[:200],
                    })
                    if len(afk_data["mentions"]) > 10:
                        afk_data["mentions"].pop(0)

                    duration = int(
                        datetime.datetime.now(datetime.timezone.utc).timestamp()
                        - float(afk_data.get("time", 0))
                    )
                    time_ago = format_time(duration)
                    body = (
                        f"▸ **User** : {mention.mention}\n"
                        f"▸ **Reason** : `{afk_data.get('reason', 'AFK')}`\n"
                        f"▸ **AFK Since** : `{time_ago} ago`"
                    )
                    await send_card(
                        message.channel,
                        title="User is AFK !",
                        body=body,
                        color=0x3498DB,
                        thumb_url=get_thumb_url(target=mention, bot=self.bot, guild=message.guild),
                        delete_after=10,
                        allowed_mentions=discord.AllowedMentions(users=False),
                    )
            self.save()

        aid_str = str(author_id)
        prefixes = await self._current_prefixes(message)
        is_afk_cmd = any(
            message.content.lower().startswith(f"{p.lower()}afk") for p in prefixes
        )
        if aid_str in afk_users and not is_afk_cmd:
            afk_data = afk_users.pop(aid_str)
            mentions_list = afk_data.get("mentions", [])
            desc = f"Welcome back {message.author.mention}, your AFK status has been removed!\n\n"
            if mentions_list:
                desc += "▸ **Mentions While Away** :\n"
                for m in mentions_list:
                    ts = float(m.get("time", 0))
                    t_str = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%H:%M:%S")
                    ch = message.guild.get_channel(int(m.get("channel_id", 0)))
                    ch_label = ch.mention if ch else f"`#{m.get('channel_id')}`"
                    desc += f"• **{m.get('author', 'User')}** in {ch_label} at `{t_str}`: {m.get('content', '')}\n"
            else:
                desc += "▸ **Mentions While Away** : `None`"

            self.save()
            try:
                await send_card(
                    message.channel,
                    title="Welcome Back !",
                    body=desc,
                    color=0x2ECC71,
                    thumb_url=get_thumb_url(target=message.author, bot=self.bot, guild=message.guild),
                    delete_after=15,
                    allowed_mentions=discord.AllowedMentions(users=True),
                )
            except discord.HTTPException:
                pass

        self._record_user_message(guild_id, author_id)
        self.save()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot or not member.guild:
            return

        g = self.gdata(member.guild.id)
        uid = str(member.id)
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()

        if before.channel is None and after.channel is not None:
            g["vc_joins"][uid] = now
            self.save()

        elif before.channel is not None and after.channel is None:
            joined_at = g["vc_joins"].pop(uid, None)
            if joined_at is not None:
                duration = max(0, int(now - float(joined_at)))
                g["voice_time_seconds"][uid] = int(g["voice_time_seconds"].get(uid, 0)) + duration
            self.save()

        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            if uid not in g["vc_joins"]:
                g["vc_joins"][uid] = now
                self.save()

    # --- Normal / Public Commands ---
    @commands.command(name="afk", help="Set your AFK status with an optional reason.")
    async def afk_command(self, ctx, *, reason: str = "AFK"):
        g = self.gdata(ctx.guild.id)
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        g["afk_users"][str(ctx.author.id)] = {
            "reason": reason,
            "time": now,
            "mentions": [],
        }
        self.save()

        body = (
            f"▸ **User** : {ctx.author.mention}\n"
            f"▸ **Reason** : `{reason}`\n"
            f"▸ **AFK Since** : `0s ago`"
        )
        await send_card(
            ctx,
            title="User is AFK !",
            body=body,
            color=0x3498DB,
            thumb_url=get_thumb_url(target=ctx.author, bot=self.bot, guild=ctx.guild),
        )

    @commands.command(name="msg", help="Check how many messages a member has sent.")
    async def msg_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        g = self.gdata(ctx.guild.id)
        uid = str(target.id)
        total_msgs = int(g["message_counts"].get(uid, 0))
        today_msgs = int(g["daily_messages"].get(today_key(), {}).get(uid, 0))
        avg_daily = self._calc_daily_avg(g, uid, total_msgs)

        body = (
            f"▸ **User** : {target.mention}\n"
            f"▸ **Total Messages** : `{total_msgs}`\n"
            f"▸ **Today's Messages** : `{today_msgs}`\n"
            f"▸ **Avg. Daily** : `{avg_daily}`"
        )
        await send_card(
            ctx,
            title="Message Tracker",
            body=body,
            color=0x3498DB,
            thumb_url=get_thumb_url(target=target, bot=self.bot, guild=ctx.guild),
        )

    @commands.command(name="vc", help="Check how much time a member has spent in voice channels.")
    async def vc_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        g = self.gdata(ctx.guild.id)
        uid = str(target.id)
        total_secs = int(g["voice_time_seconds"].get(uid, 0))

        joined_at = g["vc_joins"].get(uid)
        if joined_at is not None and target.voice and target.voice.channel:
            now = datetime.datetime.now(datetime.timezone.utc).timestamp()
            total_secs += max(0, int(now - float(joined_at)))

        body = (
            f"▸ **User** : {target.mention}\n"
            f"▸ **Voice Time** : `{format_time(total_secs)}`"
        )
        await send_card(
            ctx,
            title="Voice Tracker",
            body=body,
            color=0x2ECC71,
            thumb_url=get_thumb_url(target=target, bot=self.bot, guild=ctx.guild),
        )

    @commands.command(name="inv", help="Check how many members a user has invited.")
    async def inv_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        g = self.gdata(ctx.guild.id)
        invites = int(g["invite_counts"].get(str(target.id), 0))

        body = (
            f"▸ **User** : {target.mention}\n"
            f"▸ **Total Invites** : `{invites}`"
        )
        await send_card(
            ctx,
            title="Invite Tracker",
            body=body,
            color=0x9B59B6,
            thumb_url=get_thumb_url(target=target, bot=self.bot, guild=ctx.guild),
        )

    @commands.command(name="invite", help="Create a personal server invite link under your name.")
    @commands.has_permissions(create_instant_invite=True)
    async def create_invite(self, ctx):
        try:
            invite = await ctx.channel.create_invite(
                max_age=0,
                max_uses=0,
                unique=True,
                reason=f"Personal invite for {ctx.author} ({ctx.author.id})",
            )
            g = self.gdata(ctx.guild.id)
            g["invite_links"][invite.code] = {
                "inviter_id": ctx.author.id,
                "owner_name": ctx.author.display_name,
                "uses": int(invite.uses or 0),
            }
            cache = self.invite_cache.setdefault(ctx.guild.id, {})
            cache[invite.code] = int(invite.uses or 0)
            self.save()

            body = (
                f"▸ **Invited By** : {ctx.author.mention} (`{ctx.author.display_name}`)\n"
                f"▸ **Personal Link** : {invite.url}\n"
                f"▸ **Invite Code** : `{invite.code}`"
            )
            await send_card(
                ctx,
                title=f"{ctx.author.display_name}'s Invite Link",
                body=body,
                color=0x2ECC71,
                thumb_url=get_thumb_url(target=ctx.author, bot=self.bot, guild=ctx.guild),
            )
        except Exception as e:
            await send_card(
                ctx,
                title="Invite Error",
                body=f"❌ Could not create invite: `{e}`",
                color=0xED4245,
                thumb_url=get_thumb_url(target=ctx.author, bot=self.bot, guild=ctx.guild),
                delete_after=5,
            )

    # --- Leaderboard Commands ---
    @commands.command(name="lbmsg", help="Show message leaderboard.")
    async def lb_msg(self, ctx):
        g = self.gdata(ctx.guild.id)
        msg_map = g.get("message_counts", {})
        if not msg_map:
            return await send_card(
                ctx,
                title="Message Leaderboard",
                body="No message data recorded yet.",
                color=0x3498DB,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            )

        sorted_users = sorted(msg_map.items(), key=lambda x: int(x[1]), reverse=True)[:10]
        lines = []
        for idx, (uid, count) in enumerate(sorted_users, 1):
            user = ctx.guild.get_member(int(uid))
            name = user.mention if user else f"`User ID: {uid}`"
            lines.append(f"`#{idx}` {name} — **{int(count)}** messages")

        await send_card(
            ctx,
            title="Message Leaderboard",
            body="\n".join(lines),
            color=0x3498DB,
            thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
        )

    @commands.command(name="lbvc", help="Show voice time leaderboard.")
    async def lb_vc(self, ctx):
        g = self.gdata(ctx.guild.id)
        all_vc = {k: int(v) for k, v in g.get("voice_time_seconds", {}).items()}
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()

        for uid, start_time in g.get("vc_joins", {}).items():
            member = ctx.guild.get_member(int(uid))
            if member and member.voice and member.voice.channel:
                duration = max(0, int(now - float(start_time)))
                all_vc[uid] = int(all_vc.get(uid, 0)) + duration

        if not all_vc:
            return await send_card(
                ctx,
                title="Voice Leaderboard",
                body="No voice data recorded yet.",
                color=0x2ECC71,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            )

        sorted_users = sorted(all_vc.items(), key=lambda x: int(x[1]), reverse=True)[:10]
        lines = []
        for idx, (uid, secs) in enumerate(sorted_users, 1):
            user = ctx.guild.get_member(int(uid))
            name = user.mention if user else f"`User ID: {uid}`"
            lines.append(f"`#{idx}` {name} — **{format_time(int(secs))}**")

        await send_card(
            ctx,
            title="Voice Leaderboard",
            body="\n".join(lines),
            color=0x2ECC71,
            thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
        )

    @commands.command(name="lbinv", help="Show invite leaderboard.")
    async def lb_inv(self, ctx):
        g = self.gdata(ctx.guild.id)
        inv_map = g.get("invite_counts", {})
        if not inv_map:
            return await send_card(
                ctx,
                title="Invite Leaderboard",
                body="No invite data recorded yet.",
                color=0x9B59B6,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            )

        sorted_users = sorted(inv_map.items(), key=lambda x: int(x[1]), reverse=True)[:10]
        lines = []
        for idx, (uid, count) in enumerate(sorted_users, 1):
            user = ctx.guild.get_member(int(uid))
            name = user.mention if user else f"`User ID: {uid}`"
            lines.append(f"`#{idx}` {name} — **{int(count)}** invites")

        await send_card(
            ctx,
            title="Invite Leaderboard",
            body="\n".join(lines),
            color=0x9B59B6,
            thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
        )

    # --- Admin / Management Commands ---
    @commands.command(name="resetmsg", help="Reset message stats for a user or all users.")
    @commands.has_permissions(administrator=True)
    async def reset_msg(self, ctx, target: discord.Member = None):
        g = self.gdata(ctx.guild.id)
        if target:
            g["message_counts"][str(target.id)] = 0
            self.save()
            await send_card(
                ctx,
                title="Reset Success",
                body=f"▸ **User** : {target.mention}\n▸ **Stat** : `Message stats reset`",
                color=0x2ECC71,
                thumb_url=get_thumb_url(target=target, bot=self.bot, guild=ctx.guild),
            )
        else:
            g["message_counts"].clear()
            g["daily_messages"].clear()
            self.save()
            await send_card(
                ctx,
                title="Reset Success",
                body="▸ **Scope** : `All members`\n▸ **Stat** : `Message stats reset`",
                color=0x2ECC71,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            )

    @commands.command(name="resetvc", help="Reset voice stats for a user or all users.")
    @commands.has_permissions(administrator=True)
    async def reset_vc(self, ctx, target: discord.Member = None):
        g = self.gdata(ctx.guild.id)
        if target:
            uid = str(target.id)
            g["voice_time_seconds"][uid] = 0
            if uid in g["vc_joins"]:
                g["vc_joins"][uid] = datetime.datetime.now(datetime.timezone.utc).timestamp()
            self.save()
            await send_card(
                ctx,
                title="Reset Success",
                body=f"▸ **User** : {target.mention}\n▸ **Stat** : `Voice stats reset`",
                color=0x2ECC71,
                thumb_url=get_thumb_url(target=target, bot=self.bot, guild=ctx.guild),
            )
        else:
            g["voice_time_seconds"].clear()
            g["vc_joins"].clear()
            self.save()
            await send_card(
                ctx,
                title="Reset Success",
                body="▸ **Scope** : `All members`\n▸ **Stat** : `Voice stats reset`",
                color=0x2ECC71,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            )

    @commands.command(name="resetinv", help="Reset invite stats for a user or all users.")
    @commands.has_permissions(administrator=True)
    async def reset_inv(self, ctx, target: discord.Member = None):
        g = self.gdata(ctx.guild.id)
        if target:
            g["invite_counts"][str(target.id)] = 0
            self.save()
            await send_card(
                ctx,
                title="Reset Success",
                body=f"▸ **User** : {target.mention}\n▸ **Stat** : `Invite stats reset`",
                color=0x2ECC71,
                thumb_url=get_thumb_url(target=target, bot=self.bot, guild=ctx.guild),
            )
        else:
            g["invite_counts"].clear()
            self.save()
            await send_card(
                ctx,
                title="Reset Success",
                body="▸ **Scope** : `All members`\n▸ **Stat** : `Invite stats reset`",
                color=0x2ECC71,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            )

    @commands.command(name="say", help="Make the bot say something.")
    @commands.has_permissions(manage_messages=True)
    async def say_command(self, ctx, *, message: str):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(message)

    @commands.command(name="reply", help="Make the bot reply to a message.")
    @commands.has_permissions(manage_messages=True)
    async def reply_command(self, ctx, message_id: int, *, message: str):
        try:
            await ctx.message.delete()
            target_msg = await ctx.channel.fetch_message(message_id)
            await target_msg.reply(message)
        except Exception as e:
            await send_card(
                ctx,
                title="Reply Error",
                body=f"❌ Error replying: `{e}`",
                color=0xED4245,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
                delete_after=5,
            )

    @commands.command(name="setprefix", help="Changes the bot prefix for this server.")
    @commands.has_permissions(manage_guild=True)
    async def set_prefix(self, ctx, new_prefix: str):
        prefixes = load_prefixes()
        prefixes[str(ctx.guild.id)] = new_prefix
        save_prefixes(prefixes)

        body = (
            f"▸ **New Prefix** : `{new_prefix}`\n"
            f"▸ **Example** : `{new_prefix}help`"
        )
        await send_card(
            ctx,
            title="Prefix Updated",
            body=body,
            color=0x2ECC71,
            thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
        )


class Clone(commands.Cog, name="Clone"):
    """Explore all commands related to Clone."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clone", help="Clone custom emojis or stickers by replying to a message.")
    @commands.has_permissions(manage_emojis=True)
    async def clone_command(self, ctx):
        if not ctx.message.reference:
            return await send_card(
                ctx,
                title="Clone Error",
                body="❌ Please reply to a message containing a custom emoji or sticker!",
                color=0xED4245,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            )

        try:
            referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except Exception:
            return await send_card(
                ctx,
                title="Clone Error",
                body="❌ Could not fetch the referenced message.",
                color=0xED4245,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            )

        cloned_count = 0
        async with aiohttp.ClientSession() as session:
            emoji_matches = re.findall(r"<(a?):([a-zA-Z0-9_]+):([0-9]+)>", referenced_msg.content or "")

            for animated, name, emoji_id in emoji_matches:
                extension = "gif" if animated == "a" else "png"
                url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}"
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            await ctx.guild.create_custom_emoji(
                                name=name,
                                image=image_bytes,
                                reason=f"Cloned by {ctx.author}",
                            )
                            cloned_count += 1
                except Exception:
                    pass

            if referenced_msg.stickers:
                for sticker in referenced_msg.stickers:
                    if getattr(sticker, "format", None) and sticker.format.name == "lottie":
                        continue
                    try:
                        async with session.get(sticker.url) as resp:
                            if resp.status == 200:
                                image_bytes = await resp.read()
                                file = discord.File(io.BytesIO(image_bytes), filename=f"{sticker.name}.png")
                                await ctx.guild.create_sticker(
                                    name=sticker.name,
                                    description="Cloned sticker",
                                    emoji="✨",
                                    file=file,
                                    reason=f"Cloned by {ctx.author}",
                                )
                                cloned_count += 1
                    except Exception:
                        pass

        if cloned_count > 0:
            await send_card(
                ctx,
                title="Successfully Cloned !",
                body=f"▸ **Cloned Items** : `{cloned_count}`\n▸ **Server** : `{SERVER_BRAND}`",
                color=0x2ECC71,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            )
        else:
            await send_card(
                ctx,
                title="Clone Error",
                body="❌ No valid custom emojis or stickers found in that replied message!",
                color=0xED4245,
                thumb_url=get_thumb_url(bot=self.bot, guild=ctx.guild),
            )


async def setup(bot):
    await bot.add_cog(Utility(bot))
    await bot.add_cog(Clone(bot))
