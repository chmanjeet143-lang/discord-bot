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


class TicketControlView(ui.View):
    def __init__(self, bot=None, guild=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild = guild

    @ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="close_support_ticket_btn_final",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        try:
            title = "Closing Ticket"
            desc = "⚠️ This ticket channel will be deleted in 5 seconds..."
            if HAS_COMPONENTS_V2:
                v2_view = ui.LayoutView(timeout=None)
                v2_view.add_item(
                    build_card_v2(
                        self.bot or interaction.client,
                        interaction.guild,
                        title=title,
                        body=desc,
                        accent_color=0xED4245,
                    )
                )
                await interaction.response.send_message(view=v2_view, ephemeral=True)
            else:
                embed = create_embed(
                    self.bot or interaction.client,
                    interaction.guild,
                    title=title,
                    description=desc,
                    color=0xED4245,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

            await asyncio.sleep(5)
            await interaction.channel.delete()
        except Exception:
            pass


class TicketOpenedV2View(ui.LayoutView):
    """Ticket channel ke andar open hone par dikhne wala card + Close Ticket button."""

    def __init__(self, bot, guild, body: str):
        super().__init__(timeout=None)
        close_btn = ui.Button(
            label="Close Ticket",
            style=discord.ButtonStyle.danger,
            emoji="🔒",
            custom_id="close_support_ticket_btn_final",
        )

        async def _on_close(interaction: discord.Interaction):
            try:
                msg_view = ui.LayoutView(timeout=None)
                msg_view.add_item(
                    build_card_v2(
                        bot,
                        interaction.guild,
                        title="Closing Ticket",
                        body="⚠️ This ticket channel will be deleted in 5 seconds...",
                        accent_color=0xED4245,
                    )
                )
                await interaction.response.send_message(view=msg_view, ephemeral=True)
                await asyncio.sleep(5)
                await interaction.channel.delete()
            except Exception:
                pass

        close_btn.callback = _on_close
        self.add_item(
            build_card_v2(
                bot,
                guild,
                title="🎫 Ticket Opened",
                body=body,
                action_items=[close_btn],
            )
        )


class SupportTicketSelect(ui.Select):
    def __init__(self, bot=None):
        self.bot = bot
        options = [
            discord.SelectOption(
                label="Staff Complaint",
                description="Report or complain about a staff member.",
                emoji="⚖️",
                value="staff_complaint",
            ),
            discord.SelectOption(
                label="Promo & Sponsorship",
                description="Inquiries for promotions or partnerships.",
                emoji="🤝",
                value="promo_sponsor",
            ),
            discord.SelectOption(
                label="Giveaway Claim",
                description="Claim your won giveaway prize.",
                emoji="🎁",
                value="giveaway_claim",
            ),
        ]
        super().__init__(
            placeholder="Make a selection to open a ticket...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="support_ticket_dropdown_final",
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            bot = self.bot or interaction.client
            guild = interaction.guild
            val = self.values[0]

            if val == "staff_complaint":
                category_name = "Staff Complaints"
                role_id = 1558070324229316731
                channel_prefix = "complaint"
                auto_msg = (
                    f"Thank you for bringing this to our notice, {interaction.user.mention}. "
                    "Management will review your complaint shortly. Please share all the details and proofs below."
                )
            elif val == "promo_sponsor":
                category_name = "Promotions & Partnerships"
                role_id = 1558070509256581170
                channel_prefix = "promo"
                auto_msg = (
                    f"Thanks for reaching out for a promo/partnership with **Love heaven**, "
                    f"{interaction.user.mention}! Our partnership team will connect with you soon. "
                    "Please share your proposal or link below."
                )
            else:
                category_name = "Giveaway Claims"
                role_id = 1558070577527390248
                channel_prefix = "giveaway"
                auto_msg = (
                    f"Congratulations on winning the giveaway, {interaction.user.mention}! 🎉 "
                    "Our team will verify your win and deliver your prize shortly. "
                    "Please share the giveaway message link or screenshot below."
                )

            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                category = await guild.create_category(category_name)

            support_role = guild.get_role(role_id)

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

            ticket_channel = await guild.create_text_channel(
                name=f"{channel_prefix}-{interaction.user.name}",
                category=category,
                overwrites=overwrites,
                topic=f"Support Ticket ({val}) by {interaction.user.id}",
            )

            role_mention = support_role.mention if support_role else f"<@&{role_id}>"

            if HAS_COMPONENTS_V2:
                opened_view = TicketOpenedV2View(bot, guild, auto_msg)
                await ticket_channel.send(
                    content=f"{interaction.user.mention} {role_mention}",
                    view=opened_view,
                )
            else:
                embed = create_embed(bot, guild, title="🎫 Ticket Opened", description=auto_msg)
                await ticket_channel.send(
                    content=f"{interaction.user.mention} {role_mention}",
                    embed=embed,
                    view=TicketControlView(bot, guild),
                )

            await interaction.response.send_message(
                f"✅ Your ticket has been created: {ticket_channel.mention}",
                ephemeral=True,
            )

        except Exception as e:
            try:
                await interaction.response.send_message(f"❌ Error: `{e}`", ephemeral=True)
            except Exception:
                pass


class SupportDropdownView(ui.View):
    def __init__(self, bot=None):
        super().__init__(timeout=None)
        self.add_item(SupportTicketSelect(bot))


class SupportSetupV2View(ui.LayoutView):
    """Main ticketsetsupport panel — dropdown card ke andar aur credit sabse last mein."""

    def __init__(self, bot, guild, title: str, body: str):
        super().__init__(timeout=None)
        select_menu = SupportTicketSelect(bot)
        self.add_item(
            build_card_v2(
                bot,
                guild,
                title=title,
                body=body,
                action_items=[select_menu],
            )
        )


class SupportTickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # Bot restart ke baad bhi purane panels aur close buttons kaam karein
        self.bot.add_view(SupportDropdownView(self.bot))
        self.bot.add_view(TicketControlView(self.bot))

    @commands.command(name="ticketsetsupport")
    @commands.has_permissions(administrator=True)
    async def ticket_set_support(self, ctx):
        title = "Love heaven | Support Center"
        description = (
            "Welcome to **Love heaven** Support Center! Please select the appropriate category "
            "from the dropdown menu below depending on what you need assistance with.\n\n"
            "⚖️ **Staff Complaint** - Report any issues or unfair treatment.\n"
            "🤝 **Promo & Sponsorship** - Partner or promote with us.\n"
            "🎁 **Giveaway Claim** - Claim your won prizes.\n\n"
            "⚠️ **Please make sure to select the correct category to avoid delays!**"
        )

        if HAS_COMPONENTS_V2:
            view = SupportSetupV2View(self.bot, ctx.guild, title=title, body=description)
            await ctx.send(view=view)
        else:
            embed = create_embed(self.bot, ctx.guild, title=title, description=description)
            await ctx.send(embed=embed, view=SupportDropdownView(self.bot))


async def setup(bot):
    await bot.add_cog(SupportTickets(bot))
