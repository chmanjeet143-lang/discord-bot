import discord
from discord.ext import commands
from discord import ui

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(title="", description="", color=0x2B2D31, thumbnail=None):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail or DEFAULT_AVATAR)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class HelpDropdown(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Home", description="Return to the main help menu.", emoji="🏠", value="home"),
            discord.SelectOption(label="Ticket", description="View ticket system commands.", emoji="🎫", value="ticket"),
            discord.SelectOption(label="Utility", description="View utility and game commands.", emoji="🛠️", value="utility"),
            discord.SelectOption(label="Information", description="View server and user info commands.", emoji="ℹ️", value="info"),
            discord.SelectOption(label="Moderation", description="View moderation and security commands.", emoji="🛡️", value="moderation"),
        ]
        super().__init__(placeholder="Select Module From Here...", min_values=1, max_values=1, options=options, custom_id="zynrax_help_select")

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        
        if val == "home":
            desc = (
                "**Hey , I'm Moonlight Heaven™**\n\n"
                "A powerful multipurpose bot with fastest security and management systems.\n\n"
                "• **My Prefix is** `&`\n"
                "• **Total Commands:** 20+\n"
                "• **Choose a Specific Module of your Desire**\n\n"
                "📂 » **Ticket**\n"
                "🛠️ » **Utility**\n"
                "ℹ️ » **Information**\n"
                "🛡️ » **Moderation**\n\n"
                "🔗 **Links**\n"
                "[Support Server](https://discord.gg/moonlightheaven) | [Website](https://discord.gg/moonlightheaven)"
            )
            embed = create_embed(title="Moonlight Heaven Help Center", description=desc)
            await interaction.response.edit_message(embed=embed, view=self.view)

        elif val == "ticket":
            desc = "🎫 **Ticket Module Commands:**\n\n`&ticketsetup` - Setup the interactive dropdown ticket panel."
            embed = create_embed(title="Ticket Module", description=desc)
            await interaction.response.edit_message(embed=embed, view=self.view)

        elif val == "utility":
            desc = (
                "🛠️ **Utility & Games Module:**\n\n"
                "`&say <msg>` - Make bot say a message.\n"
                "`&reply <id> <msg>` - Reply to a message.\n"
                "`&start <num>` - Start counting game.\n"
                "`&emojiadd <url> <name>` - Add custom emoji.\n"
                "`&stickeradd <name>` - Add custom sticker.\n"
                "`&m / &v / &i` - Check stats (Message, Voice, Invite).\n"
                "`&rm all / &rv all / &ri all` - Reset stats."
            )
            embed = create_embed(title="Utility Module", description=desc)
            await interaction.response.edit_message(embed=embed, view=self.view)

        elif val == "info":
            desc = (
                "ℹ️ **Information Module:**\n\n"
                "`&avatar [user]` - View avatar in PNG/JPG/WEBP.\n"
                "`&userinfo [user]` - Detailed user profile info.\n"
                "`&serverinfo` - Detailed server stats.\n"
                "`&botinfo` - Bot hardware and network stats."
            )
            embed = create_embed(title="Information Module", description=desc)
            await interaction.response.edit_message(embed=embed, view=self.view)

        elif val == "moderation":
            desc = (
                "🛡️ **Moderation & Security Module:**\n\n"
                "`&lock / &unlock` - Lock or unlock channels.\n"
                "`&hide / &unhide` - Hide or unhide channels.\n"
                "`&kick / &ban / &massban` - Punish members.\n"
                "`&mute / &warn` - Restrict users.\n"
                "`&antinuke <on/off>` - Toggle anti-nuke.\n"
                "`&antiaddbot <on/off>` - Restrict bot adds to owner only."
            )
            embed = create_embed(title="Moderation Module", description=desc)
            await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpDropdown())

class HelpMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx):
        desc = (
            "**Hey , I'm Moonlight Heaven™**\n\n"
            "A powerful multipurpose bot with fastest security and management systems.\n\n"
            "• **My Prefix is** `&`\n"
            "• **Total Commands:** 20+\n"
            "• **Choose a Specific Module of your Desire**\n\n"
            "📂 » **Ticket**\n"
            "🛠️ » **Utility**\n"
            "ℹ️ » **Information**\n"
            "🛡️ » **Moderation**\n\n"
            "🔗 **Links**\n"
            "[Support Server](https://discord.gg/moonlightheaven) | [Website](https://discord.gg/moonlightheaven)"
        )
        embed = create_embed(title="Moonlight Heaven Help Center", description=desc)
        await ctx.send(embed=embed, view=HelpView())
        
        # Message delete karne wali problem yahan solve kar di hai:
        # Ab aapka command type kiya hua message delete nahi hoga, taaki chat natural rahe!

async def setup(bot):
    await bot.add_cog(HelpMenu(bot))
