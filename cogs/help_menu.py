import discord
from discord.ext import commands

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class HelpDropdown(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = []
        
        # Automatically scan all loaded cogs and build dropdown options dynamically
        for cog_name in self.bot.cogs:
            cog = self.bot.get_cog(cog_name)
            # Skip help cog itself from showing inside options if you want, 
            # par yahan humne HelpCog ke liye alag se handle kar liya hai
            if cog_name.lower() == "help":
                continue
            
            # Format label nicely with emojis and clean names
            emoji_map = {
                "Moderation": "🛡️",
                "Giveaway": "🎉",
                "Tickets": "🎫",
                "SupportTickets": "🎫",
                "Support Ticket": "🎫",
                "HelpCog": "❓",
                "Help": "❓",
                "Utility": "⚙️",
                "Information": "📊"
            }
            emoji = emoji_map.get(cog_name, "📁")
            
            # Clean up cog names if they are written together
            display_name = cog_name
            if cog_name == "SupportTickets":
                display_name = "Support Tickets"
            elif cog_name == "HelpCog":
                display_name = "Help Menu"

            options.append(
                discord.SelectOption(
                    label=f"{display_name} Commands",
                    value=cog_name,
                    description=f"Explore all commands related to {display_name}.",
                    emoji=emoji
                )
            )

        # Fallback if no cogs found
        if not options:
            options.append(discord.SelectOption(label="No Modules Found", value="none", description="No active cogs detected."))

        super().__init__(placeholder="✨ Select a category to explore commands...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_cog = self.values[0]
        cog = self.bot.get_cog(selected_cog)
        
        if not cog:
            return await interaction.response.send_message("Sorry, this category could not be found.", ephemeral=True)

        # Gather all commands inside this cog
        command_list = []
        for cmd in cog.get_commands():
            if not cmd.hidden:
                command_list.append(f"• `&{cmd.name}` - {cmd.help or 'No description provided.'}")

        commands_str = "\n".join(command_list) if command_list else "No public commands available in this category."

        embed = create_embed(
            interaction.guild,
            title=f"📂 Category • {selected_cog}",
            description=f"Here are all the available commands under **{selected_cog}**:\n\n{commands_str}",
            color=discord.Color.purple()
        )
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=180)
        self.add_item(HelpDropdown(bot))

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = create_embed(
            ctx.guild,
            title="🌙 Moonlight Heaven • Help Center",
            description=(
                f"Hello {ctx.author.mention}! Welcome to the interactive help command center.\n\n"
                "Please select a category from the dropdown menu below to view its available commands."
            ),
            color=discord.Color.purple()
        )
        view = HelpView(self.bot)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
