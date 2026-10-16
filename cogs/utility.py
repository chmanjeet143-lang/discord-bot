import discord
from discord.ext import commands
import datetime
import re

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

def format_time(seconds: int):
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_count = 1
        self.counting_channel = None
        self.success_emoji = "✅"
        
        # Tracking dictionaries & Active VC timers {user_id: join_timestamp}
        self.message_counts = {}
        self.invite_counts = {}
        self.voice_time_seconds = {}
        self.vc_joins = {}

    @commands.command(name="start")
    @commands.has_permissions(manage_channels=True)
    async def start_counting(self, ctx, number: int, channel: discord.TextChannel = None, emoji: str = "✅"):
        self.current_count = number
        self.counting_channel = channel or ctx.channel
        self.success_emoji = emoji

        embed = create_embed(
            ctx.guild,
            title="🎯 Counting Game Started!",
            description=f"The counting game has been configured successfully!\n\n"
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

        author_id = message.author.id
        self.message_counts[author_id] = self.message_counts.get(author_id, 0) + 1

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
                    title="✨ Wrong Number!",
                    description=f"Oops {message.author.mention}, that's incorrect. Next correct number is: **{self.current_count}**",
                    color=discord.Color.orange()
                )
                await message.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        
        now = datetime.datetime.utcnow().timestamp()

        # User joined a VC
        if before.channel is None and after.channel is not None:
            self.vc_joins[member.id] = now

        # User left a VC
        elif before.channel is not None and after.channel is None:
            if member.id in self.vc_joins:
                duration = int(now - self.vc_joins[member.id])
                self.voice_time_seconds[member.id] = self.voice_time_seconds.get(member.id, 0) + duration
                del self.vc_joins[member.id]

    # Short & Direct Commands
    @commands.command(name="m")
    async def message_count(self, ctx):
        count = self.message_counts.get(ctx.author.id, 0)
        embed = create_embed(
            ctx.guild,
            title="💬 Message Count",
            description=f"You have sent **{count}** messages.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="v")
    async def voice_count(self, ctx):
        total_secs = self.voice_time_seconds.get(ctx.author.id, 0)
        # Agar user abhi bhi VC me hai toh live time bhi add kar do
        if ctx.author.id in self.vc_joins:
            total_secs += int(datetime.datetime.utcnow().timestamp() - self.vc_joins[ctx.author.id])

        formatted_time = format_time(total_secs)
        embed = create_embed(
            ctx.guild,
            title="🎙️ Voice Time",
            description=f"You have spent **{formatted_time}** in voice channels.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="i")
    async def invite_count(self, ctx):
        invites = self.invite_counts.get(ctx.author.id, 0)
        embed = create_embed(
            ctx.guild,
            title="✉️ Invite Count",
            description=f"You have successfully invited **{invites}** members.",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    # Leaderboards (`&lm`, `&lv`, `&li`)
    @commands.command(name="lm")
    async def leaderboard_messages(self, ctx):
        if not self.message_counts:
            embed = create_embed(ctx.guild, title="💬 Messages Leaderboard", description="No message data recorded yet.", color=discord.Color.blue())
            return await ctx.send(embed=embed)

        sorted_users = sorted(self.message_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        desc = ""
        for idx, (uid, count) in enumerate(sorted_users, 1):
            desc += f"`#{idx}` <@{uid}> — **{count}** messages\n"

        embed = create_embed(ctx.guild, title="💬 Messages Leaderboard", description=desc, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command(name="lv")
    async def leaderboard_voice(self, ctx):
        if not self.voice_time_seconds and not self.vc_joins:
            embed = create_embed(ctx.guild, title="🎙️ Voice Leaderboard", description="No voice time recorded yet.", color=discord.Color.green())
            return await ctx.send(embed=embed)

        # Calculate live times for active users
        current_data = self.voice_time_seconds.copy()
        now = datetime.datetime.utcnow().timestamp()
        for uid, join_time in self.vc_joins.items():
            current_data[uid] = current_data.get(uid, 0) + int(now - join_time)

        sorted_users = sorted(current_data.items(), key=lambda x: x[1], reverse=True)[:10]
        desc = ""
        for idx, (uid, secs) in enumerate(sorted_users, 1):
            desc += f"`#{idx}` <@{uid}> — **{format_time(secs)}**\n"

        embed = create_embed(ctx.guild, title="🎙️ Voice Time Leaderboard", description=desc, color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name="li")
    async def leaderboard_invites(self, ctx):
        if not self.invite_counts:
            embed = create_embed(ctx.guild, title="✉️ Invites Leaderboard", description="No invite data recorded yet.", color=discord.Color.purple())
            return await ctx.send(embed=embed)

        sorted_users = sorted(self.invite_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        desc = ""
        for idx, (uid, count) in enumerate(sorted_users, 1):
            desc += f"`#{idx}` <@{uid}> — **{count}** invites\n"

        embed = create_embed(ctx.guild, title="✉️ Invites Leaderboard", description=desc, color=discord.Color.purple())
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
