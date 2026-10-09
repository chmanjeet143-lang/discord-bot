import discord
from discord.ext import commands
import asyncio

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

# Unified Embed Helper Function
def create_embed(ctx_or_user, title="", description="", color=0x2B2D31, thumbnail=None):
    avatar_url = thumbnail or getattr(ctx_or_user, 'display_avatar', None) and ctx_or_user.display_avatar.url or DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=avatar_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antinuke_active = {} # {guild_id: True/False}
        self.antiaddbot_active = {} # {guild_id: True/False}

    # --- SECURITY LISTENERS (Anti-Nuke & Anti-Add Bot) ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.bot:
            return
        guild = member.guild
        # Check if antiaddbot is enabled for this guild
        if self.antiaddbot_active.get(guild.id, True): # Default enabled
            try:
                # Check who added the bot using audit logs
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                    if entry.target.id == member.id:
                        adder = entry.user
                        # ONLY server owner is allowed. Even admins are restricted!
                        if adder.id != guild.owner_id:
                            await member.kick(reason="AntiAddBot Security: Only the true server owner can add bots!")
                            try:
                                embed = create_embed(
                                    guild.me,
                                    title="🛡️ Security Alert: Bot Blocked",
                                    description=f"❌ **{member.name}** was automatically kicked because unauthorized user **{adder.name}** added them. Only the true server owner can add bots!",
                                    color=0xED4245
                                )
                                await guild.system_channel.send(embed=embed)
                            except:
                                pass
            except Exception as e:
                print(f"AntiAddBot Error: {e}")

    # --- COMMANDS ---

    # 1. Lock Channel
    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock_channel(self, ctx, channel: discord.TextChannel = None):
        target_channel = channel or ctx.channel
        await target_channel.set_permissions(ctx.guild.default_role, send_messages=False)
        embed = create_embed(ctx.author, title="🔒 Channel Locked", description=f"Successfully locked {target_channel.mention} for everyone.")
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 2. Unlock Channel
    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx, channel: discord.TextChannel = None):
        target_channel = channel or ctx.channel
        await target_channel.set_permissions(ctx.guild.default_role, send_messages=True)
        embed = create_embed(ctx.author, title="🔓 Channel Unlocked", description=f"Successfully unlocked {target_channel.mention}.")
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 3. Hide Channel
    @commands.command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide_channel(self, ctx, channel: discord.TextChannel = None):
        target_channel = channel or ctx.channel
        await target_channel.set_permissions(ctx.guild.default_role, view_channel=False)
        embed = create_embed(ctx.author, title="👁️‍🗨️ Channel Hidden", description=f"Successfully hid {target_channel.mention} from members.")
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 4. Unhide Channel
    @commands.command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide_channel(self, ctx, channel: discord.TextChannel = None):
        target_channel = channel or ctx.channel
        await target_channel.set_permissions(ctx.guild.default_role, view_channel=True)
        embed = create_embed(ctx.author, title="👁️ Channel Unhidden", description=f"Successfully made {target_channel.mention} visible to members.")
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 5. Kick Member
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        embed = create_embed(ctx.author, title="👢 Member Kicked", description=f"Successfully kicked **{member.name}**.\n**Reason:** {reason}")
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 6. Ban Member
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        embed = create_embed(ctx.author, title="🔨 Member Banned", description=f"Successfully banned **{member.name}**.\n**Reason:** {reason}", color=0xED4245)
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 7. Mass Ban
    @commands.command(name="massban")
    @commands.has_permissions(administrator=True)
    async def mass_ban(self, ctx, *members: discord.Member):
        if not members:
            embed = create_embed(ctx.author, title="Error", description="❌ Please provide members to mass ban.", color=0xED4245)
            await ctx.send(embed=embed)
            return
        
        count = 0
        for member in members:
            try:
                await member.ban(reason="Mass ban executed by admin")
                count += 1
            except:
                pass
        
        embed = create_embed(ctx.author, title="🔨 Mass Ban Executed", description=f"Successfully banned **{count}** members.")
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 8. Warn Member
    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        embed = create_embed(ctx.author, title="⚠️ Member Warned", description=f"Successfully warned **{member.mention}**.\n**Reason:** {reason}")
        await ctx.send(embed=embed)
        try:
            await member.send(f"⚠️ You have been warned in **{ctx.guild.name}** for: {reason}")
        except:
            pass
        try: await ctx.message.delete()
        except: pass

    # 9. Mute Member
    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            try:
                muted_role = await ctx.guild.create_role(name="Muted")
                for channel in ctx.guild.channels:
                    await channel.set_permissions(muted_role, send_messages=False, speak=False)
            except Exception as e:
                embed = create_embed(ctx.author, title="Error", description=f"❌ Could not create 'Muted' role: {e}", color=0xED4245)
                await ctx.send(embed=embed)
                return

        await member.add_roles(muted_role, reason=reason)
        embed = create_embed(ctx.author, title="🔇 Member Muted", description=f"Successfully muted **{member.mention}**.\n**Reason:** {reason}")
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 10. Anti-Add-Bot Control (Only Owner can toggle or manage)
    @commands.command(name="antiaddbot")
    async def anti_add_bot(self, ctx, status: str):
        # Strict check: ONLY server owner can use this command
        if ctx.author.id != ctx.guild.owner_id:
            embed = create_embed(ctx.author, title="❌ Access Denied", description="Only the true **Server Owner** can configure the Anti-Add-Bot protection!", color=0xED4245)
            await ctx.send(embed=embed, delete_after=5)
            try: await ctx.message.delete()
            except: pass
            return

        if status.lower() == "on":
            self.antiaddbot_active[ctx.guild.id] = True
            embed = create_embed(ctx.author, title="🛡️ Anti-Add-Bot Enabled", description="Anti-Add-Bot protection is now **ON**. Only you (the server owner) can add new bots.")
        elif status.lower() == "off":
            self.antiaddbot_active[ctx.guild.id] = False
            embed = create_embed(ctx.author, title="⚠️ Anti-Add-Bot Disabled", description="Anti-Add-Bot protection is now **OFF**.", color=0xED4245)
        else:
            embed = create_embed(ctx.author, title="Error", description="❌ Please specify either `on` or `off` (e.g., `&antiaddbot on`).", color=0xED4245)
            
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 11. Anti-Nuke Control (Only Owner)
    @commands.command(name="antinuke")
    async def anti_nuke(self, ctx, status: str):
        if ctx.author.id != ctx.guild.owner_id:
            embed = create_embed(ctx.author, title="❌ Access Denied", description="Only the true **Server Owner** can configure Anti-Nuke protection!", color=0xED4245)
            await ctx.send(embed=embed, delete_after=5)
            try: await ctx.message.delete()
            except: pass
            return

        if status.lower() == "on":
            self.antinuke_active[ctx.guild.id] = True
            embed = create_embed(ctx.author, title="🛡️ Anti-Nuke Enabled", description="Anti-Nuke security system is now active.")
        elif status.lower() == "off":
            self.antinuke_active[ctx.guild.id] = False
            embed = create_embed(ctx.author, title="⚠️ Anti-Nuke Disabled", description="Anti-Nuke system is now **OFF**.", color=0xED4245)
        else:
            embed = create_embed(ctx.author, title="Error", description="❌ Please specify either `on` or `off`.", color=0xED4245)

        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

async def setup(bot):
    await bot.add_cog(Moderation(bot))
