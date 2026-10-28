import discord
from discord.ext import commands
import aiosqlite
import json

class Jail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "jail.db"
        self.bot.loop.create_task(self.init_db())

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS jailed_users (
                    guild_id INTEGER,
                    user_id INTEGER,
                    roles TEXT,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            await db.commit()

    @commands.command(
        name="jail",
        help="Jails a member, strips their roles, and saves them to the database.\nUsage: !jail @user [reason]",
        brief="Jail a member"
    )
    @commands.has_permissions(manage_roles=True)
    async def jail(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member == ctx.author:
            embed = discord.Embed(
                title="❌ Action Denied",
                description="You cannot jail yourself!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        guild = ctx.guild
        
        jail_role = discord.utils.get(guild.roles, name="Jailed")
        if not jail_role:
            try:
                jail_role = await guild.create_role(name="Jailed", reason="Jail system setup")
                for channel in guild.channels:
                    await channel.set_permissions(jail_role, send_messages=False, speak=False, add_reactions=False)
            except discord.Forbidden:
                embed = discord.Embed(
                    title="❌ Permission Error",
                    description="I do not have permissions to create the 'Jailed' role or update channel permissions!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM jailed_users WHERE guild_id = ? AND user_id = ?", (guild.id, member.id)) as cursor:
                exists = await cursor.fetchone()
                if exists:
                    embed = discord.Embed(
                        title="⚠️ Already Jailed",
                        description=f"{member.mention} is already in jail!",
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=embed)
                    return

        user_roles = [role.id for role in member.roles if role != guild.default_role and not role.managed]

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO jailed_users (guild_id, user_id, roles) VALUES (?, ?, ?)",
                (guild.id, member.id, json.dumps(user_roles))
            )
            await db.commit()

        try:
            roles_to_remove = [r for r in member.roles if r != guild.default_role and not r.managed]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"Jailed by {ctx.author}: {reason}")
            await member.add_roles(jail_role, reason=reason)
            
            embed = discord.Embed(
                title="🔒 Member Jailed",
                description=f"**{member}** has been successfully jailed.",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Jailed by {ctx.author}")
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Hierarchy Error",
                description="My role must be higher than the member you are trying to jail!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(
        name="unjail",
        help="Releases a member from jail and restores their previous roles.\nUsage: !unjail @user",
        brief="Unjail a member"
    )
    @commands.has_permissions(manage_roles=True)
    async def unjail(self, ctx, member: discord.Member):
        guild = ctx.guild
        jail_role = discord.utils.get(guild.roles, name="Jailed")

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT roles FROM jailed_users WHERE guild_id = ? AND user_id = ?", (guild.id, member.id)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    embed = discord.Embed(
                        title="⚠️ Not Jailed",
                        description=f"{member.mention} is not currently in jail!",
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=embed)
                    return

                saved_role_ids = json.loads(row[0])

            await db.execute("DELETE FROM jailed_users WHERE guild_id = ? AND user_id = ?", (guild.id, member.id))
            await db.commit()

        try:
            if jail_role and jail_role in member.roles:
                await member.remove_roles(jail_role, reason="Unjailed")

            roles_to_add = [guild.get_role(r_id) for r_id in saved_role_ids if guild.get_role(r_id) is not None]
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Restored roles after unjail")

            embed = discord.Embed(
                title="🔓 Member Unjailed",
                description=f"**{member}** has been released from jail and their previous roles have been restored.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="Failed to restore roles due to role hierarchy limitations.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @jail.error
    @unjail.error
    async def jail_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You need the `Manage Roles` permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Invalid Syntax",
                description="Please follow the correct usage.\nExample: `!jail @user [reason]` or `!unjail @user`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Jail(bot))
