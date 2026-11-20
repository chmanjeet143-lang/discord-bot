import discord
from discord.ext import commands

IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1532422031650455655/"
    "1573473889915502682/IMG_3099.png"
    "?ex=6b022341&is=6b00d1c1&hm=30f2f09afc213ed06927a0d470e0c00f59cddbe2158d58632a47cd1e3f59f422&"
)
DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"
BOT_CREDIT = "Bot Made By : Zeus"
ACCENT_COLOR = 0x3498DB

# Home embed ke liye alag description
HOME_DESCRIPTION = (
    "Welcome to **Love heaven help** — your server's complete command hub "
    "for smooth moderation, automated systems, and active community engagement."
)

# Har category/module ke liye alag description (keys lowercase mein rakhein)
CATEGORY_DESCRIPTIONS = {
    "automod": "Automated protection rules to filter spam, links, and unwanted chat activity.",
    "boost": "Server boost alerts, milestones, and perk management tools.",
    "bump": "Reminder and bump utilities to keep your server visible and growing.",
    "clone": "Channel and structure cloning tools for fast server setup.",
    "giveaway": "Create, manage, and reroll giveaways for your community.",
    "information": "Server stats, user info, bot metrics, and lookup commands.",
    "jail": "Isolate rule-breakers safely and restore their access cleanly.",
    "leveling": "XP tracking, rank cards, and activity reward controls.",
    "moderation": "Ban, kick, mute, warn, and day-to-day staff moderation commands.",
    "supporttickets": "Ticket creation, panel setup, and support workflow commands.",
    "tickets": "Ticket creation, panel setup, and support workflow commands.",
    "utility": "Everyday helper tools, configuration options, and quick utilities.",
    "welcome1": "First welcome module for greeting new members when they join.",
    "welcome2": "Secondary welcome module with custom join messages and styling.",
    "welcome": "Greeting messages and onboarding commands for new members.",
}

# Specific commands ke liye alag description (agar command docstring khali ho to yahan se lega)
COMMAND_DESCRIPTIONS = {
    "help": "Shows the interactive help menu or details for a specific command.",
}

EMOJI_MAP = {
    "automod": "🤖",
    "boost": "🚀",
    "bump": "📢",
    "clone": "📋",
    "giveaway": "🎉",
    "information": "📊",
    "jail": "⛓️",
    "leveling": "⭐",
    "moderation": "🛡️",
    "supporttickets": "🎫",
    "tickets": "🎫",
    "utility": "⚙️",
    "welcome1": "👋",
    "welcome2": "✨",
    "welcome": "💌",
}


def get_current_prefix(bot, guild=None) -> str:
    """Bot ka current active prefix nikalta hai."""
    prefix = bot.command_prefix
    if callable(prefix):
        try:
            class _DummyMsg:
                def __init__(self, g, b):
                    self.guild = g
                    self._state = getattr(b, "_connection", None)
                    self.author = getattr(b, "user", None)
                    self.content = ""

            res = prefix(bot, _DummyMsg(guild, bot))
            if isinstance(res, (list, tuple)) and res:
                return str(res[0])
            if isinstance(res, str) and res:
                return res
        except Exception:
            pass
        return ","

    if isinstance(prefix, (list, tuple)) and prefix:
        return str(prefix[0])
    if isinstance(prefix, str) and prefix:
        return prefix
    return ","


def count_bot_commands(bot) -> int:
    """Sabhi non-hidden commands aur subcommands count karta hai."""
    return sum(1 for cmd in bot.walk_commands() if not cmd.hidden)


def get_active_cogs(bot) -> list[str]:
    """Help cog ke alawa un active cogs ki list deta hai jinmein kam se kam 1 visible command ho."""
    cogs = [
        cog_name
        for cog_name in bot.cogs
        if cog_name.lower() not in ["helpcog", "help"]
    ]
    sorted_cogs = sorted(cogs, key=lambda name: name.lower())
    active = []
    for cog_name in sorted_cogs:
        cog = bot.get_cog(cog_name)
        if cog and any(not cmd.hidden for cmd in cog.get_commands()):
            active.append(cog_name)
    return active


def get_category_description(cog_name: str, display_name: str) -> str:
    """Category ke liye alag description return karta hai."""
    custom = CATEGORY_DESCRIPTIONS.get(cog_name.lower())
    if custom:
        return custom
    return f"Dedicated commands and tools for the **{display_name}** module."


def get_command_description(cmd) -> str:
    """Command ke liye custom ya docstring description return karta hai."""
    if cmd.qualified_name.lower() in COMMAND_DESCRIPTIONS:
        return COMMAND_DESCRIPTIONS[cmd.qualified_name.lower()]
    if cmd.name.lower() in COMMAND_DESCRIPTIONS:
        return COMMAND_DESCRIPTIONS[cmd.name.lower()]
    return cmd.short_doc or cmd.help or "No description provided."


def apply_common_visuals(embed: discord.Embed, guild, prefix: str, include_banner: bool = True):
    """Thumbnail, banner image, aur footer apply karta hai."""
    thumb = IMAGE_URL or (guild.icon.url if guild and guild.icon else DEFAULT_AVATAR)
    embed.set_thumbnail(url=thumb)
    if include_banner and IMAGE_URL:
        embed.set_image(url=IMAGE_URL)
    embed.set_footer(
        text=f"{BOT_CREDIT} • Use {prefix}help (command) for details on a specific command"
    )
    return embed


def build_home_embed(bot, guild, prefix: str) -> discord.Embed:
    """Love heaven help home embed banata hai."""
    commands_count = count_bot_commands(bot)
    modules_count = len(get_active_cogs(bot))

    embed = discord.Embed(
        title="Love heaven help",
        description=(
            f"{HOME_DESCRIPTION}\n\n"
            f"**Prefix** `{prefix}`\n"
            f"**Commands** `{commands_count:,}`\n"
            f"**Modules** `{modules_count}`"
        ),
        color=ACCENT_COLOR,
    )
    return apply_common_visuals(embed, guild, prefix, include_banner=True)


def build_category_embed(bot, guild, cog_name: str, prefix: str) -> discord.Embed:
    """Selected module ke commands aur uski alag description dikhata hai."""
    cog = bot.get_cog(cog_name)
    display_name = "Support Tickets" if cog_name.lower() == "supporttickets" else cog_name

    if not cog:
        embed = discord.Embed(
            title="Love heaven help",
            description="❌ This category could not be found.",
            color=ACCENT_COLOR,
        )
        return apply_common_visuals(embed, guild, prefix, include_banner=False)

    cat_desc = get_category_description(cog_name, display_name)
    command_list = []

    for cmd in cog.get_commands():
        if cmd.hidden:
            continue

        desc = get_command_description(cmd)
        if isinstance(cmd, commands.Group):
            sub_cmds = [sub.name for sub in cmd.commands if not sub.hidden]
            sub_str = f" (Subcommands: {', '.join(sub_cmds)})" if sub_cmds else ""
            command_list.append(f"• `{prefix}{cmd.name}`{sub_str} — *{desc}*")
        else:
            command_list.append(f"• `{prefix}{cmd.name}` — *{desc}*")

    commands_str = (
        "\n".join(command_list)
        if command_list
        else "No public commands available in this category."
    )

    embed = discord.Embed(
        title=f"Love heaven help • {display_name}",
        description=f"{cat_desc}\n\n**Commands**\n{commands_str}",
        color=ACCENT_COLOR,
    )
    return apply_common_visuals(embed, guild, prefix, include_banner=False)


def build_command_detail_embed(guild, command_obj, prefix: str) -> discord.Embed:
    """Specific command ki detail dikhata hai."""
    aliases = (
        ", ".join(f"`{prefix}{a}`" for a in command_obj.aliases)
        if getattr(command_obj, "aliases", None)
        else "None"
    )
    usage = f"`{prefix}{command_obj.qualified_name} {command_obj.signature}`.strip()"
    desc = get_command_description(command_obj)

    lines = [
        f"**Command:** `{prefix}{command_obj.qualified_name}`",
        f"**Description:** {desc}",
        f"**Usage:** {usage}",
        f"**Aliases:** {aliases}",
    ]

    if isinstance(command_obj, commands.Group):
        sub_names = [s.name for s in command_obj.commands if not s.hidden]
        if sub_names:
            lines.append(f"**Subcommands:** {', '.join(f'`{n}`' for n in sub_names)}")

    embed = discord.Embed(
        title="Love heaven help • Command Details",
        description="\n".join(lines),
        color=ACCENT_COLOR,
    )
    return apply_common_visuals(embed, guild, prefix, include_banner=False)


class HelpDropdown(discord.ui.Select):
    def __init__(self, bot, prefix: str):
        self.bot = bot
        self.prefix = prefix

        options = [
            discord.SelectOption(
                label="Home",
                value="__home__",
                description="Return to the main Love heaven help overview.",
                emoji="🏠",
            )
        ]

        for cog_name in get_active_cogs(bot):
            display_name = (
                "Support Tickets" if cog_name.lower() == "supporttickets" else cog_name
            )
            emoji = EMOJI_MAP.get(cog_name.lower(), "🔹")
            cat_desc = get_category_description(cog_name, display_name)

            options.append(
                discord.SelectOption(
                    label=f"{display_name} Commands",
                    value=cog_name,
                    description=cat_desc[:100],  # Discord select description max 100 chars
                    emoji=emoji,
                )
            )

        super().__init__(
            placeholder="Home",
            min_values=1,
            max_values=1,
            options=options[:25],
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == "__home__":
            embed = build_home_embed(self.bot, interaction.guild, self.prefix)
        else:
            embed = build_category_embed(self.bot, interaction.guild, selected, self.prefix)

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, bot, prefix: str):
        super().__init__(timeout=180)
        self.message = None
        self.add_item(HelpDropdown(bot, prefix))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx, *, query: str | None = None):
        prefix = (
            ctx.prefix
            if isinstance(ctx.prefix, str) and ctx.prefix
            else get_current_prefix(self.bot, ctx.guild)
        )

        if query:
            target_cmd = self.bot.get_command(query.strip())
            if target_cmd and not target_cmd.hidden:
                embed = build_command_detail_embed(ctx.guild, target_cmd, prefix)
                return await ctx.send(embed=embed)

        embed = build_home_embed(self.bot, ctx.guild, prefix)
        view = HelpView(self.bot, prefix)
        message = await ctx.send(embed=embed, view=view)
        view.message = message


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
