import json
import os
import random
import discord
from discord import ui
from discord.ext import commands, tasks

CONFIG_FILE = "levels_config.json"

DEFAULT_MSG_CHANNEL_ID = 1532793451899519137
DEFAULT_VC_CHANNEL_ID = 1562969374694834256

DEFAULT_MSG_LEVEL_TEXT = (
    "✨ Level Up in Love Heaven! ✨\n"
    "{user}! You just hit Level {level} — Love Heaven chat keeps getting livelier! 🚀"
)
DEFAULT_VC_LEVEL_TEXT = (
    "🎙️ Congrats {user}! Your VC time just brought you to Level {level} — Love Heaven loves having you around! ✨"
)

IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1532422031650455655/"
    "1573473889915502682/IMG_3099.png"
    "?ex=6b022341&is=6b00d1c1&hm=30f2f09afc213ed06927a0d470e0c00f59cddbe2158d58632a47cd1e3f59f422&"
)
DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"
BOT_CREDIT = "Bot Made By : Zeus"
ACCENT_COLOR = 0x3498DB

HAS_COMPONENTS_V2 = (
    hasattr(discord.ui, "LayoutView")
    and hasattr(discord.ui, "Container")
    and hasattr(discord.ui, "Section")
    and hasattr(discord.ui, "MediaGallery")
)


def load_data() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_data(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def ensure_guild_defaults(data: dict, guild_id: str) -> dict:
    """Har guild ke liye auto-on defaults (channels + messages) ensure karta hai."""
    changed = False
    if guild_id not in data or not isinstance(data[guild_id], dict):
        data[guild_id] = {}
        changed = True

    guild_entry = data[guild_id]
    if "settings" not in guild_entry or not isinstance(guild_entry["settings"], dict):
        guild_entry["settings"] = {}
        changed = True
    if "users" not in guild_entry or not isinstance(guild_entry["users"], dict):
        guild_entry["users"] = {}
        changed = True

    settings = guild_entry["settings"]
    if "auto_on" not in settings:
        settings["auto_on"] = True
        changed = True
    if not settings.get("msg_channel"):
        settings["msg_channel"] = DEFAULT_MSG_CHANNEL_ID
        changed = True
    if not settings.get("vc_channel"):
        settings["vc_channel"] = DEFAULT_VC_CHANNEL_ID
        changed = True
    if not settings.get("msg_custom_msg"):
        settings["msg_custom_msg"] = DEFAULT_MSG_LEVEL_TEXT
        changed = True
    if not settings.get("vc_custom_msg"):
        settings["vc_custom_msg"] = DEFAULT_VC_LEVEL_TEXT
        changed = True

    if changed:
        save_data(data)
    return guild_entry


def get_bot_dp(bot, guild=None) -> str:
    if bot and getattr(bot, "user", None) and bot.user.display_avatar:
        return bot.user.display_avatar.url
    if guild and guild.icon:
        return guild.icon.url
    return DEFAULT_AVATAR


def build_level_embed(
    bot,
    guild,
    title: str = "",
    description: str = "",
    color: int = ACCENT_COLOR,
    include_banner: bool = False,
) -> discord.Embed:
    heading = f"## {title}\n" if title else ""
    embed = discord.Embed(
        description=f"{heading}{description}".strip(),
        color=color,
    )
    if include_banner and IMAGE_URL:
        embed.set_image(url=IMAGE_URL)
    embed.set_thumbnail(url=get_bot_dp(bot, guild))
    embed.set_footer(text=BOT_CREDIT)
    return embed


def build_level_v2_view(
    bot,
    guild,
    title: str,
    body: str,
    accent_color: int = ACCENT_COLOR,
    include_banner: bool = False,
) -> discord.ui.LayoutView:
    dp_url = get_bot_dp(bot, guild)
    children: list[discord.ui.Item] = []

    if include_banner and IMAGE_URL:
        children.append(discord.ui.MediaGallery(discord.MediaGalleryItem(media=IMAGE_URL)))

    heading_block = f"## {title}\n{body}".strip() if title else body
    children.append(
        discord.ui.Section(
            discord.ui.TextDisplay(heading_block),
            accessory=discord.ui.Thumbnail(media=dp_url),
        )
    )
    children.append(discord.ui.Separator())
    children.append(discord.ui.TextDisplay(f"-# {BOT_CREDIT}"))

    view = ui.LayoutView(timeout=None)
    view.add_item(discord.ui.Container(*children, accent_color=accent_color))
    return view


class Level(commands.Cog, description="Explore all commands related to Leveling and XP system."):
    """Explore all commands related to Leveling system."""

    def __init__(self, bot):
        self.bot = bot
        if not self.vc_xp_loop.is_running():
            self.vc_xp_loop.start()

    def cog_unload(self):
        self.vc_xp_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot start hote hi sabhi guilds ke liye leveling auto-on aur default channels set karta hai."""
        data = load_data()
        for guild in self.bot.guilds:
            ensure_guild_defaults(data, str(guild.id))

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        data = load_data()
        ensure_guild_defaults(data, str(guild.id))

    @commands.command(name="setmsgchannel", help="Set the channel for Message XP level-up notifications.")
    @commands.has_permissions(administrator=True)
    async def set_msg_channel(self, ctx, channel: discord.TextChannel = None):
        """Set message XP channel.
        Usage: &setmsgchannel #channel-name"""
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if not channel:
            embed = build_level_embed(
                self.bot,
                ctx.guild,
                title="⚙️ Message XP Channel",
                description="Set the channel where message level-up notifications will be sent.\n\n**Usage:**\n`&setmsgchannel #channel`",
            )
            return await ctx.send(embed=embed, delete_after=5)

        data = load_data()
        guild_entry = ensure_guild_defaults(data, str(ctx.guild.id))
        guild_entry["settings"]["msg_channel"] = channel.id
        save_data(data)

        embed = build_level_embed(
            self.bot,
            ctx.guild,
            description=f"✅ Message XP channel successfully set to {channel.mention}!",
            color=discord.Color.green().value,
        )
        await ctx.send(embed=embed, delete_after=3)

    @commands.command(name="setvcchannel", help="Set the channel for Voice Chat (VC) XP notifications.")
    @commands.has_permissions(administrator=True)
    async def set_vc_channel(self, ctx, channel: discord.TextChannel = None):
        """Set VC XP channel.
        Usage: &setvcchannel #channel-name"""
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if not channel:
            embed = build_level_embed(
                self.bot,
                ctx.guild,
                title="🎙️ VC XP Channel",
                description="Set the channel where Voice Chat level-up notifications will be sent.\n\n**Usage:**\n`&setvcchannel #channel`",
            )
            return await ctx.send(embed=embed, delete_after=5)

        data = load_data()
        guild_entry = ensure_guild_defaults(data, str(ctx.guild.id))
        guild_entry["settings"]["vc_channel"] = channel.id
        save_data(data)

        embed = build_level_embed(
            self.bot,
            ctx.guild,
            description=f"✅ VC XP channel successfully set to {channel.mention}!",
            color=discord.Color.green().value,
        )
        await ctx.send(embed=embed, delete_after=3)

    @commands.command(name="setmsglevelmsg", help="Set custom level-up announcement message for text messages.")
    @commands.has_permissions(administrator=True)
    async def set_msg_level_msg(self, ctx, *, message: str = None):
        """Set custom text level up message."""
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if not message:
            embed = build_level_embed(
                self.bot,
                ctx.guild,
                title="⚙️ Custom Message Level-Up Text",
                description="Set custom message for **Text Message** level-ups.\n\n**Variables:** `{user}`, `{level}`, `{xp}`, `{server}`\n**Usage:**\n`&setmsglevelmsg Congrats {user} for Level {level}!`",
            )
            return await ctx.send(embed=embed, delete_after=5)

        data = load_data()
        guild_entry = ensure_guild_defaults(data, str(ctx.guild.id))
        guild_entry["settings"]["msg_custom_msg"] = message
        save_data(data)

        embed = build_level_embed(
            self.bot,
            ctx.guild,
            description="✅ Text message level-up announcement updated successfully!",
            color=discord.Color.green().value,
        )
        await ctx.send(embed=embed, delete_after=3)

    @commands.command(name="setvclevelmsg", help="Set custom level-up announcement message for voice chat.")
    @commands.has_permissions(administrator=True)
    async def set_vc_level_msg(self, ctx, *, message: str = None):
        """Set custom VC level up message."""
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if not message:
            embed = build_level_embed(
                self.bot,
                ctx.guild,
                title="⚙️ Custom Voice Level-Up Text",
                description="Set custom message for **Voice Chat (VC)** level-ups.\n\n**Variables:** `{user}`, `{level}`, `{xp}`, `{server}`\n**Usage:**\n`&setvclevelmsg VC Level Up {user} to Level {level}!`",
            )
            return await ctx.send(embed=embed, delete_after=5)

        data = load_data()
        guild_entry = ensure_guild_defaults(data, str(ctx.guild.id))
        guild_entry["settings"]["vc_custom_msg"] = message
        save_data(data)

        embed = build_level_embed(
            self.bot,
            ctx.guild,
            description="✅ Voice chat level-up announcement updated successfully!",
            color=discord.Color.green().value,
        )
        await ctx.send(embed=embed, delete_after=3)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        data = load_data()
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        guild_entry = ensure_guild_defaults(data, guild_id)
        settings = guild_entry["settings"]
        if not settings.get("auto_on", True):
            return

        users = guild_entry["users"]
        if user_id not in users:
            users[user_id] = {"msg_xp": 0, "msg_level": 1, "vc_xp": 0, "vc_level": 1}

        xp_earned = random.randint(2, 4)
        user_data = users[user_id]
        user_data["msg_xp"] += xp_earned

        next_level_xp = user_data["msg_level"] * 100
        if user_data["msg_xp"] >= next_level_xp:
            user_data["msg_level"] += 1
            user_data["msg_xp"] = 0

            target_channel_id = settings.get("msg_channel") or DEFAULT_MSG_CHANNEL_ID
            target_channel = (
                message.guild.get_channel(int(target_channel_id))
                or self.bot.get_channel(int(target_channel_id))
                or message.channel
            )

            custom_msg = settings.get("msg_custom_msg") or DEFAULT_MSG_LEVEL_TEXT
            formatted_msg = custom_msg.format(
                user=message.author.mention,
                level=user_data["msg_level"],
                xp=user_data["msg_xp"],
                server=message.guild.name,
            )
            allowed = discord.AllowedMentions(users=True, roles=False, everyone=False)

            try:
                if HAS_COMPONENTS_V2:
                    view = build_level_v2_view(
                        self.bot,
                        message.guild,
                        title="Love heaven | Chat Level Up",
                        body=formatted_msg,
                        accent_color=0xF1C40F,
                        include_banner=False,
                    )
                    await target_channel.send(view=view, allowed_mentions=allowed)
                else:
                    embed = build_level_embed(
                        self.bot,
                        message.guild,
                        title="Love heaven | Chat Level Up",
                        description=formatted_msg,
                        color=0xF1C40F,
                    )
                    await target_channel.send(
                        content=message.author.mention,
                        embed=embed,
                        allowed_mentions=allowed,
                    )
            except Exception:
                pass

        save_data(data)

    @tasks.loop(minutes=1)
    async def vc_xp_loop(self):
        data = load_data()
        changed = False

        # Sabhi connected guilds ke liye auto-on ensure karein
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            guild_entry = ensure_guild_defaults(data, guild_id)
            settings = guild_entry["settings"]
            if not settings.get("auto_on", True):
                continue

            users_data = guild_entry["users"]

            for vc in guild.voice_channels:
                active_members = [m for m in vc.members if not m.bot and not m.voice.self_deaf]
                if not active_members:
                    continue

                for member in active_members:
                    user_id = str(member.id)
                    if user_id not in users_data:
                        users_data[user_id] = {"msg_xp": 0, "msg_level": 1, "vc_xp": 0, "vc_level": 1}

                    vc_earned = 4
                    u_info = users_data[user_id]
                    u_info["vc_xp"] += vc_earned
                    changed = True

                    next_vc_xp = u_info["vc_level"] * 100
                    if u_info["vc_xp"] >= next_vc_xp:
                        u_info["vc_level"] += 1
                        u_info["vc_xp"] = 0

                        target_channel_id = settings.get("vc_channel") or DEFAULT_VC_CHANNEL_ID
                        target_channel = (
                            guild.get_channel(int(target_channel_id))
                            or self.bot.get_channel(int(target_channel_id))
                        )

                        if target_channel:
                            custom_msg = settings.get("vc_custom_msg") or DEFAULT_VC_LEVEL_TEXT
                            formatted_msg = custom_msg.format(
                                user=member.mention,
                                level=u_info["vc_level"],
                                xp=u_info["vc_xp"],
                                server=guild.name,
                            )
                            allowed = discord.AllowedMentions(users=True, roles=False, everyone=False)

                            try:
                                if HAS_COMPONENTS_V2:
                                    view = build_level_v2_view(
                                        self.bot,
                                        guild,
                                        title="Love heaven | VC Level Up",
                                        body=formatted_msg,
                                        accent_color=0x9B59B6,
                                        include_banner=False,
                                    )
                                    await target_channel.send(view=view, allowed_mentions=allowed)
                                else:
                                    embed = build_level_embed(
                                        self.bot,
                                        guild,
                                        title="Love heaven | VC Level Up",
                                        description=formatted_msg,
                                        color=0x9B59B6,
                                    )
                                    await target_channel.send(
                                        content=member.mention,
                                        embed=embed,
                                        allowed_mentions=allowed,
                                    )
                            except Exception:
                                pass

        if changed:
            save_data(data)

    @vc_xp_loop.before_loop
    async def before_vc_xp(self):
        await self.bot.wait_until_ready()

    @commands.command(name="leaderboard", help="Show the top members leaderboard.")
    async def leaderboard(self, ctx):
        """Show leaderboard.
        Usage: &leaderboard"""
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id].get("users"):
            embed = build_level_embed(
                self.bot,
                ctx.guild,
                description="❌ Is server par abhi koi level data available nahi hai!",
                color=discord.Color.red().value,
            )
            return await ctx.send(embed=embed, delete_after=3)

        users_dict = data[guild_id]["users"]
        sorted_users = sorted(
            users_dict.items(),
            key=lambda x: (x[1].get("msg_level", 1), x[1].get("msg_xp", 0)),
            reverse=True,
        )[:10]

        desc = ""
        for i, (user_id, info) in enumerate(sorted_users, start=1):
            member = ctx.guild.get_member(int(user_id))
            name = member.mention if member else f"User ID: `{user_id}`"
            desc += (
                f"**{i}.** {name} — "
                f"Chat Lv.**{info.get('msg_level', 1)}** (`{info.get('msg_xp', 0)} XP`) • "
                f"VC Lv.**{info.get('vc_level', 1)}** (`{info.get('vc_xp', 0)} XP`)\n"
            )

        if HAS_COMPONENTS_V2:
            view = build_level_v2_view(
                self.bot,
                ctx.guild,
                title=f"🏆 Love heaven | Leaderboard",
                body=desc,
                accent_color=0xF1C40F,
                include_banner=True,
            )
            await ctx.send(view=view)
        else:
            embed = build_level_embed(
                self.bot,
                ctx.guild,
                title="🏆 Love heaven | Leaderboard",
                description=desc,
                color=0xF1C40F,
                include_banner=True,
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Level(bot))
