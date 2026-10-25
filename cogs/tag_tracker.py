import discord
from discord.ext import commands

class TagTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.test_channel_id = None

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.bot:
            return

        # Console me print karke check karne ke liye
        print(f"--- MEMBER UPDATE DETECTED ---")
        print(f"User: {after.name}")
        print(f"Before Name/Nick: {before.display_name} | After Name/Nick: {after.display_name}")
        print(f"Before Clan: {getattr(before, 'clan', None)} | After Clan: {getattr(after, 'clan', None)}")

        # Agar test channel set hai, toh wahan tag karke message bhejo
        if self.test_channel_id:
            channel = after.guild.get_channel(self.test_channel_id)
            if channel:
                await channel.send(f"🔔 {after.mention} ne apna tag ya nickname change kiya! **Tag adopted!** ✨")

    @commands.command(name="testchannel")
    @commands.has_permissions(administrator=True)
    async def test_channel(self, ctx, channel: discord.TextChannel):
        self.test_channel_id = channel.id
        await ctx.send(f"✅ Test channel set ho gaya hai {channel.mention} par. Ab nickname/tag badal kar test karo!")

async def setup(bot):
    await bot.add_cog(TagTracker(bot))
