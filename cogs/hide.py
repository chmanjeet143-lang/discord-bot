import discord
from discord.ext import commands, tasks
import asyncio
import typing
import json
import os
from datetime import datetime

class MoonlightHeavenControlPanel(commands.Cog):
    """Hidden master control panel and high-security management system."""
    
    def __init__(self, bot):
        self.bot = bot
        if not self.auto_backup_loop.is_running():
            self.auto_backup_loop.start()

    def cog_unload(self):
        self.auto_backup_loop.cancel()

    # --- Error Handler for this Cog ---
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Arguments",
                description=f"Aapne zaroori details nahi di hain!\n**Error:** `{error}`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=7)
        else:
            embed = discord.Embed(
                title="⚠️ Command Error",
                description=f"Kuch technical issue aa gaya hai:\n```py\n{error}\n```",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)

    # ==========================================
    # 1. SECRET CONTROL PANEL COMMAND (&hide)
    # ==========================================
    @commands.command(name="hide", hidden=True, help="Opens the secret master control panel (Admins only).")
    @commands.has_permissions(administrator=True)
    async def hide_command(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass

        embed = discord.Embed(
            title="🛡️ Moonlight Heaven • Secret Control Panel",
            description="Welcome to the high-security master management menu. This panel auto-deletes in **5 seconds** for security.",
            color=discord.Color.from_rgb(20, 24, 33)
        )
        
        embed.add_field(
            name="📩 Smart DM System",
            value="`&dm @user <msg>` - Send a DM to a specific user.\n`&dm @Role <msg>` - Send a bulk DM to all non-bot role members.\n*Permissions: Administrator Only*",
            inline=False
        )
        
        embed.add_field(
            name="🎧 VC Role System",
            value="Automatic background listener: Assigns a designated VC role when members join any voice channel and removes it instantly when they leave.",
            inline=False
        )
        
        embed.add_field(
            name="💾 Backup & Restore System",
            value="`&backup` - Take an instant manual backup of channels, roles, and permissions.\n`&restore` - Safely rebuilds and restores the server state within rate limits.\n*(Background auto-backup runs every 6 hours automatically)*",
            inline=False
        )
        
        embed.add_field(
            name="🚨 Anti-Nuke Security",
            value="Active 24/7 (No toggle). If any non-owner admin adds an unauthorized bot to the server, their administrator permissions are instantly stripped.",
            inline=False
        )
        
        embed.set_footer(text="Moonlight Heaven • Secure Modular Architecture")
        
        sent_msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        try:
            await sent_msg.delete()
        except:
            pass

    # ==========================================
    # 2. FLEXIBLE DM COMMAND (&dm)
    # ==========================================
    @commands.command(name="dm", help="Send a DM to a user or all members of a role.\n\n**Example:** &dm @username Hello! OR &dm @RoleName Announcement!")
    @commands.has_permissions(administrator=True)
    async def dm_command(self, ctx, target: typing.Union[discord.Member, discord.Role], *, message: str):
        try:
            await ctx.message.delete()
        except:
            pass

        if isinstance(target, discord.Member):
            try:
                await target.send(message)
                await ctx.send(f"✅ Successfully **{target.display_name}** ke DM mein message bhej diya gaya hai!", delete_after=5)
            except discord.Forbidden:
                await ctx.send(f"❌ **{target.display_name}** ko DM nahi bheja ja saka, shayad unke DMs band hain.", delete_after=5)
            except Exception as e:
                await ctx.send(f"❌ Kuch error aa gaya: {e}", delete_after=5)

        elif isinstance(target, discord.Role):
            success_count = 0
            fail_count = 0
            
            progress_msg = await ctx.send(f"⏳ **{target.name}** role ke members ko DMs bheje ja rahe ہیں...")

            for member in target.members:
                if member.bot:
                    continue
                try:
                    await member.send(message)
                    success_count += 1
                except:
                    fail_count += 1

            try:
                await progress_msg.delete()
            except:
                pass

            await ctx.send(f"✅ Role **{target.name}** ke liye DM process poori ho gayi!\n• Successful: {success_count}\n• Failed (DMs closed/Blocked): {fail_count}", delete_after=10)

    # ==========================================
    # 3. VC ROLE SYSTEM (Auto Join/Leave)
    # ==========================================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        guild = member.guild
        role_name = "In VC"
        
        vc_role = discord.utils.get(guild.roles, name=role_name)
        if not vc_role:
            try:
                vc_role = await guild.create_role(name=role_name, reason="Automatic VC Role system setup")
            except:
                return

        if before.channel is None and after.channel is not None:
            try:
                if vc_role not in member.roles:
                    await member.add_roles(vc_role, reason="Member joined a voice channel")
            except:
                pass

        elif before.channel is not None and after.channel is None:
            try:
                if vc_role in member.roles:
                    await member.remove_roles(vc_role, reason="Member left voice channels")
            except:
                pass

    # ==========================================
    # 4. BACKUP & RESTORE SYSTEM
    # ==========================================
    async def perform_backup(self, guild):
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "roles": [],
            "categories": [],
            "channels": []
        }

        for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
            if role.is_default() or role.managed:
                continue
            backup_data["roles"].append({
                "name": role.name,
                "color": role.color.value,
                "permissions": role.permissions.value,
                "hoist": role.hoist,
                "mentionable": role.mentionable,
                "position": role.position
            })

        for category in guild.categories:
            cat_data = {
                "name": category.name,
                "position": category.position,
                "channels": []
            }
            for channel in category.text_channels:
                cat_data["channels"].append({
                    "name": channel.name,
                    "type": "text",
                    "topic": channel.topic,
                    "slowmode": channel.slowmode_delay,
                    "nsfw": channel.nsfw,
                    "position": channel.position
                })
            for channel in category.voice_channels:
                cat_data["channels"].append({
                    "name": channel.name,
                    "type": "voice",
                    "bitrate": channel.bitrate,
                    "user_limit": channel.user_limit,
                    "position": channel.position
                })
            backup_data["categories"].append(cat_data)

        uncat_data = {"name": "Uncategorized", "position": 0, "channels": []}
        for channel in guild.text_channels:
            if channel.category is None:
                uncat_data["channels"].append({
                    "name": channel.name,
                    "type": "text",
                    "topic": channel.topic,
                    "slowmode": channel.slowmode_delay,
                    "nsfw": channel.nsfw,
                    "position": channel.position
                })
        for channel in guild.voice_channels:
            if channel.category is None:
                uncat_data["channels"].append({
                    "name": channel.name,
                    "type": "voice",
                    "bitrate": channel.bitrate,
                    "user_limit": channel.user_limit,
                    "position": channel.position
                })
        if uncat_data["channels"]:
            backup_data["categories"].append(uncat_data)

        filename = f"backup_{guild.id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=4)
        return filename

    @commands.command(name="backup", help="Create an instant server backup.")
    @commands.has_permissions(administrator=True)
    async def backup_cmd(self, ctx):
        await ctx.message.delete()
        msg = await ctx.send("⏳ Server ka backup liya ja raha hai...")
        try:
            await self.perform_backup(ctx.guild)
            await msg.edit(content="✅ Server backup successfully create ho gaya hai!")
            await asyncio.sleep(5)
            await msg.delete()
        except Exception as e:
            await msg.edit(content=f"❌ Backup lene mein error aaya: {e}")

    @tasks.loop(hours=6)
    async def auto_backup_loop(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                await self.perform_backup(guild)
            except:
                pass

    @commands.command(name="restore", help="Safely restore server structure from the latest backup (rate-limit safe).")
    @commands.has_permissions(administrator=True)
    async def restore_cmd(self, ctx):
        await ctx.message.delete()
        filename = f"backup_{ctx.guild.id}.json"
        if not os.path.exists(filename):
            await ctx.send("❌ Koi backup file nahi mili! Pehle `&backup` run karein.", delete_after=5)
            return

        msg = await ctx.send("🔄 Server restore process shuru ho chuki hai...")
        
        try:
            with open(filename, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            guild = ctx.guild

            for r_data in backup_data.get("roles", []):
                existing_role = discord.utils.get(guild.roles, name=r_data["name"])
                if not existing_role:
                    try:
                        await guild.create_role(
                            name=r_data["name"],
                            color=discord.Color(r_data["color"]),
                            permissions=discord.Permissions(r_data["permissions"]),
                            hoist=r_data["hoist"],
                            mentionable=r_data["mentionable"],
                            reason="Server restoration tool"
                        )
                        await asyncio.sleep(1.5)
                    except:
                        pass

            for cat_data in backup_data.get("categories", []):
                category = discord.utils.get(guild.categories, name=cat_data["name"])
                if not category:
                    try:
                        category = await guild.create_category(name=cat_data["name"], reason="Server restoration tool")
                        await asyncio.sleep(1.5)
                    except:
                        pass

                for ch_data in cat_data.get("channels", []):
                    existing_ch = discord.utils.get(guild.channels, name=ch_data["name"])
                    if not existing_ch:
                        try:
                            if ch_data["type"] == "text":
                                await guild.create_text_channel(
                                    name=ch_data["name"],
                                    category=category,
                                    topic=ch_data.get("topic"),
                                    slowmode_delay=ch_data.get("slowmode", 0),
                                    nsfw=ch_data.get("nsfw", False),
                                    reason="Server restoration tool"
                                )
                            elif ch_data["type"] == "voice":
                                await guild.create_voice_channel(
                                    name=ch_data["name"],
                                    category=category,
                                    bitrate=ch_data.get("bitrate", 64000),
                                    user_limit=ch_data.get("user_limit", 0),
                                    reason="Server restoration tool"
                                )
                            await asyncio.sleep(1.5)
                        except:
                            pass

            await msg.edit(content="✅ Server successfully restore aur fix kar diya gaya hai!")
            await asyncio.sleep(7)
            await msg.delete()
        except Exception as e:
            await msg.edit(content=f"❌ Restore karne mein error aaya: {e}")

    # ==========================================
    # 5. ANTI-NUKE SECURITY (Bot Add Monitor)
    # ==========================================
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.bot:
            return

        guild = member.guild
        try:
            await asyncio.sleep(2)
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id:
                    adder = entry.user
                    if adder.id != guild.owner_id:
                        for role in adder.roles:
                            if role.permissions.administrator or role.permissions.manage_guild or role.permissions.ban_members:
                                try:
                                    await adder.remove_roles(role, reason="Anti-Nuke: Unauthorized bot addition detected.")
                                except:
                                    pass
                        
                        if guild.system_channel:
                            try:
                                await guild.system_channel.send(
                                    f"🚨 **ANTI-NUKE TRIGGERED!**\n"
                                    f"• Unauthorized Bot Added: {member.mention}\n"
                                    f"• Added By: {adder.mention} (Not Server Owner)\n"
                                    f"• Action Taken: Administrative roles stripped instantly!"
                                )
                            except:
                                pass
                    break
        except Exception as e:
            print(f"Anti-Nuke Audit Log Error: {e}")

async def setup(bot):
    await bot.add_cog(MoonlightHeavenControlPanel(bot))
