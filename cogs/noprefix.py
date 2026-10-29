import discord
from discord.ext import commands
import json
import os

DATA_FILE = "noprefix.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class NoPrefix(commands.Cog, name="NoPrefix"):
    """NoPrefix management commands for trusted users."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="no", help="View all available NoPrefix commands and descriptions.")
    async def no_prefix_main(self, ctx):
        embed = discord.Embed(
            title="Category • NoPrefix",
            description="Here are all the available commands under **NoPrefix**:\n\n"
                        "• `&no add` — Add a user to the no-prefix list.\n"
                        "• `&no remove` — Remove a user from the no-prefix list.\n"
                        "• `&no list` — View all users in the no-prefix list.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

    @commands.command(name="add", help="Add a user to the no-prefix list.")
    @commands.has_permissions(administrator=True)
    async def no_prefix_add(self, ctx, member: discord.Member):
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data:
            data[guild_id] = []

        if member.id in data[guild_id]:
            embed = discord.Embed(
                title="NoPrefix • Warning",
                description=f"⚠️ **{member.display_name}** pehle se hi no-prefix list mein hai!",
                color=discord.Color.gold()
            )
            embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
            return await ctx.send(embed=embed)

        data[guild_id].append(member.id)
        save_data(data)
        
        embed = discord.Embed(
            title="NoPrefix • Added",
            description=f"✅ Successfully **{member.display_name}** ko no-prefix list mein add kar diya gaya hai!",
            color=discord.Color.green()
        )
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

    @commands.command(name="remove", help="Remove a user from the no-prefix list.")
    @commands.has_permissions(administrator=True)
    async def no_prefix_remove(self, ctx, member: discord.Member):
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or member.id not in data[guild_id]:
            embed = discord.Embed(
                title="NoPrefix • Error",
                description=f"❌ **{member.display_name}** no-prefix list mein maujood nahi hai!",
                color=discord.Color.red()
            )
            embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
            return await ctx.send(embed=embed)

        data[guild_id].remove(member.id)
        save_data(data)
        
        embed = discord.Embed(
            title="NoPrefix • Removed",
            description=f"✅ Successfully **{member.display_name}** ko no-prefix list se hata diya gaya hai!",
            color=discord.Color.green()
        )
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

    @commands.command(name="list", help="View all users in the no-prefix list.")
    async def no_prefix_list(self, ctx):
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id]:
            embed = discord.Embed(
                title="Server No-Prefix Users",
                description="📂 Is server par koi bhi user no-prefix list mein nahi hai.",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
            return await ctx.send(embed=embed)

        mentions = [f"<@{uid}>" for uid in data[guild_id]]
        
        embed = discord.Embed(
            title="📜 Server No-Prefix Users",
            description="\n".join(mentions),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        data = load_data()
        guild_id = str(message.guild.id)
        
        if guild_id in data and message.author.id in data[guild_id]:
            prefix = "&"
            if not message.content.startswith(prefix):
                message.content = prefix + message.content
                await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(NoPrefix(bot))
