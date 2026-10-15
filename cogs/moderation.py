import discord
from discord.ext import commands
import datetime
import re
import json
import os

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

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = "warnings.json"
        self.load_warnings()

    def load_warnings(self):
        if os.path.exists(self.warnings_file):
            try:
                with open(self.warnings_file, "r") as f:
                    self.warnings_store = json.load(f)
            except Exception:
                self.warnings_store = {}
        else:
            self.warnings_store = {}

    def save_warnings(self):
        try:
            with open(self.warnings_file, "w") as f:
                json.dump(self.warnings_store, f, indent=4)
        except Exception as e:
            print(f"Error saving warnings: {e}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_command(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = create_embed(ctx.guild, title="🛡️ Permission Denied", description="You cannot ban a member who has an equal or higher role than you.", color=discord.Color.red())
            return await ctx.send(embed=embed)
        
        await member.ban(reason=reason)
        embed = create_embed(
            ctx.guild,
            title="🛡️ Member Banned",
            description=f"Successfully banned **{member}** from the server.\n\n📝 **Reason:** {reason}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban_command(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            embed = create_embed(
                ctx.guild,
                title="🛡️ Member Unbanned",
                description=f"Successfully unbanned **{user}**.\n\n📝 **Reason:** {reason}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception:
            embed = create_embed(ctx.guild, title="🛡️ Error", description="Could not find a banned user with that ID or they are already unbanned.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_command(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = create_embed(ctx.guild, title="🛡️ Permission Denied", description="You cannot kick a member who has an equal or higher role than you.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        await member.kick(reason=reason)
        embed = create_embed(
            ctx.guild,
            title="🛡️ Member Kicked",
            description=f"Successfully kicked **{member}** from the server.\n\n📝 **Reason:** {reason}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name="mute", aliases=["timeout"])
    @commands.has_permissions(moderate_members=True)
    async def mute_command(self, ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        delta = parse_time(duration)
        if not delta:
            embed = create_embed(ctx.guild, title="🛡️ Invalid Time Format", description="Please use a valid format like `10s` (seconds), `5m` (minutes), `2h` (hours), or `1d` (days).", color=discord.Color.red())
            return await ctx.send(embed=embed)

        try:
            await member.timeout(delta, reason=reason)
            embed = create_embed(
                ctx.guild,
                title="🛡️ Member Muted (Timeout)",
                description=f"Successfully timed out **{member.mention}** for **{duration}**.\n\n📝 **Reason:** {reason}",
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_embed(ctx.guild, title="🛡️ Error", description=f"An error occurred while attempting to timeout the member: {e}", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name="unmute", aliases=["untimeout"])
    @commands.has_permissions(moderate_members=True)
    async def unmute_command(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        try:
            await member.timeout(None, reason=reason)
            embed = create_embed(
                ctx.guild,
                title="🛡️ Member Unmuted",
                description=f"Successfully removed timeout for **{member.mention}**.\n\n📝 **Reason:** {reason}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_embed(ctx.guild, title="🛡️ Error", description=f"Could not remove timeout: {e}", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn_command(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        if guild_id not in self.warnings_store:
            self.warnings_store[guild_id] = {}
        if user_id not in self.warnings_store[guild_id]:
            self.warnings_store[guild_id][user_id] = []
            
        self.warnings_store[guild_id][user_id].append(reason)
        self.save_warnings()
        total_warns = len(self.warnings_store[guild_id][user_id])

        embed = create_embed(
            ctx.guild,
            title="⚠️ Member Warned",
            description=f"Successfully warned **{member.mention}**.\n\n📝 **Reason:** {reason}\n📊 **Total Warnings:** {total_warns}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name="warnings")
    @commands.has_permissions(manage_messages=True)
    async def warnings_command(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        warns = self.warnings_store.get(guild_id, {}).get(user_id, [])
        
        if not warns:
            embed = create_embed(ctx.guild, title="⚠️ Warnings Record", description=f"**{member}** has no active warnings. Clean record!", color=discord.Color.green())
            return await ctx.send(embed=embed)

        warn_list = "\n".join([f"{idx}. {reason}" for idx, reason in enumerate(warns, 1)])
        embed = create_embed(
            ctx.guild,
            title=f"⚠️ Warnings for {member}",
            description=f"Here is the warning history:\n\n{warn_list}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name="clear", aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    async def clear_command(self, ctx, amount: int = 5):
        if amount > 100:
            amount = 100
        deleted = await ctx.channel.purge(limit=amount + 1)
        embed = create_embed(
            ctx.guild,
            title="🧹 Messages Cleared",
            description=f"Successfully cleaned up **{len(deleted) - 1}** messages from this channel with care.",
            color=discord.Color.blue()
        )
        msg = await ctx.send(embed=embed)
        await discord.utils.sleep_until(datetime.datetime.utcnow() + datetime.timedelta(seconds=3))
        try:
            await msg.delete()
        except:
            pass

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode_command(self, ctx, seconds: int = 0):
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            embed = create_embed(ctx.guild, title="⏳ Slowmode Disabled", description="Slowmode has been disabled for this channel.", color=discord.Color.green())
        else:
            embed = create_embed(ctx.guild, title="⏳ Slowmode Updated", description=f"Channel slowmode has been set to **{seconds} seconds**.", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command(name="lock", aliases=["lockdown"])
    @commands.has_permissions(manage_channels=True)
    async def lock_command(self, ctx, channel: discord.TextChannel = None):
        target_channel = channel or ctx.channel
        await target_channel.set_permissions(ctx.guild.default_role, send_messages=False)
        embed = create_embed(
            ctx.guild,
            title="🔒 Channel Locked",
            description=f"Successfully locked {target_channel.mention}. Normal members can no longer send messages here.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock_command(self, ctx, channel: discord.TextChannel = None):
        target_channel = channel or ctx.channel
        await target_channel.set_permissions(ctx.guild.default_role, send_messages=True)
        embed = create_embed(
            ctx.guild,
            title="🔓 Channel Unlocked",
            description=f"Successfully unlocked {target_channel.mention}. Normal members can now send messages again.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
