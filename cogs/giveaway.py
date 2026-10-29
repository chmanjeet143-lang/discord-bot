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

class GiveawayDMControlView(discord.ui.View):
    def __init__(self, cog, message_id_str):
        super().__init__(timeout=None)
        self.cog = cog
        self.message_id_str = message_id_str

    @discord.ui.button(label="Reroll", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="gw_dm_reroll")
    async def reroll_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.cog.active_giveaways.get(self.message_id_str)
        if not data:
            return await interaction.response.send_message("❌ This giveaway data is no longer active.", ephemeral=True)

        guild = self.cog.bot.get_guild(data["guild_id"])
        if not guild:
            return await interaction.response.send_message("❌ Guild not found.", ephemeral=True)

        try:
            channel = guild.get_channel(data["channel_id"])
            message = await channel.fetch_message(data["message_id"])
        except Exception:
            return await interaction.response.send_message("❌ Could not fetch the public giveaway message.", ephemeral=True)

        users = []
        for reaction in message.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        users.append(user.id)

        if not users:
            return await interaction.response.send_message("❌ No participants found to reroll.", ephemeral=True)

        winners_count = data["winners_count"]
        actual_winners_count = min(winners_count, len(users))
        new_winners = random.sample(users, actual_winners_count)
        data["current_winners"] = new_winners
        self.cog.save_giveaways()

        winners_mention = ", ".join([f"<@{w}>" for w in new_winners])
        await interaction.response.edit_message(content=f"🔄 **Rerolled!** New temporary winner selected: {winners_mention}.\nClick **Confirm** when you are ready to announce.", view=self)

    @discord.ui.button(label="Confirm Winner", style=discord.ButtonStyle.success, emoji="✅", custom_id="gw_dm_confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.cog.active_giveaways.get(self.message_id_str)
        if not data:
            return await interaction.response.send_message("❌ This giveaway data is no longer active.", ephemeral=True)

        guild = self.cog.bot.get_guild(data["guild_id"])
        if not guild:
            return await interaction.response.send_message("❌ Guild not found.", ephemeral=True)

        try:
            channel = guild.get_channel(data["channel_id"])
            message = await channel.fetch_message(data["message_id"])
        except Exception:
            return await interaction.response.send_message("❌ Could not fetch the public giveaway message.", ephemeral=True)

        winners = data.get("current_winners", [])
        if not winners:
            return await interaction.response.send_message("❌ No winner is currently selected.", ephemeral=True)

        winners_mention = ", ".join([f"<@{w}>" for w in winners])
        ended_time_str = datetime.datetime.fromtimestamp(data["end_time"], datetime.timezone.utc).strftime("%d/%m/%Y, %H:%M")
        users_count = data.get("total_participants", 0)

        # Update public message to final ended state (No buttons for normal members)
        embed = create_embed(
            guild,
            title="🎁 Giveaway Ended 🎁",
            description=(
                f"🎁 **{data['prize']}**\n\n"
                f"• Hosted by: <@{data['host_id']}>\n"
                f"• Total participant(s) : {users_count}\n\n"
                f"• **Winner :**\n{winners_mention}\n\n"
                f"Ended | {ended_time_str}"
            ),
            color=discord.Color.green()
        )

        try:
            await message.edit(embed=embed, view=None)
        except Exception:
            pass

        # Send public congratulations message in channel
        announcement = f"Congrats, {winners_mention} you have won **{data['prize']}**, hosted by <@{data['host_id']}>"
        try:
            await channel.send(content=announcement)
        except Exception:
            pass

        # Disable buttons in DM and clean up
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"✅ **Confirmed!** Winner {winners_mention} has been successfully announced publicly.", view=self)

        self.cog.active_giveaways.pop(self.message_id_str, None)
        self.cog.save_giveaways()


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
            if now >= data["end_time"] and not data.get("pending_confirmation", False):
                expired.append(msg_id_str)

        for msg_id_str in expired:
            data = self.active_giveaways[msg_id_str]
            data["pending_confirmation"] = True
            self.save_giveaways()
            await self.send_host_dm(data)

    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        await self.bot.wait_until_ready()

    async def send_host_dm(self, data):
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

        data["total_participants"] = len(users)
        prize = data["prize"]
        winners_count = data["winners_count"]

        if len(users) == 0:
            embed = message.embeds[0] if message.embeds else create_embed(guild)
            embed.title = "🎁 Giveaway Ended (No Entries) 🎁"
            embed.description = f"The giveaway for **{prize}** has ended, but unfortunately no one reacted to participate."
            embed.color = discord.Color.orange()
            try:
                await message.edit(embed=embed, view=None)
            except Exception:
                pass
            self.active_giveaways.pop(str(message.id), None)
            self.save_giveaways()
            return

        actual_winners_count = min(winners_count, len(users))
        winners = random.sample(users, actual_winners_count)
        data["current_winners"] = winners
        self.save_giveaways()

        winners_mention = ", ".join([f"<@{w}>" for w in winners])

        # Fetch Host Member to DM
        host = guild.get_member(data["host_id"])
        if not host:
            try:
                host = await guild.fetch_member(data["host_id"])
            except Exception:
                return

        view = GiveawayDMControlView(self, str(message.id))
        try:
            await host.send(
                content=f"🔔 **Giveaway Ended for: {prize}**\n"
                        f"• Total Participants: {len(users)}\n"
                        f"• Temporary Winner: {winners_mention}\n\n"
                        f"Zeus, please choose to **Reroll** or **Confirm** below:",
                view=view
            )
        except Exception:
            # Fallback if DMs are closed: send temporary notice in channel or handle gracefully
            pass

    @commands.command(
        name="gstart", 
        aliases=["giveaway"],
        help="Starts a new giveaway in the channel.\n\n**Example:** `&gstart 1h 1 50 RS`"
    )
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
            title="🎁 Giveaway Time! 🎁",
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
            "host_id": ctx.author.id,
            "end_time": end_time.timestamp(),
            "winners_count": winners_count,
            "prize": prize,
            "pending_confirmation": False
        }
        self.save_giveaways()

    @commands.command(
        name="reroll",
        help="Instantly rerolls a winner for a specific giveaway message ID.\n\n**Example:** `&reroll 123456789012345678`"
    )
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
