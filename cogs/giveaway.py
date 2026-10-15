import discord
from discord.ext import commands
import asyncio
import random
import datetime
import re

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

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

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = set()

    @discord.ui.button(label="🎉 Enter Giveaway", style=discord.ButtonStyle.success, custom_id="giveaway_join_button")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participants:
            await interaction.response.send_message("You have already entered this giveaway with love!", ephemeral=True)
        else:
            self.participants.add(interaction.user.id)
            await interaction.response.send_message(f"✨ Successfully entered the giveaway! Good luck, {interaction.user.mention}!", ephemeral=True)

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gstart", aliases=["giveaway"])
    @commands.has_permissions(manage_guild=True)
    async def gstart(self, ctx, duration: str, winners_count: int, *, prize: str):
        delta = parse_time(duration)
        if not delta:
            embed = create_embed(ctx.guild, title="🎉 Invalid Time Format", description="Please use a valid duration format like `10s`, `5m`, `2h`, or `1d`.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        end_time = datetime.datetime.utcnow() + delta
        end_timestamp = int(end_time.timestamp())

        embed = create_embed(
            ctx.guild,
            title="🎉 GIVEAWAY TIME! 🎉",
            description=f"Win an amazing prize crafted for our community members!\n\n"
                        f"🎁 **Prize:** **{prize}**\n"
                        f"👑 **Winners:** `{winners_count}`\n"
                        f"⏳ **Ends At:** <t:{end_timestamp}:R> (<t:{end_timestamp}:F>)\n"
                        f"hosted by: {ctx.author.mention}\n\n"
                        f"Click the **🎉 Enter Giveaway** button below to participate!",
            color=discord.Color.gold()
        )

        view = GiveawayView()
        message = await ctx.send(embed=embed, view=view)

        await asyncio.sleep(delta.total_seconds())

        # Fetch latest message state
        try:
            message = await ctx.channel.fetch_message(message.id)
        except:
            return

        participants = list(view.participants)
        if len(participants) == 0:
            embed.title = "🎉 GIVEAWAY ENDED (No Entries)"
            embed.description = f"The giveaway for **{prize}** has ended, but unfortunately no one participated."
            embed.color = discord.Color.orange()
            await message.edit(embed=embed, view=None)
            return

        actual_winners_count = min(winners_count, len(participants))
        winners = random.sample(participants, actual_winners_count)
        winners_mention = ", ".join([f"<@{w}>" for w in winners])

        embed.title = "🎉 GIVEAWAY ENDED 🎉"
        embed.description = (
            f"The giveaway for **{prize}** has concluded!\n\n"
            f"🏆 **Winner(s):** {winners_mention}\n"
            f"🎁 Congratulations! Please contact {ctx.author.mention} to claim your wonderful prize."
        )
        embed.color = discord.Color.green()
        await message.edit(embed=embed, view=None)

        # Announce winners in chat politely
        announcement = create_embed(
            ctx.guild,
            title="🎊 We Have Giveaway Winner(s)! 🎊",
            description=f"Congratulations to {winners_mention} for winning **{prize}**! Thank you to everyone who participated in **Moonlight Heaven**.",
            color=discord.Color.purple()
        )
        await ctx.send(content=winners_mention, embed=announcement)

    @commands.command(name="reroll")
    @commands.has_permissions(manage_guild=True)
    async def reroll(self, ctx, message_id: int):
        try:
            msg = await ctx.channel.fetch_message(message_id)
        except:
            embed = create_embed(ctx.guild, title="🎉 Error", description="Could not find a giveaway message with that ID in this channel.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        embed = create_embed(
            ctx.guild,
            title="🔄 Giveaway Rerolled!",
            description=f"A new winner has been selected for this giveaway! Check the original message pin or history.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
