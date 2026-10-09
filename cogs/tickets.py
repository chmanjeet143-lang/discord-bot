import discord
from discord.ext import commands
from discord import ui
import asyncio

# Dropdown Menu for Categories
class TicketSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Staff Complaint",
                description="Report or complain about a staff member.",
                emoji="⚠️",
                value="staff_complaint"
            ),
            discord.SelectOption(
                label="Partnership & Sponsorship",
                description="Inquiries regarding partnerships and sponsorships.",
                emoji="🤝",
                value="partnership"
            ),
            discord.SelectOption(
                label="Zeus Management / Owner Contact",
                description="Urgent matters directly related to server management.",
                emoji="⚡",
                value="management"
            )
        ]
        super().__init__(placeholder="Make a selection", min_values=1, max_values=1, options=options, custom_id="ticket_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category_name = "Tickets"
        
        # Category find ya create karna
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        # Support role name yahan apne hisab se badal sakte hain
        support_role = discord.utils.get(guild.roles, name="Support Team")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        # Ticket Channel Name
        channel_name = f"ticket-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket opened by {interaction.user.id} | Type: {self.values[0]}"
        )

        # Yahan aap apne hisab se ticket open hone par message change kar sakte hain
        embed = discord.Embed(
            title="🎫 Support Ticket Opened",
            description=(
                f"Hello {interaction.user.mention},\n\n"
                "Thank you for reaching out to support. Our team members will "
                "contact you shortly. Please describe your issue clearly in the meantime."
            ),
            color=0x5865F2
        )
        embed.set_footer(text="Click the close button below to close this ticket.")

        view = TicketControlView()
        tag_text = support_role.mention if support_role else "@here"

        # Bot tag karke custom message bhejega
        await ticket_channel.send(
            content=f"{tag_text} - New ticket opened by {interaction.user.mention}!",
            embed=embed,
            view=view
        )

        await interaction.response.send_message(f"✅ Your ticket has been created: {ticket_channel.mention}", ephemeral=True)

class TicketDropdownView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class TicketControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("⚠️ This ticket will be deleted in 5 seconds...", ephemeral=True)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticketsetup")
    @commands.has_permissions(administrator=True)
    async def ticket_setup(self, ctx):
        """Sends the interactive dropdown ticket panel."""
        embed = discord.Embed(
            title="Support Center",
            description="Please select a category from the dropdown menu below to open a support ticket.",
            color=0x2B2D31
        )
        embed.set_footer(text="Moonlight Heaven Ticket System")
        
        await ctx.send(embed=embed, view=TicketDropdownView())
        try:
            await ctx.message.delete()
        except:
            pass

async def setup(bot):
    await bot.add_cog(Tickets(bot))
