import discord
from discord.ext import commands

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_count = 1
        self.counting_channel = None
        self.success_emoji = "✅"
        
        # Tracking dictionaries for members
        self.message_counts = {}
        self.invite_counts = {}
        self.voice_time = {}

    @commands.command(name="start")
    @commands.has_permissions(manage_channels=True)
    async def start_counting(self, ctx, number: int, channel: discord.TextChannel = None, emoji: str = "✅"):
        self.current_count = number
        self.counting_channel = channel or ctx.channel
        self.success_emoji = emoji

        embed = create_embed(
            ctx.guild,
            title="🎯 Counting Game Started!",
            description=f"The counting game has been configured successfully with love!\n\n"
                        f"📂 **Channel:** {self.counting_channel.mention}\n"
                        f"🔢 **Start Number:** **{self.current_count}**\n"
                        f"✨ **Reaction Emoji:** {self.success_emoji}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Track message count for &m
        author_id = message.author.id
        self.message_counts[author_id] = self.message_counts.get(author_id, 0) + 1

        # Counting game logic
        if self.counting_channel and message.channel.id == self.counting_channel.id:
            try:
                number = int(message.content.strip())
            except ValueError:
                return  

            if number == self.current_count:
                try:
                    await message.add_reaction(self.success_emoji)
                except:
                    pass
                self.current_count += 1
            else:
                embed = create_embed(
                    message.guild,
                    title="✨ Oopsie! Close, but not quite!",
                    description=f"Oh dear {message.author.mention}, that wasn't quite the right number! Please don't worry, mistakes happen to the best of us.\n\nThe next correct number to send is: **{self.current_count}**",
                    color=discord.Color.orange()
                )
                await message.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        # Basic tracking hook for voice activity
        if before.channel is None and after.channel is not None:
            self.voice_time[member.id] = self.voice_time.get(member.id, 0) + 1

    @commands.command(name="m")
    async def message_count(self, ctx):
        count = self.message_counts.get(ctx.author.id, 0)
        embed = create_embed(
            ctx.guild,
            title="💬 Message Statistics",
            description=f"Hello {ctx.author.mention}! You have sent a total of **{count}** messages in this server while I've been active. Keep up the wonderful activity!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="v")
    async def voice_count(self, ctx):
        v_stat = self.voice_time.get(ctx.author.id, 0)
        embed = create_embed(
            ctx.guild,
            title="🎙️ Voice Timing Statistics",
            description=f"Greetings {ctx.author.mention}! Your voice activity engagement score is currently registered at **{v_stat} sessions**. Thank you for hanging out in our voice channels!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="i")
    async def invite_count(self, ctx):
        invites = self.invite_counts.get(ctx.author.id, 0)
        embed = create_embed(
            ctx.guild,
            title="✉️ Invite Statistics",
            description=f"Hello {ctx.author.mention}! You have successfully invited **{invites}** members to **Moonlight Heaven**. We truly appreciate your support in growing our community!",
            color=discord.Color.purple()
        )
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

async def setup(bot):
    await bot.add_cog(Utility(bot))
