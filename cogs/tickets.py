import discord
from discord.ext import commands
from discord import ui
import asyncio

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

# Unified Embed Helper Function (Server Icon or Clean Thumbnail, No User Avatar)
def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class StaffTicketButtonView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Apply for Staff", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="open_staff_ticket_btn")
    async def open_staff_ticket(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        category_name = "Staff Applications"
        
        # Category find ya create karna
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        # Specific Role ID jo aapne di hai (<@&1558065387600617603>)
        role_id = 1558065387600617603
        support_role = guild.get_role(role_id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        # Ticket Channel Name
        channel_name = f"staff-ticket-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Staff Application Ticket by {interaction.user.id}"
        )

        role_mention = support_role.mention if support_role else f"<@&{role_id}>"
        
        # Ticket open hone ke baad andar ka message aur guidelines
        description_text = (
            f"Thank you for applying to the staff team at **Moonlight Heaven**, {interaction.user.mention}! Our staff will contact you soon.\n\n"
            f"⚠️ **Important Guidelines:**\n"
            f"• Do not share any false information in your application.\n"
            f"• Once the ticket is open, please be patient; our management team will review it shortly.\n\n"
            f"While you wait, please share the following details to speed up the process:\n\n"
            f"1. **Your Age & Timezone:**\n"
            f"2. **Previous staff/moderation experience (if any):**\n"
            f"3. **How active can you be on the server daily?**"
        )

        embed = create_embed(
            guild,
            title="📝 Staff Application Form",
            description=description_text
        )

        close_view = TicketControlView()

        # Bot tag karke embed bhejega with exact role ID
        await ticket_channel.send(
            content=f"{interaction.user.mention} {role_mention}",
            embed=embed,
            view=close_view
        )

        await interaction.response.send_message(f"✅ Your staff application ticket has been created: {ticket_channel.mention}", ephemeral=True)

class TicketControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_staff_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        embed = create_embed(guild, title="Closing Ticket", description="⚠️ This ticket channel will be deleted in 5 seconds...", color=0xED4245)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticketsetupstaff")
    @commands.has_permissions(administrator=True)
    async def ticket_setup_staff(self, ctx):
        """Creates the Staff Recruitment Panel."""
        title = "📝 Moonlight Heaven | Staff Recruitment"
        description = (
            "Want to join the **Moonlight Heaven** staff team and help our community grow?\n\n"
            "⚠️ **Important Guidelines:**\n"
            "• Do not share any false information in your application.\n"
            "• Once the ticket is open, please be patient; our management team will review it shortly.\n\n"
            "🎫 Click the button below to open your application ticket!"
        )
        
        embed = create_embed(ctx.guild, title=title, description=description)
        await ctx.send(embed=embed, view=StaffTicketButtonView())

async def setup(bot):
    await bot.add_cog(Tickets(bot))
