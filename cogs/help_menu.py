import discord
from discord.ext import commands

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(guild, title="", description="", color=0x9B59B6):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class HelpDropdown(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = []
        
        # Har category ke liye specific emojis yahan set kiye hain
        emoji_map = {
            "moderation": "🛡️",
            "automod": "🤖",
            "giveaway": "🎉",
            "tickets": "🎫",
            "supporttickets": "🎫",
            "support ticket": "🎫",
            "utility": "⚙️",
            "information": "📊",
            "leveling": "⭐",
            "welcome": "👋",
            "welcome1": "👋",
            "welcome2": "✨",
            "bump": "📢",
            "boost": "🚀",
            "clone": "📋",
            "jail": "⛓️"
        }

        for cog_name in self.bot.cogs:
            if cog_name.lower() in ["helpcog", "help"]:
                continue
            
            cog = self.bot.get_cog(cog_name)
            if not any(not cmd.hidden for cmd in cog.get_commands()):
                continue

            display_name = cog_name
            if cog_name.lower() == "supporttickets":
                display_name = "Support Tickets"

            # Agar exact match na mile toh naam ke hisaab se koi acha emoji ya default star/sparkle le lega
            emoji = emoji_map.get(cog_name.lower(), "✨")

            options.append(
                discord.SelectOption(
                    label=f"{display_name} Commands",
                    value=cog_name,
                    description=f"Explore all commands related to {display_name}.",
                    emoji=emoji
                )
            )

        if not options:
            options.append(discord.SelectOption(label="No Modules Found", value="none", description="No active cogs detected."))

        super().__init__(placeholder="✨ Select a category to explore commands...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_cog = self.values[0]
        cog = self.bot.get_cog(selected_cog)
        
        if not cog:
            return await interaction.response.send_message("❌ This category could not be found.", ephemeral=True)

        command_list = []
        for cmd in cog.get_commands():
            if cmd.hidden:
                continue
            
            # Check agar command group hai (subcommands hain)
            if isinstance(cmd, commands.Group):
                sub_cmds = [sub.name for sub in cmd.commands if not sub.hidden]
                sub_str = f" (Subcommands: {', '.join(sub_cmds)})" if sub_cmds else ""
                desc = cmd.short_doc or cmd.help or "No description provided."
                command_list.append(f"• `&{cmd.name}`{sub_str} — *{desc}*")
            else:
                desc = cmd.short_doc or cmd.help or "No description provided."
                command_list.append(f"• `&{cmd.name}` — *{desc}*")

        commands_str = "\n".join(command_list) if command_list else "No public commands available in this category."

        embed = create_embed(
            interaction.guild,
            title=f"🌌 Category • {selected_cog}",
            description=f"Here are all the available commands under **{selected_cog}**:\n\n{commands_str}",
            color=discord.Color.purple()
        )
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=180)
        self.add_item(HelpDropdown(bot))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass

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
                "✨ Please select a category from the dropdown menu below to view its available commands."
            ),
            color=discord.Color.purple()
        )
        view = HelpView(self.bot)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
