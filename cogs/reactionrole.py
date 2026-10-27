import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "reaction_roles.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. Embed Message banane ka command
    @commands.command(name="embed", help="Create and send an embed message.")
    @commands.has_permissions(administrator=True)
    async def create_embed(self, ctx, *, message: str):
        """Create and send an embed message.
        Usage: &embed Your message here"""
        await ctx.message.delete() # Command message delete karna
        
        embed = discord.Embed(
            description=message,
            color=discord.Color.from_rgb(153, 45, 255)
        )
        await ctx.send(embed=embed)

    # 2. Last message (embed/text) par reaction role lagane ka command
    @commands.command(name="addrr", help="Add reaction role to the last message in the channel.")
    @commands.has_permissions(administrator=True)
    async def add_reaction_role_last(self, ctx, role: discord.Role, emoji: str):
        """Add reaction role to the last message in the channel.
        Usage: &addrr @role 🎉"""
        
        # Channel ka last message fetch karna (command message ke alawa)
        async for message in ctx.channel.history(limit=2):
            if message.id != ctx.message.id:
                target_msg = message
                break
        else:
            await ctx.send("❌ Koi message nahi mila!")
            return

        config = load_config()
        guild_id = str(ctx.guild.id)
        msg_id = str(target_msg.id)

        if guild_id not in config:
            config[guild_id] = {}
        if msg_id not in config[guild_id]:
            config[guild_id][msg_id] = {}

        config[guild_id][msg_id][emoji] = role.id
        save_config(config)

        try:
            await target_msg.add_reaction(emoji)
        except Exception:
            pass

        embed = discord.Embed(
            description=f"✅ Last message par reaction role successfully set ho gaya hai!\n**Role:** {role.mention}\n**Emoji:** {emoji}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, delete_after=5)

    # 3. User specific reaction role add karne ka command
    @commands.command(name="addrruser", help="Set up a reaction role mapping for a specific user.")
    @commands.has_permissions(administrator=True)
    async def add_reaction_role_user(self, ctx, member: discord.Member, role: discord.Role, emoji: str):
        """Set up a reaction role for a user tag.
        Usage: &addrruser @user @role 🎉"""
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
            description=f"✅ User {member.mention} ke liye reaction role set kar diya gaya hai!\n**Role:** {role.mention}\n**Emoji:** {emoji}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    # 4. User specific reaction role hatane ka command
    @commands.command(name="removerruser", help="Remove reaction role mapping for a specific user.")
    @commands.has_permissions(administrator=True)
    async def remove_reaction_role_user(self, ctx, member: discord.Member):
        """Remove reaction role for a user.
        Usage: &removerruser @user"""
        config = load_config()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id in config and "users" in config[guild_id] and user_id in config[guild_id]["users"]:
            del config[guild_id]["users"][user_id]
            save_config(config)

            embed = discord.Embed(
                description=f"✅ User {member.mention} ka reaction role configuration hata diya gaya hai!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description=f"❌ User {member.mention} ke liye koi reaction role configuration nahi mila!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    # Listener: Reaction Add hone par role dena
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member and payload.member.bot:
            return
        
        config = load_config()
        guild_id = str(payload.guild_id)
        msg_id = str(payload.message_id)
        emoji = str(payload.emoji)

        if guild_id in config:
            # Message based reaction roles check
            if msg_id in config[guild_id] and emoji in config[guild_id][msg_id]:
                role_id = config[guild_id][msg_id][emoji]
                guild = self.bot.get_guild(payload.guild_id)
                if guild:
                    role = guild.get_role(role_id)
                    member = guild.get_member(payload.user_id)
                    if role and member:
                        await member.add_roles(role)

    # Listener: Reaction Remove hone par role hatana
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        config = load_config()
        guild_id = str(payload.guild_id)
        msg_id = str(payload.message_id)
        emoji = str(payload.emoji)

        if guild_id in config:
            if msg_id in config[guild_id] and emoji in config[guild_id][msg_id]:
                role_id = config[guild_id][msg_id][emoji]
                guild = self.bot.get_guild(payload.guild_id)
                if guild:
                    role = guild.get_role(role_id)
                    member = guild.get_member(payload.user_id)
                    if role and member and not member.bot:
                        await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(ReactionRole(bot))
