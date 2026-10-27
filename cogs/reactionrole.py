import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "reaction_roles.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. Embed Message Command
    @commands.command(name="embed", help="Create and send an embed message.\nUsage: &embed Your message here")
    @commands.has_permissions(administrator=True)
    async def create_embed(self, ctx, *, message: str = None):
        try:
            await ctx.message.delete()
        except:
            pass

        if not message:
            embed = discord.Embed(
                title="📌 Embed Command",
                description="Create and send a clean embed message.\n\n**Usage:**\n`&embed Your message here`",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, delete_after=5)
        
        embed = discord.Embed(
            description=message,
            color=discord.Color.from_rgb(153, 45, 255)
        )
        await ctx.send(embed=embed)

    # 2. Add Reaction Role to Last Message (Auto-deletes command & bot msg after 2s)
    @commands.command(name="addrr", help="Add reaction role to the last message in the channel.\nUsage: &addrr @role 🎉")
    @commands.has_permissions(administrator=True)
    async def add_reaction_role_last(self, ctx, role: discord.Role = None, emoji: str = None):
        try:
            await ctx.message.delete()
        except:
            pass

        if not role or not emoji:
            embed = discord.Embed(
                title="🛡️ Reaction Role Command",
                description="Add reaction role to the last message in the channel.\n\n**Usage:**\n`&addrr @role 🎉`",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, delete_after=5)

        # Fetch last message in the channel (excluding the deleted command message)
        async for message in ctx.channel.history(limit=5):
            if message.id != ctx.message.id:
                target_msg = message
                break
        else:
            embed = discord.Embed(description="❌ No message found in history!", color=discord.Color.red())
            return await ctx.send(embed=embed, delete_after=3)

        config = load_config()
        guild_id = str(ctx.guild.id)
        msg_id = str(target_msg.id)

        if guild_id not in config:
            config[guild_id] = {}
        if "messages" not in config[guild_id]:
            config[guild_id]["messages"] = {}
        if msg_id not in config[guild_id]["messages"]:
            config[guild_id]["messages"][msg_id] = {}

        config[guild_id]["messages"][msg_id][emoji] = role.id
        save_config(config)

        try:
            await target_msg.add_reaction(emoji)
        except Exception as e:
            embed = discord.Embed(description=f"❌ Failed to add reaction: {e}", color=discord.Color.red())
            return await ctx.send(embed=embed, delete_after=3)

        embed = discord.Embed(
            description=f"✅ Reaction role successfully set!\n**Role:** {role.mention}\n**Emoji:** {emoji}",
            color=discord.Color.green()
        )
        # Deletes bot's confirmation message after 2 seconds
        await ctx.send(embed=embed, delete_after=2)

    # 3. User-Specific Reaction Role Command (`addrruser`)
    @commands.command(name="addrruser", help="Set up a reaction role for a specific user's messages.\nUsage: &addrruser @user @role 🎉")
    @commands.has_permissions(administrator=True)
    async def add_reaction_role_user(self, ctx, member: discord.Member = None, role: discord.Role = None, emoji: str = None):
        try:
            await ctx.message.delete()
        except:
            pass

        if not member or not role or not emoji:
            embed = discord.Embed(
                title="👤 User Reaction Role Command",
                description="Set reaction role for any message sent by a specific user.\n\n**Usage:**\n`&addrruser @user @role 🎉`",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, delete_after=5)

        config = load_config()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id not in config:
            config[guild_id] = {}
        if "users" not in config[guild_id]:
            config[guild_id]["users"] = {}

        config[guild_id]["users"][user_id] = {"role_id": role.id, "emoji": emoji}
        save_config(config)

        embed = discord.Embed(
            description=f"✅ User-specific reaction role set for {member.mention}!\n**Role:** {role.mention}\n**Emoji:** {emoji}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, delete_after=3)

    # 4. Remove User-Specific Reaction Role Command (`removerruser`)
    @commands.command(name="removerruser", help="Remove reaction role mapping for a specific user.\nUsage: &removerruser @user")
    @commands.has_permissions(administrator=True)
    async def remove_reaction_role_user(self, ctx, member: discord.Member = None):
        try:
            await ctx.message.delete()
        except:
            pass

        if not member:
            embed = discord.Embed(
                title="🗑️ Remove User Reaction Role",
                description="Remove reaction role configuration for a user.\n\n**Usage:**\n`&removerruser @user`",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, delete_after=5)

        config = load_config()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id in config and "users" in config[guild_id] and user_id in config[guild_id]["users"]:
            del config[guild_id]["users"][user_id]
            save_config(config)

            embed = discord.Embed(
                description=f"✅ Reaction role configuration removed for {member.mention}!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed, delete_after=3)
        else:
            embed = discord.Embed(
                description=f"❌ No reaction role configuration found for {member.mention}!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=3)

    # --- LISTENERS (Persistent & Safe across restarts) ---

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if not member or member.bot:
            return

        config = load_config()
        guild_id = str(payload.guild_id)
        msg_id = str(payload.message_id)
        emoji = str(payload.emoji)

        if guild_id in config:
            # 1. Check Message-based Reaction Roles
            messages_config = config[guild_id].get("messages", {})
            if msg_id in messages_config and emoji in messages_config[msg_id]:
                role_id = messages_config[msg_id][emoji]
                role = guild.get_role(role_id)
                if role:
                    try:
                        await member.add_roles(role)
                    except:
                        pass
                return

            # 2. Check User-specific Reaction Roles (`addrruser`)
            users_config = config[guild_id].get("users", {})
            if users_config:
                try:
                    channel = self.bot.get_channel(payload.channel_id) or await self.bot.fetch_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    author_id_str = str(message.author.id)
                    if author_id_str in users_config:
                        u_data = users_config[author_id_str]
                        if emoji == u_data["emoji"]:
                            role = guild.get_role(u_data["role_id"])
                            if role:
                                await member.add_roles(role)
                except:
                    pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not payload.guild_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if not member or member.bot:
            return

        config = load_config()
        guild_id = str(payload.guild_id)
        msg_id = str(payload.message_id)
        emoji = str(payload.emoji)

        if guild_id in config:
            # 1. Check Message-based Reaction Roles
            messages_config = config[guild_id].get("messages", {})
            if msg_id in messages_config and emoji in messages_config[msg_id]:
                role_id = messages_config[msg_id][emoji]
                role = guild.get_role(role_id)
                if role:
                    try:
                        await member.remove_roles(role)
                    except:
                        pass
                return

            # 2. Check User-specific Reaction Roles (`addrruser`)
            users_config = config[guild_id].get("users", {})
            if users_config:
                try:
                    channel = self.bot.get_channel(payload.channel_id) or await self.bot.fetch_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    author_id_str = str(message.author.id)
                    if author_id_str in users_config:
                        u_data = users_config[author_id_str]
                        if emoji == u_data["emoji"]:
                            role = guild.get_role(u_data["role_id"])
                            if role:
                                await member.remove_roles(role)
                except:
                    pass

async def setup(bot):
    await bot.add_cog(ReactionRole(bot))
