import discord
from discord.ext import commands
from discord import ui
import asyncio

class TicketModal(ui.Modal, title="🎫 Create Support Ticket"):
    subject = ui.TextInput(label="Ticket Subject / Heading", placeholder="e.g., General Help", required=True, max_length=100)
    description = ui.TextInput(label="Describe your issue", placeholder="Apni problem detail mein likhein...", style=discord.TextStyle.paragraph, required=True, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")

        support_role = discord.utils.get(guild.roles, name="Support Team")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel_name = f"ticket-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(title=f"🎫 Ticket: {self.subject.value}", description=f"**User:** {interaction.user.mention}\n**Reason:** {self.description.value}", color=0x00FF00)
        view = TicketControlView()
        tag_text = support_role.mention if support_role else "@here"
        
        await ticket_channel.send(content=f"{tag_text} - Naya ticket khula hai!", embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket ban gaya: {ticket_channel.mention}", ephemeral=True)

class TicketControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("⚠️ Yeh ticket 5 seconds mein delete ho raha hai...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketSetupView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.primary, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(TicketModal())

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticketsetup")
    @commands.has_permissions(administrator=True)
    async def ticket_setup(self, ctx):
        embed = discord.Embed(title="🎫 Support Center", description="Neeche diye gaye button par click karke ticket banayein.", color=0x5865F2)
        await ctx.send(embed=embed, view=TicketSetupView())
        try: await ctx.message.delete()
        except: pass

async def setup(bot):
    await bot.add_cog(Tickets(bot))
