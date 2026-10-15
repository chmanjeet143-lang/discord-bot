import discord
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_count = 1
        self.counting_channel = None
        self.success_emoji = "✅"

    @commands.command(name="start")
    @commands.has_permissions(manage_channels=True)
    async def start_counting(self, ctx, number: int, channel: discord.TextChannel = None, emoji: str = "✅"):
        self.current_count = number
        self.counting_channel = channel or ctx.channel
        self.success_emoji = emoji

        embed = discord.Embed(
            title="🎯 Counting Game Started!",
            description=f"Counting has been configured successfully!\n\n"
                        f"📂 **Channel:** {self.counting_channel.mention}\n"
                        f"🔢 **Start Number:** **{self.current_count}**\n"
                        f"✨ **Reaction:** {self.success_emoji}",
            color=discord.Color.green()
        )
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Agar counting channel set hai aur message usi channel mein hai
        if self.counting_channel and message.channel.id == self.counting_channel.id:
            # Check karte hain ki message ek valid integer hai ya nahi
            try:
                number = int(message.content.strip())
            except ValueError:
                return  # Agar number nahi hai toh ignore karo, msg delete mat karo

            # Agar counting sahi hai
            if number == self.current_count:
                try:
                    await message.add_reaction(self.success_emoji)
                except:
                    pass
                self.current_count += 1
            else:
                # Agar counting galat hai toh pyaar se English mein guide karo, msg delete mat karo
                embed = discord.Embed(
                    title="Oopsie! Close, but not quite ✨",
                    description=f"Oh no, {message.author.mention}! That wasn't the right number. Don't worry, mistakes happen!\nThe next correct number to send is: **{self.current_count}**",
                    color=discord.Color.orange()
                )
                embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
                await message.channel.send(embed=embed)

    @commands.command(name="m")
    async def message_count(self, ctx, number: int = None):
        embed = discord.Embed(
            title="💬 Counting Game Status",
            description=f"Current active counting is running smoothly!\nNext expected number is: **{self.current_count}**",
            color=discord.Color.from_rgb(138, 43, 226)
        )
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

    @commands.command(name="v")
    async def voice_count(self, ctx):
        embed = discord.Embed(
            title="🎙️ Voice Timing Count",
            description="Voice activity tracking is active for this server.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

    @commands.command(name="say")
    async def say_command(self, ctx, *, message: str):
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(message)

    @commands.command(name="reply")
    async def reply_command(self, ctx, *, message: str):
        if ctx.message.reference:
            original_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            await original_msg.reply(message)
        else:
            await ctx.send(message)

    @commands.command(name="i")
    async def invite_count(self, ctx):
        embed = discord.Embed(
            title="✉️ Invite Statistics",
            description=f"Invite tracking is enabled for {ctx.author.mention}.",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
