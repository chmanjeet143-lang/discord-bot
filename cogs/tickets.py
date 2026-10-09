import discord
from discord.ext import commands
from discord import ui
import asyncio

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class SupportTicketSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Staff Complaint",
                description="Report or complain about a staff member.",
                emoji="⚖️",
                value="staff_complaint"
            ),
            discord.SelectOption(
                label="Promo & Sponsorship",
                description="Inquiries for promotions or partnerships.",
                emoji="🤝",
                value="promo_sponsor"
            ),
            discord.SelectOption(
                label="Giveaway Claim",
                description="Claim your won giveaway prize.",
                emoji="🎁",
                value="giveaway_claim"
            )
        ]
        super().__init__(placeholder="Make a selection to open a ticket...", min_values=1, max_values=1, options=options, custom_id="support_ticket_dropdown")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        val = self.values[0]
        
        if val == "staff_complaint":
            category_name = "Staff Complaints"
            role_id = 1558070324229316731
            channel_prefix = "complaint"
            auto_msg = f"Thank you for bringing this to our notice, {interaction.user.mention}. Management will review your complaint shortly. Please share all the details and proofs below."
        elif val == "promo_sponsor":
            category_name = "Promotions & Partnerships"
            role_id = 1558070509256581170
            channel_prefix = "promo"
            auto_msg = f"Thanks for reaching out for a promo/partnership with **Moonlight Heaven**, {interaction.user.mention}! Our partnership team will connect with you soon. Please share your proposal or link below."
        else: # giveaway_claim
            category_name = "Giveaway Claims"
            role_id = 1558070577527390248
            channel_prefix = "giveaway"
            auto_msg = f"Congratulations on winning the giveaway, {interaction.user.mention}! 🎉 Our team will verify your win and deliver your prize shortly. Please share the giveaway message link or screenshot below."

        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        support_role = guild.get_role(role_id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        ticket_channel = await guild.create_text_channel(
            name=f"{channel_prefix}-{interaction.user.name}",
            category=category,
            overwrites=overwrites,
            topic=f"Support Ticket ({val}) by {interaction.user.id}"
        )

        role_mention = support_role.mention if support_role else f"<@&{role_id}>"

        embed = create_embed(
            guild,
            title="🎫 Ticket Opened",
            description=auto_msg
        )

        view = TicketControlView()
        await ticket_channel.send(content=f"{interaction.user.mention} {role_mention}", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Your ticket has been created: {ticket_channel.mention}", ephemeral=True)

class SupportDropdownView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SupportTicketSelect())

class TicketControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_support_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        embed = create_embed(interaction.guild, title="Closing Ticket", description="⚠️ This ticket channel will be deleted in 5 seconds...", color=0xED4245)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

class SupportTickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticketsetsupport")
    @commands.has_permissions(administrator=True)
    async def ticket_set_support(self, ctx):
        """Creates the Support & Management Dropdown Ticket Panel."""
        title = "🛡️ Moonlight Heaven | Support Center"
        description = (
            "Welcome to **Moonlight Heaven** Support Center! Please select the appropriate category from the dropdown menu below depending on what you need assistance with.\n\n"
            "⚖️ **Staff Complaint** - Report any issues or unfair treatment.\n"
            "🤝 **Promo & Sponsorship** - Partner or promote with us.\n"
            "🎁 **Giveaway Claim** - Claim your won prizes.\n\n"
            "⚠️ **Please make sure to select the correct category to avoid delays!**"
        )
        
        embed = create_embed(ctx.guild, title=title, description=description)
        await ctx.send(embed=embed, view=SupportDropdownView())

async def setup(bot):
    await bot.add_cog(SupportTickets(bot))
