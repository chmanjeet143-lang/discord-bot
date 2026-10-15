import discord
from discord.ext import commands
from datetime import timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. MUTE (Timeout) COMMAND
    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute_command(self, ctx, member: discord.Member, minutes: int = 10, *, reason: str = "No reason provided"):
        try:
            duration = timedelta(minutes=minutes)
            await member.timeout(duration, reason=reason)
            
            embed = discord.Embed(
                title="🔇 Member Muted",
                description=f"Successfully muted {member.mention}.\n⏳ **Duration:** {minutes} minutes\n📝 **Reason:** {reason}",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to mute member. Error: {e}")

    @mute_command.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Usage: `&mute @member [minutes] [reason]`")

    # 2. UNMUTE COMMAND
    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute_command(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        try:
            await member.timeout(None, reason=reason)
            
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"Successfully unmuted {member.mention}.\n📝 **Reason:** {reason}",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to unmute member. Error: {e}")

    @unmute_command.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Usage: `&unmute @member`")

    # 3. PURGE / CLEAR COMMAND
    @commands.command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    async def purge_command(self, ctx, limit: int = 10):
        try:
            # Command message khud delete ho jayega aur limit ke mutabiq msgs delete honge
            deleted = await ctx.channel.purge(limit=limit + 1)
            
            msg = await ctx.send(f"🧹 Successfully deleted **{len(deleted) - 1}** messages!")
            await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=3))
            try:
                await msg.delete()
            except:
                pass
        except Exception as e:
            await ctx.send(f"❌ Failed to purge messages. Error: {e}")

    @purge_command.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to manage messages!")

    # 4. KICK COMMAND
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_command(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"Successfully kicked **{member.name}**.\n📝 **Reason:** {reason}",
                color=discord.Color.red()
            )
            embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to kick member. Error: {e}")

    # 5. BAN COMMAND
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_command(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"Successfully banned **{member.name}**.\n📝 **Reason:** {reason}",
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to ban member. Error: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
