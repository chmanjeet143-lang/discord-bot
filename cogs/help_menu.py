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

HOME_DESCRIPTION = (
    "Experience the ultimate Discord bot designed for seamless "
    "management and community engagement."
)

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

HAS_COMPONENTS_V2 = (
    hasattr(discord.ui, "LayoutView")
    and hasattr(discord.ui, "Container")
    and hasattr(discord.ui, "Section")
    and hasattr(discord.ui, "MediaGallery")
)


def get_bot_dp(bot, guild=None) -> str:
    """Side thumbnail ke liye bot ki DP (avatar) return karta hai."""
    if getattr(bot, "user", None) and bot.user.display_avatar:
        return bot.user.display_avatar.url
    if guild and guild.icon:
        return guild.icon.url
    return DEFAULT_AVATAR


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
    """Sabhi public commands aur subcommands count karta hai."""
    return sum(1 for cmd in bot.walk_commands() if not cmd.hidden)


def get_active_cogs(bot) -> list[str]:
    """Help cog ke alawa active cogs ki sorted list return karta hai."""
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
    return CATEGORY_DESCRIPTIONS.get(
        cog_name.lower(),
        f"Dedicated commands and tools for the **{display_name}** module.",
    )


def get_command_description(cmd) -> str:
    if cmd.qualified_name.lower() in COMMAND_DESCRIPTIONS:
        return COMMAND_DESCRIPTIONS[cmd.qualified_name.lower()]
    if cmd.name.lower() in COMMAND_DESCRIPTIONS:
        return COMMAND_DESCRIPTIONS[cmd.name.lower()]
    return cmd.short_doc or cmd.help or "No description provided."


def build_select_options(bot) -> list[discord.SelectOption]:
    options = [
        discord.SelectOption(
            label="Home",
            value="__home__",
            description="Return to the main Love heaven help overview.",
            emoji="🏠",
        )
    ]
    for cog_name in get_active_cogs(bot):
        display_name = "Support Tickets" if cog_name.lower() == "supporttickets" else cog_name
        emoji = EMOJI_MAP.get(cog_name.lower(), "🔹")
        cat_desc = get_category_description(cog_name, display_name)
        options.append(
            discord.SelectOption(
                label=f"{display_name} Commands",
                value=cog_name,
                description=cat_desc[:100],
                emoji=emoji,
            )
        )
    return options[:25]


def get_home_body_text(bot, prefix: str) -> str:
    commands_count = count_bot_commands(bot)
    modules_count = len(get_active_cogs(bot))
    return (
        f"## Love heaven help\n"
        f"{HOME_DESCRIPTION}\n\n"
        f"**Prefix** `{prefix}`\n"
        f"**Commands** `{commands_count:,}`\n"
        f"**Modules** `{modules_count}`"
    )


def get_category_body_text(bot, cog_name: str, prefix: str) -> str:
    cog = bot.get_cog(cog_name)
    display_name = "Support Tickets" if cog_name.lower() == "supporttickets" else cog_name
    if not cog:
        return f"## Love heaven help\n❌ This category could not be found."

    cat_desc = get_category_description(cog_name, display_name)
    lines = []
    for cmd in cog.get_commands():
        if cmd.hidden:
            continue
        desc = get_command_description(cmd)
        if isinstance(cmd, commands.Group):
            sub_cmds = [sub.name for sub in cmd.commands if not sub.hidden]
            sub_str = f" (Subcommands: {', '.join(sub_cmds)})" if sub_cmds else ""
            lines.append(f"• `{prefix}{cmd.name}`{sub_str} — *{desc}*")
        else:
            lines.append(f"• `{prefix}{cmd.name}` — *{desc}*")

    cmds_block = "\n".join(lines) if lines else "No public commands available in this category."
    return (
        f"## Love heaven help\n"
        f"**{display_name} Commands**\n"
        f"{cat_desc}\n\n"
        f"{cmds_block}"
    )


if HAS_COMPONENTS_V2:
    class V2HelpDropdown(discord.ui.Select):
        def __init__(self, parent_view, bot, prefix: str):
            self.parent_view = parent_view
            self.bot = bot
            self.prefix = prefix
            super().__init__(
                placeholder="Home",
                min_values=1,
                max_values=1,
                options=build_select_options(bot),
            )

        async def callback(self, interaction: discord.Interaction):
            self.parent_view.selected_value = self.values[0]
            self.parent_view.rebuild(interaction.guild)
            await interaction.response.edit_message(view=self.parent_view)

    class LoveHeavenV2View(discord.ui.LayoutView):
        def __init__(self, bot, guild, prefix: str, selected_value: str = "__home__"):
            super().__init__(timeout=180)
            self.bot = bot
            self.prefix = prefix
            self.selected_value = selected_value
            self.message = None
            self.rebuild(guild)

        def rebuild(self, guild):
            self.clear_items()
            dp_url = get_bot_dp(self.bot, guild)

            if self.selected_value == "__home__":
                header_text = get_home_body_text(self.bot, self.prefix)
            else:
                header_text = get_category_body_text(self.bot, self.selected_value, self.prefix)

            gallery_items = []
            if IMAGE_URL:
                gallery_items.append(discord.MediaGalleryItem(media=IMAGE_URL))

            container_children = []
            if gallery_items:
                container_children.append(discord.ui.MediaGallery(*gallery_items))

            # Bot DP side mein + bada Love heaven help heading aur stats
            container_children.append(
                discord.ui.Section(
                    discord.ui.TextDisplay(header_text),
                    accessory=discord.ui.Thumbnail(media=dp_url),
                )
            )
            container_children.append(discord.ui.Separator())

            # Embed/Container ke andar Home dropdown
            dropdown = V2HelpDropdown(self, self.bot, self.prefix)
            container_children.append(discord.ui.ActionRow(dropdown))

            # Sabse last mein help command details line + credit
            footer_line = (
                f"Use `{self.prefix}help (command)` for details on a specific command\n"
                f"-# {BOT_CREDIT}"
            )
            container_children.append(discord.ui.TextDisplay(footer_line))

            container = discord.ui.Container(*container_children, accent_color=ACCENT_COLOR)
            self.add_item(container)

        async def on_timeout(self):
            for child in self.walk_children():
                if hasattr(child, "disabled"):
                    child.disabled = True
            if self.message:
                try:
                    await self.message.edit(view=self)
                except Exception:
                    pass


# Fallback Embed View (agar discord.py 2.5 se purana ho)
class FallbackDropdown(discord.ui.Select):
    def __init__(self, bot, guild, prefix: str):
        self.bot = bot
        self.guild = guild
        self.prefix = prefix
        super().__init__(
            placeholder="Home",
            min_values=1,
            max_values=1,
            options=build_select_options(bot),
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == "__home__":
            desc = get_home_body_text(self.bot, self.prefix)
        else:
            desc = get_category_body_text(self.bot, selected, self.prefix)

        embed = discord.Embed(description=desc, color=ACCENT_COLOR)
        if IMAGE_URL:
            embed.set_image(url=IMAGE_URL)
        embed.set_thumbnail(url=get_bot_dp(self.bot, interaction.guild))
        embed.set_footer(
            text=f"Use {self.prefix}help (command) for details on a specific command • {BOT_CREDIT}"
        )
        await interaction.response.edit_message(embed=embed, view=self.view)


class FallbackHelpView(discord.ui.View):
    def __init__(self, bot, guild, prefix: str):
        super().__init__(timeout=180)
        self.message = None
        self.add_item(FallbackDropdown(bot, guild, prefix))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


def build_command_detail_embed(bot, guild, command_obj, prefix: str) -> discord.Embed:
    aliases = (
        ", ".join(f"`{prefix}{a}`" for a in command_obj.aliases)
        if getattr(command_obj, "aliases", None)
        else "None"
    )
    usage = f"`{prefix}{command_obj.qualified_name} {command_obj.signature}`.strip()"
    desc = get_command_description(command_obj)

    lines = [
        "## Love heaven help",
        f"**Command:** `{prefix}{command_obj.qualified_name}`",
        f"**Description:** {desc}",
        f"**Usage:** {usage}",
        f"**Aliases:** {aliases}",
    ]
    if isinstance(command_obj, commands.Group):
        sub_names = [s.name for s in command_obj.commands if not s.hidden]
        if sub_names:
            lines.append(f"**Subcommands:** {', '.join(f'`{n}`' for n in sub_names)}")

    embed = discord.Embed(description="\n".join(lines), color=ACCENT_COLOR)
    if IMAGE_URL:
        embed.set_image(url=IMAGE_URL)
    embed.set_thumbnail(url=get_bot_dp(bot, guild))
    embed.set_footer(
        text=f"Use {prefix}help (command) for details on a specific command • {BOT_CREDIT}"
    )
    return embed


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
                embed = build_command_detail_embed(self.bot, ctx.guild, target_cmd, prefix)
                return await ctx.send(embed=embed)

        if HAS_COMPONENTS_V2:
            view = LoveHeavenV2View(self.bot, ctx.guild, prefix)
            message = await ctx.send(view=view)
            view.message = message
        else:
            desc = get_home_body_text(self.bot, prefix)
            embed = discord.Embed(description=desc, color=ACCENT_COLOR)
            if IMAGE_URL:
                embed.set_image(url=IMAGE_URL)
            embed.set_thumbnail(url=get_bot_dp(self.bot, ctx.guild))
            embed.set_footer(
                text=f"Use {prefix}help (command) for details on a specific command • {BOT_CREDIT}"
            )
            view = FallbackHelpView(self.bot, ctx.guild, prefix)
            message = await ctx.send(embed=embed, view=view)
            view.message = message


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
