import discord
from discord.ext import commands
from discord import ui

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class HelpSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Moderation", description="View server moderation commands.", emoji="🛡️", value="mod"),
            discord.SelectOption(label="Tickets & Support", description="View ticket and support setup commands.", emoji="🎫", value="tickets"),
            discord.SelectOption(label="Utility & Games", description="View counting game and utility commands.", emoji="🛠️", value="utility"),
        ]
        super().__init__(placeholder="📂 Select a category to view commands...", min_values=1, max_values=1, options=options, custom_id="help_menu_dropdown")

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        guild = interaction.guild

        if val == "mod":
            embed = create_embed(
                guild,
                title="🛡️ Moderation Commands",
                description="Here are the available moderation commands to protect and manage the server:\n\n"
                            "• `&ban` - Ban a member from the server.\n"
                            "• `&kick` - Kick a member from the server.\n"
                            "• `&mute` - Mute a disruptive member.\n"
                            "• `&clear` - Bulk delete chat messages.\n"
                            "• `&slowmode` - Set channel slowmode.",
                color=discord.Color.red()
            )
        elif val == "tickets":
            embed = create_embed(
                guild,
                title="🎫 Tickets & Support Commands",
                description="Here are the ticket management and setup commands:\n\n"
                            "• `&ticketsetsupport` - Setup the Support Center dropdown menu.\n"
                            "• `&ticketsetupstaff` - Setup the Staff Application button panel.",
                color=discord.Color.blue()
            )
        else:
            embed = create_embed(
                guild,
                title="🛠️ Utility & Games Commands",
                description="Here are the utility and counting game commands:\n\n"
                            "• `&start` - Start the counting game in a channel.\n"
                            "• `&counting` - Check current counting game status.\n"
                            "• `&m` - Check message statistics.\n"
                            "• `&v` - Check voice timing count.\n"
                            "• `&i` - Check invite statistics.\n"
                            "• `&say` - Make the bot say something.\n"
                            "• `&reply` - Reply to a specific message.",
                color=discord.Color.green()
            )

        await interaction.response.edit_message(embed=embed)

class HelpView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)  # 3 minutes timeout
        self.add_item(HelpSelect())

class HelpMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        intro_desc = (
            "👋 Hello there! Main **Moonlight Heaven** hoon, aapka apna advanced Discord bot.\n"
            "Mujhe pure pyaar aur dedication ke sath **Zeus** ne banaya hai taaki aapke server ko ekdum secure, fun aur automated banaya ja sake.\n\n"
            "Neeche diye gaye dropdown menu se category select karein aur commands dekhein!"
        )
        embed = create_embed(ctx.guild, title="🌙 Moonlight Heaven • Help Center", description=intro_desc, color=0x8A2BE2)
        await ctx.send(embed=embed, view=HelpView())

async def setup(bot):
    await bot.add_cog(HelpMenu(bot))
