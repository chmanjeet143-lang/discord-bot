import discord
from discord.ext import commands

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ask(self, ctx, *, message: str):
        await ctx.send(f"आपने कहा: {message}")

async def setup(bot):
    await bot.add_cog(AI(bot))
