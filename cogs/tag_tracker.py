import discord
from discord.ext import commands

SERVER_TAG = "Moon"  # Aapka server tag
LOG_CHANNEL_ID = 1562820194236366868  # Jahan tag add/remove hone ka message jayega (Channel ID)

class TagTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_tag(self, member: discord.Member) -> bool:
        """User ke username, global name ya nickname mein tag check karta hai."""
        name_to_check = [
            member.name,
            member.global_name or "",
            member.nick or ""
        ]
        return any(SERVER_TAG.lower() in text.lower() for text in name_to_check)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Bot updates ko ignore karein
        if after.bot:
            return

        before_has = self.has_tag(before)
        after_has = self.has_tag(after)

        channel = after.guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return

        # Agar pehle tag nahi tha, ab lagaa liya hai
        if not before_has and after_has:
            embed = discord.Embed(
                title="Guild Tag Added",
                description=f"{after.mention} ne server tag (`{SERVER_TAG}`) pehn liya hai!",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            await channel.send(embed=embed)

        # Agar pehle tag tha, ab hata diya hai
        elif before_has and not after_has:
            embed = discord.Embed(
                title="Guild Tag Removed",
                description=f"{after.mention} ne server tag (`{SERVER_TAG}`) hata diya hai.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            await channel.send(embed=embed)

    # Prefix Commands
    @commands.command(name="checktag")
    async def checktag(self, ctx, member: discord.Member = None):
        """Check karein ki kisi user ke naam mein tag hai ya nahi. Usage: !checktag @user"""
        member = member or ctx.author
        if self.has_tag(member):
            await ctx.send(f"Haan, {member.mention} ke naam mein `{SERVER_TAG}` tag laga hua hai!")
        else:
            await ctx.send(f"Nahi, {member.mention} ke naam mein `{SERVER_TAG}` tag nahi hai.")

    @commands.command(name="tagstats")
    async def tagstats(self, ctx):
        """Server mein total kitne logo ne tag pehna hai check karne ke liye. Usage: !tagstats"""
        count = sum(1 for member in ctx.guild.members if self.has_tag(member))
        await ctx.send(f"Total `{count}` members ne server tag (`{SERVER_TAG}`) pehna hua hai!")

async def setup(bot):
    await bot.add_cog(TagTracker(bot))
