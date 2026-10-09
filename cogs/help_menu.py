import discord
from discord.ext import commands

class HelpMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Discord ka default help command hata dete hain taaki hamara custom embed chale
        self.bot.remove_command('help')

    @commands.command(name="help")
    async def help_command(self, ctx, *, category: str = None):
        # Embed ka basic setup
        embed = discord.Embed(
            title="✨ Moonlight Heaven — Help Menu",
            description="Type `&help [command]` for more info on a specific command.\nType `&help [category]` for a category's details.",
            color=discord.Color.from_rgb(138, 43, 226)
        )
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        # Agar koi specific category mangi ho
        if category:
            cat_lower = category.lower()
            if cat_lower == "info":
                embed.add_field(name="📂 Info Commands", value="`avatar`, `botinfo`, `serverinfo`, `userinfo`", inline=False)
            elif cat_lower == "moderation":
                embed.add_field(name="🛡️ Moderation Commands", value="`antiaddbot`, `antinuke`, `mute`, `warn`", inline=False)
            elif cat_lower == "utility":
                embed.add_field(name="🛠️ Utility Commands", value="`i`, `m`, `reply`, `say`, `v`", inline=False)
            else:
                embed.description = f"❌ Category **'{category}'** nahi mili!"
                embed.color = discord.Color.red()
            
            embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
            await ctx.send(embed=embed)
            return

        # Main help menu with all categories in Embed format
        embed.add_field(
            name="📂 Info",
            value="`avatar`, `botinfo`, `serverinfo`, `userinfo`",
            inline=False
        )
        embed.add_field(
            name="🛡️ Moderation",
            value="`antiaddbot`, `antinuke`, `mute`, `warn`",
            inline=False
        )
        embed.add_field(
            name="🛠️ Utility",
            value="`i`, `m`, `reply`, `say`, `v`",
            inline=False
        )
        
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpMenu(bot))
