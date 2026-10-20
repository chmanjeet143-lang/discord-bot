import discord
from discord.ext import commands

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class Vanity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vanity", help="Sends the server vanity link.")
    async def vanity_command(self, ctx):
        guild = ctx.guild
        vanity_url = guild.vanity_url

        if not vanity_url:
            embed = create_embed(
                guild,
                title="🔗 Server Vanity Link",
                description="This server does not have an active vanity URL (Level 3 boost required).",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)

        embed = create_embed(
            guild,
            title="✨ Moonlight Heaven • Official Vanity",
            description=f"Here is our server's vanity link:\n\n🔗 **{vanity_url}**",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Vanity(bot))
