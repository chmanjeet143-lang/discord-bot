import discord
from discord.ext import commands, tasks
import asyncio
import random
import datetime
import re
import json
import os

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"
TICKET_CHANNEL_ID = 1533539817332281495  # Support ticket channel tag
GIVEAWAY_FILE = "giveaways.json"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

def parse_time(time_str: str):
    time_regex = re.compile(r"^(\d+)([smhd])$")
    match = time_regex.match(time_str.lower())
    if not match:
        return None
    amount, unit = int(match.group(1)), match.group(2)
    if unit == "s":
        return datetime.timedelta(seconds=amount)
    elif unit == "m":
        return datetime.timedelta(minutes=amount)
    elif unit == "h":
        return datetime.timedelta(hours=amount)
    elif unit == "d":
        return datetime.timedelta(days=amount)
    return None

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}
        self.load_giveaways()
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    def load_giveaways(self):
        if os.path.exists(GIVEAWAY_FILE):
            try:
                with open(GIVEAWAY_FILE, "r") as f:
                    self.active_giveaways = json.load(f)
            except Exception:
                self.active_giveaways = {}
        else:
            self.active_giveaways = {}

    def save_giveaways(self):
        try:
            with open(GIVEAWAY_FILE, "w") as f:
                json.dump(self.active_giveaways, f, indent=4)
        except Exception as e:
            print(f"Error saving giveaways: {e}")

    @tasks.loop(seconds=15)
    async def check_giveaways(self):
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        expired = []
        
        for msg_id_str, data in list(self.active_giveaways.items()):
            if now >= data["end_time"]:
                expired.append(msg_id_str)

        for msg_id_str in expired:
            data = self.active_giveaways.pop(msg_id_str, None)
            if data:
                self.save_giveaways()
                await self.end_giveaway_task(data)

    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        await self.bot.wait_until_ready()

    async def end_giveaway_task(self, data):
        guild = self.bot.get_guild(data["guild_id"])
        if not guild:
            return
        channel = guild.get_channel(data["channel_id"])
        if not channel:
            return

        try:
            message = await channel.fetch_message(data["message_id"])
        except Exception:
            return

        users = []
        for reaction in message.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        users.append(user.id)

        prize = data["prize"]
        winners_count = data["winners_count"]

        if len(users) == 0:
            embed = message.embeds[0] if message.embeds else create_embed(guild)
            embed.title = "🎉 GIVEAWAY ENDED (No Entries)"
            embed.description = f"The giveaway for **{prize}** has ended, but unfortunately no one reacted to participate."
            embed.color = discord.Color.orange()
            try:
                await message.edit(embed=embed)
            except Exception:
                pass
            return

        actual_winners_count = min(winners_count, len(users))
        winners = random.sample(users, actual_winners_count)
        winners_mention = ", ".join([f"<@{w}>" for w in winners])

        embed = message.embeds[0] if message.embeds else create_embed(guild)
        embed.title = "🎉 GIVEAWAY ENDED 🎉"
        embed.description = (
            f"The giveaway for **{prize}** has concluded!\n\n"
            f"🏆 **Winner(s):** {winners_mention}\n"
            f"🎁 Congratulations! Please go to <#{TICKET_CHANNEL_ID}> and open a support ticket to claim your wonderful prize."
        )
        embed.color = discord.Color.green()
        
        try:
            await message.edit(embed=embed)
        except Exception:
            pass

        announcement = create_embed(
            guild,
            title="🎊 We Have Giveaway Winner(s)! 🎊",
            description=f"Congratulations to {winners_mention} for winning **{prize}**!\n\n🎟️ Please head over to <#{TICKET_CHANNEL_ID}> to open a ticket and claim your prize.",
            color=discord.Color.purple()
        )
        try:
            await channel.send(content=winners_mention, embed=announcement)
        except Exception:
            pass

    @commands.command(name="gstart", aliases=["giveaway"])
    @commands.has_permissions(manage_guild=True)
    async def gstart(self, ctx, duration: str, winners_count: int, *, prize: str):
        delta = parse_time(duration)
        if not delta:
            embed = create_embed(ctx.guild, title="🎉 Invalid Time Format", description="Please use a valid duration format like `10s`, `5m`, `2h`, or `1d`.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        end_time = datetime.datetime.now(datetime.timezone.utc) + delta
        end_timestamp = int(end_time.timestamp())

        embed = create_embed(
            ctx.guild,
            title="🎉 GIVEAWAY TIME! 🎉",
            description=f"Win an amazing prize crafted for our community members!\n\n"
                        f"🎁 **Prize:** **{prize}**\n"
                        f"👑 **Winners:** `{winners_count}`\n"
                        f"⏳ **Ends At:** <t:{end_timestamp}:R> (<t:{end_timestamp}:F>)\n"
                        f"Hosted by: {ctx.author.mention}\n\n"
                        f"React with 🎉 below to enter the giveaway!",
            color=discord.Color.gold()
        )

        message = await ctx.send(embed=embed)
        await message.add_reaction("🎉")

        self.active_giveaways[str(message.id)] = {
            "message_id": message.id,
            "channel_id": ctx.channel.id,
            "guild_id": ctx.guild.id,
            "end_time": end_time.timestamp(),
            "winners_count": winners_count,
            "prize": prize
        }
        self.save_giveaways()

    @commands.command(name="reroll")
    @commands.has_permissions(manage_guild=True)
    async def reroll(self, ctx, message_id: int):
        try:
            msg = await ctx.channel.fetch_message(message_id)
        except Exception:
            embed = create_embed(ctx.guild, title="🎉 Error", description="Could not find a giveaway message with that ID in this channel.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        users = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        users.append(user.id)

        if not users:
            embed = create_embed(ctx.guild, title="🔄 Reroll Failed", description="No valid participants found on that message to reroll.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        new_winner = random.choice(users)
        winner_mention = f"<@{new_winner}>"

        embed = create_embed(
            ctx.guild,
            title="🔄 Giveaway Rerolled!",
            description=f"A new winner has been selected: {winner_mention}!\n\n🎟️ Please head over to <#{TICKET_CHANNEL_ID}> to claim your prize.",
            color=discord.Color.blue()
        )
        await ctx.send(content=winner_mention, embed=embed)

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
