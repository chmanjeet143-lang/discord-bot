import discord
from discord.ext import commands
from discord import ui
import asyncio

# Dynamic Ticket Modal for Customizing Open Message
class TicketReasonModal(ui.Modal, title="Provide Ticket Details"):
    reason = ui.TextInput(
        label="Please describe your issue",
        style=discord.TextStyle.paragraph,
        placeholder="Type your issue or details here...",
        required=True,
        max_length=1000
    )

    def __init__(self, category_name, role_to_tag):
        super().__init__()
        self.category_name = category_name
        self.role_to_tag = role_to_tag

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category_name = "Tickets"
        
        # Category find ya create karna
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        # Role find karna jo tag hoga
        support_role = discord.utils.get(guild.roles, name=self.role_to_tag) or discord.utils.get(guild.roles, name="Support Team")

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
            topic=f"Ticket by {interaction.user.id} | Category: {self.category_name}"
        )

        # Apne hisaab se set ki gayi ticket open description
        embed = discord.Embed(
            title=f"🎫 Ticket: {self.category_name}",
            description=(
                f"Hello {interaction.user.mention},\n\n"
                f"**Your Issue / Details:**\n{self.reason.value}\n\n"
                "A staff member will be with you shortly. Please stay patient."
            ),
            color=0x5865F2
        )
        embed.set_footer(text="Moonlight Heaven Support System")

        view = TicketControlView()
        tag_text = support_role.mention if support_role else "@here"

        # Role tag aur custom message
        await ticket_channel.send(
            content=f"{tag_text} - New ticket opened by {interaction.user.mention}!",
            embed=embed,
            view=view
        )

        await interaction.response.send_message(f"✅ Your ticket has been created successfully: {ticket_channel.mention}", ephemeral=True)

class TicketSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Staff Complaint",
                description="Report or complain about a staff member.",
                emoji="⚠️",
                value="Staff Complaint"
            ),
            discord.SelectOption(
                label="Partnership & Sponsorship",
                description="Inquiries regarding partnerships and sponsorships.",
                emoji="🤝",
                value="Partnership & Sponsorship"
            ),
            discord.SelectOption(
                label="Zeus Management",
                description="Urgent matters directly related to server management.",
                emoji="⚡",
                value="Zeus Management"
            )
        ]
        super().__init__(placeholder="Make a selection to open a ticket", min_values=1, max_values=1, options=options, custom_id="custom_ticket_select")

    async def callback(self, interaction: discord.Interaction):
        # Yahan aap define kar sakte hain ki kis option par kaun sa role tag hoga
        selected_value = self.values[0]
        role_mapping = {
            "Staff Complaint": "Staff Team",
            "Partnership & Sponsorship": "Partnership Manager",
            "Zeus Management": "Management"
        }
        target_role = role_mapping.get(selected_value, "Support Team")
        
        await interaction.response.send_modal(TicketReasonModal(category_name=selected_value, role_to_tag=target_role))

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
    async def ticket_setup(self, ctx, title: str = "Support Center", *, description: str = "Please select a category from the dropdown menu below to open a support ticket."):
        """Usage: &ticketsetup [Title] | [Description]"""
        embed = discord.Embed(
            title=title,
            description=description,
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
