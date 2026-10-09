import discord
from discord.ext import commands

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

# Unified Embed Helper Function
def create_embed(ctx_or_user, title="", description="", color=0x2B2D31, thumbnail=None):
    avatar_url = thumbnail or getattr(ctx_or_user, 'display_avatar', None) and ctx_or_user.display_avatar.url or DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=avatar_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class HelpMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx):
        """Displays all commands in the unified Moonlight Heaven embed format."""
        description = (
            "Welcome to the help center! Here are all available commands categorized for your assistance.\n\n"
            "🔹 **Prefix:** `&`\n"
        )

        embed = create_embed(ctx.author, title="✨ Moonlight Heaven • Help Menu", description=description)

        # 1. Ticket System
        embed.add_field(
            name="🎫 Ticket System",
            value="`&ticketsetup` - Setup the interactive dropdown ticket panel.",
            inline=False
        )
        
        # 2. Utility & Games
        embed.add_field(
            name="🛠️ Utility & Games",
            value=(
                "`&say <message>` - Make the bot say a message.\n"
                "`&reply <msg_id> <msg>` - Reply to a specific message.\n"
                "`&start <num> [channel] [emoji]` - Start the counting game.\n"
                "`&emojiadd <url> <name>` - Add a custom emoji.\n"
                "`&stickeradd <name>` - Add a custom sticker."
            ),
            inline=False
        )
        
        # 3. Information Commands
        embed.add_field(
            name="ℹ️ Information Commands",
            value=(
                "`&avatar [member]` - View user avatar (PNG/JPG/WEBP)[span_3](start_span)[span_3](end_span).\n"
                "`&userinfo [member]` - View detailed user profile[span_4](start_span)[span_4](end_span).\n"
                "`&serverinfo` - View server statistics.\n"
                "`&botinfo` - View bot system information[span_5](start_span)[span_5](end_span)."
            ),
            inline=False
        )

        # 4. Statistics & Tracking
        embed.add_field(
            name="📊 Statistics Tracking",
            value=(
                "`&m [member]` - Check message count.\n"
                "`&v [member]` - Check voice channel time.\n"
                "`&i [member]` - Check invite count."
            ),
            inline=False
        )

        # 5. Admin Resets
        embed.add_field(
            name="⚙️ Admin Reset Commands",
            value=(
                "`&rm all` - Reset all message statistics.\n"
                "`&rv all` - Reset all voice statistics.\n"
                "`&ri all` - Reset all invite statistics."
            ),
            inline=False
        )

        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

async def setup(bot):
    await bot.add_cog(HelpMenu(bot))
