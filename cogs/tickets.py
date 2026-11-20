import asyncio
import discord
from discord import ui
from discord.ext import commands

IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1532422031650455655/"
    "1573473889915502682/IMG_3099.png"
    "?ex=6b022341&is=6b00d1c1&hm=30f2f09afc213ed06927a0d470e0c00f59cddbe2158d58632a47cd1e3f59f422&"
)
DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"
BOT_CREDIT = "Bot Made By : Zeus"
ACCENT_COLOR = 0x3498DB
STAFF_ROLE_ID = 1558065387600617603
CATEGORY_NAME = "Staff Applications"

HAS_COMPONENTS_V2 = (
    hasattr(discord.ui, "LayoutView")
    and hasattr(discord.ui, "Container")
    and hasattr(discord.ui, "Section")
    and hasattr(discord.ui, "MediaGallery")
)


def get_bot_dp(bot, guild=None) -> str:
    """Side thumbnail ke liye bot ki DP (avatar) return karta hai."""
    if bot and getattr(bot, "user", None) and bot.user.display_avatar:
        return bot.user.display_avatar.url
    if guild and guild.icon:
        return guild.icon.url
    return DEFAULT_AVATAR


def create_embed(bot, guild, title: str = "", description: str = "", color: int = ACCENT_COLOR) -> discord.Embed:
    """Fallback / standard embed ke saath banner, bot DP aur Bot Made By : Zeus footer."""
    heading = f"## {title}\n" if title else ""
    embed = discord.Embed(
        description=f"{heading}{description}".strip(),
        color=color,
    )
    if IMAGE_URL:
        embed.set_image(url=IMAGE_URL)
    embed.set_thumbnail(url=get_bot_dp(bot, guild))
    embed.set_footer(text=BOT_CREDIT)
    return embed


def build_card_v2(
    bot,
    guild,
    title: str,
    body: str,
    action_items: list[discord.ui.Item] | None = None,
    accent_color: int = ACCENT_COLOR,
) -> discord.ui.Container:
    """Upar image, side mein bot DP, bada heading, andar action items aur last mein credit."""
    dp_url = get_bot_dp(bot, guild)
    children: list[discord.ui.Item] = []

    if IMAGE_URL:
        children.append(discord.ui.MediaGallery(discord.MediaGalleryItem(media=IMAGE_URL)))

    heading_block = f"## {title}\n{body}".strip() if title else body
    children.append(
        discord.ui.Section(
            discord.ui.TextDisplay(heading_block),
            accessory=discord.ui.Thumbnail(media=dp_url),
        )
    )
    children.append(discord.ui.Separator())

    if action_items:
        children.append(discord.ui.ActionRow(*action_items))

    children.append(discord.ui.TextDisplay(f"-# {BOT_CREDIT}"))
    return discord.ui.Container(*children, accent_color=accent_color)


async def handle_close_ticket(interaction: discord.Interaction, bot=None):
    """Ticket channel delete karne ka common handler."""
    try:
        title = "Closing Ticket"
        desc = "⚠️ This ticket channel will be deleted in 5 seconds..."
        client = bot or interaction.client
        if HAS_COMPONENTS_V2:
            msg_view = ui.LayoutView(timeout=None)
            msg_view.add_item(
                build_card_v2(
                    client,
                    interaction.guild,
                    title=title,
                    body=desc,
                    accent_color=0xED4245,
                )
            )
            await interaction.response.send_message(view=msg_view, ephemeral=True)
        else:
            embed = create_embed(
                client,
                interaction.guild,
                title=title,
                description=desc,
                color=0xED4245,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        await asyncio.sleep(5)
        if interaction.channel:
            await interaction.channel.delete()
    except Exception:
        pass


class TicketControlView(ui.View):
    def __init__(self, bot=None):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="close_staff_ticket_btn_final",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await handle_close_ticket(interaction, self.bot)


class StaffTicketOpenedV2View(ui.LayoutView):
    """Staff ticket channel ke andar dikhne wala card + Close Ticket button."""

    def __init__(self, bot, guild, body: str):
        super().__init__(timeout=None)
        close_btn = ui.Button(
            label="Close Ticket",
            style=discord.ButtonStyle.danger,
            emoji="🔒",
            custom_id="close_staff_ticket_btn_final",
        )

        async def _on_close(interaction: discord.Interaction):
            await handle_close_ticket(interaction, bot)

        close_btn.callback = _on_close
        self.add_item(
            build_card_v2(
                bot,
                guild,
                title="📝 Staff Application Form",
                body=body,
                action_items=[close_btn],
            )
        )


async def handle_open_staff_ticket(interaction: discord.Interaction, bot=None):
    """Apply for Staff button click par channel create aur role tag karta hai."""
    try:
        client = bot or interaction.client
        guild = interaction.guild

        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if not category:
            category = await guild.create_category(CATEGORY_NAME)

        support_role = guild.get_role(STAFF_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_channels=True
            ),
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )

        channel_name = f"staff-ticket-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Staff Application Ticket by {interaction.user.id}",
        )

        role_mention = support_role.mention if support_role else f"<@&{STAFF_ROLE_ID}>"
        questions_body = (
            f"Thank you for applying to the staff team at **Love heaven**, {interaction.user.mention}! "
            "Our staff will contact you soon.\n\n"
            "⚠️ **Important Guidelines:**\n"
            "• Do not share any false information in your application.\n"
            "• Once the ticket is open, please be patient; our management team will review it shortly.\n\n"
            "While you wait, please share the following details to speed up the process:\n\n"
            "1. **Your Age & Timezone:**\n"
            "2. **Previous staff/moderation experience (if any):**\n"
            "3. **How active can you be on the server daily?**"
        )
        full_body = f"{interaction.user.mention} {role_mention}\n\n{questions_body}"
        allowed = discord.AllowedMentions(users=True, roles=True, everyone=False)

        if HAS_COMPONENTS_V2:
            opened_view = StaffTicketOpenedV2View(client, guild, full_body)
            await ticket_channel.send(view=opened_view, allowed_mentions=allowed)
        else:
            embed = create_embed(
                client,
                guild,
                title="📝 Staff Application Form",
                description=questions_body,
            )
            await ticket_channel.send(
                content=f"{interaction.user.mention} {role_mention}",
                embed=embed,
                view=TicketControlView(client),
                allowed_mentions=allowed,
            )

        await interaction.response.send_message(
            f"✅ Your staff application ticket has been created: {ticket_channel.mention}",
            ephemeral=True,
        )

    except Exception as e:
        try:
            await interaction.response.send_message(f"❌ Error: `{e}`", ephemeral=True)
        except Exception:
            pass


class StaffTicketButtonView(ui.View):
    def __init__(self, bot=None):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(
        label="Apply for Staff",
        style=discord.ButtonStyle.primary,
        emoji="🎫",
        custom_id="open_staff_ticket_btn_final",
    )
    async def open_staff_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await handle_open_staff_ticket(interaction, self.bot)


class StaffSetupV2View(ui.LayoutView):
    """Bahar ka clean panel — upar image, side DP, bada heading, button andar aur credit last mein."""

    def __init__(self, bot, guild, title: str, body: str):
        super().__init__(timeout=None)
        apply_btn = ui.Button(
            label="Apply for Staff",
            style=discord.ButtonStyle.primary,
            emoji="🎫",
            custom_id="open_staff_ticket_btn_final",
        )

        async def _on_apply(interaction: discord.Interaction):
            await handle_open_staff_ticket(interaction, bot)

        apply_btn.callback = _on_apply
        self.add_item(
            build_card_v2(
                bot,
                guild,
                title=title,
                body=body,
                action_items=[apply_btn],
            )
        )


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # Bot restart ke baad bhi purane panels aur close buttons kaam karein
        self.bot.add_view(StaffTicketButtonView(self.bot))
        self.bot.add_view(TicketControlView(self.bot))

    @commands.command(name="ticketsetupstaff")
    @commands.has_permissions(administrator=True)
    async def ticket_setup_staff(self, ctx):
        title = "Love heaven | Staff Recruitment"
        description = (
            "Want to join the **Love heaven** staff team and help our community grow?\n\n"
            "⚠️ **Important Guidelines:**\n"
            "• Do not share any false information in your application.\n"
            "• Once the ticket is open, please be patient; our management team will review it shortly.\n\n"
            "🎫 Click the button below to open your application ticket!"
        )

        if HAS_COMPONENTS_V2:
            view = StaffSetupV2View(self.bot, ctx.guild, title=title, body=description)
            await ctx.send(view=view)
        else:
            embed = create_embed(self.bot, ctx.guild, title=title, description=description)
            await ctx.send(embed=embed, view=StaffTicketButtonView(self.bot))


async def setup(bot):
    await bot.add_cog(Tickets(bot))
