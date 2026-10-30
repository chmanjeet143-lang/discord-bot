import discord
from discord.ext import commands, tasks
import json
import os
import random
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp

CONFIG_FILE = "levels_config.json"

def load_data():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Level(commands.Cog, description="Explore all commands related to Leveling and XP system."):
    """Explore all commands related to Leveling system."""
    
    def __init__(self, bot):
        self.bot = bot
        self.vc_xp_loop.start()

    def cog_unload(self):
        self.vc_xp_loop.cancel()

    @commands.command(name="setmsgchannel", help="Set the channel for Message XP level-up notifications.")
    @commands.has_permissions(administrator=True)
    async def set_msg_channel(self, ctx, channel: discord.TextChannel = None):
        """Set message XP channel.
        Usage: &setmsgchannel #channel-name"""
        try:
            await ctx.message.delete()
        except:
            pass

        if not channel:
            embed = discord.Embed(
                title="⚙️ Message XP Channel",
                description="Set the channel where message level-up notifications will be sent.\n\n**Usage:**\n`&setmsgchannel #channel`",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, delete_after=5)

        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {"settings": {}, "users": {}}
        data[guild_id]["settings"]["msg_channel"] = channel.id
        save_data(data)

        embed = discord.Embed(
            description=f"✅ Message XP channel successfully set to {channel.mention}!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, delete_after=3)

    @commands.command(name="setvcchannel", help="Set the channel for Voice Chat (VC) XP notifications.")
    @commands.has_permissions(administrator=True)
    async def set_vc_channel(self, ctx, channel: discord.TextChannel = None):
        """Set VC XP channel.
        Usage: &setvcchannel #channel-name"""
        try:
            await ctx.message.delete()
        except:
            pass

        if not channel:
            embed = discord.Embed(
                title="🎙️ VC XP Channel",
                description="Set the channel where Voice Chat level-up notifications will be sent.\n\n**Usage:**\n`&setvcchannel #channel`",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, delete_after=5)

        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {"settings": {}, "users": {}}
        data[guild_id]["settings"]["vc_channel"] = channel.id
        save_data(data)

        embed = discord.Embed(
            description=f"✅ VC XP channel successfully set to {channel.mention}!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, delete_after=3)

    @commands.command(name="setmsglevelmsg", help="Set custom level-up announcement message for text messages.")
    @commands.has_permissions(administrator=True)
    async def set_msg_level_msg(self, ctx, *, message: str = None):
        """Set custom text level up message.
        Usage: &setmsglevelmsg Congrats {user} for Level {level}!"""
        try:
            await ctx.message.delete()
        except:
            pass

        if not message:
            embed = discord.Embed(
                title="⚙️ Custom Message Level-Up Text",
                description="Set custom message for **Text Message** level-ups.\n\n**Variables:** `{user}`, `{level}`, `{xp}`, `{server}`\n**Usage:**\n`&setmsglevelmsg Congrats {user} for Level {level}! Current XP: {xp}`",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, delete_after=5)

        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {"settings": {}, "users": {}}
        data[guild_id]["settings"]["msg_custom_msg"] = message
        save_data(data)

        embed = discord.Embed(
            description="✅ Text message level-up announcement updated successfully!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, delete_after=3)

    @commands.command(name="setvclevelmsg", help="Set custom level-up announcement message for voice chat.")
    @commands.has_permissions(administrator=True)
    async def set_vc_level_msg(self, ctx, *, message: str = None):
        """Set custom VC level up message.
        Usage: &setvclevelmsg VC Level Up {user} to Level {level}!"""
        try:
            await ctx.message.delete()
        except:
            pass

        if not message:
            embed = discord.Embed(
                title="⚙️ Custom Voice Level-Up Text",
                description="Set custom message for **Voice Chat (VC)** level-ups.\n\n**Variables:** `{user}`, `{level}`, `{xp}`, `{server}`\n**Usage:**\n`&setvclevelmsg VC Level Up {user} to Level {level}! Current XP: {xp}`",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, delete_after=5)

        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {"settings": {}, "users": {}}
        data[guild_id]["settings"]["vc_custom_msg"] = message
        save_data(data)

        embed = discord.Embed(
            description="✅ Voice chat level-up announcement updated successfully!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, delete_after=3)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        data = load_data()
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        if guild_id not in data:
            data[guild_id] = {"settings": {}, "users": {}}
        if "users" not in data[guild_id]:
            data[guild_id]["users"] = {}
        if user_id not in data[guild_id]["users"]:
            data[guild_id]["users"][user_id] = {"msg_xp": 0, "msg_level": 1, "vc_xp": 0, "vc_level": 1}

        xp_earned = random.randint(2, 4)
        user_data = data[guild_id]["users"][user_id]
        user_data["msg_xp"] += xp_earned

        next_level_xp = user_data["msg_level"] * 100
        if user_data["msg_xp"] >= next_level_xp:
            user_data["msg_level"] += 1
            user_data["msg_xp"] = 0

            settings = data[guild_id].get("settings", {})
            target_channel_id = settings.get("msg_channel", message.channel.id)
            target_channel = message.guild.get_channel(target_channel_id) or message.channel

            custom_msg = settings.get("msg_custom_msg", "🎉 Badhai ho {user}, aapka message level badhkar **Level {level}** ho gaya hai! (XP: {xp})")
            formatted_msg = custom_msg.format(
                user=message.author.mention,
                level=user_data["msg_level"],
                xp=user_data["msg_xp"],
                server=message.guild.name
            )
            embed = discord.Embed(description=formatted_msg, color=discord.Color.gold())
            try:
                await target_channel.send(embed=embed)
            except:
                pass

        save_data(data)

    @tasks.loop(minutes=1)
    async def vc_xp_loop(self):
        data = load_data()
        for guild_id, guild_info in data.items():
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            settings = guild_info.get("settings", {})
            users_data = guild_info.get("users", {})

            for vc in guild.voice_channels:
                active_members = [m for m in vc.members if not m.bot and not m.voice.self_deaf]
                if not active_members:
                    continue

                for member in active_members:
                    user_id = str(member.id)
                    if user_id not in users_data:
                        users_data[user_id] = {"msg_xp": 0, "msg_level": 1, "vc_xp": 0, "vc_level": 1}

                    vc_earned = 4
                    u_info = users_data[user_id]
                    u_info["vc_xp"] += vc_earned

                    next_vc_xp = u_info["vc_level"] * 100
                    if u_info["vc_xp"] >= next_vc_xp:
                        u_info["vc_level"] += 1
                        u_info["vc_xp"] = 0

                        target_channel_id = settings.get("vc_channel")
                        target_channel = guild.get_channel(target_channel_id) if target_channel_id else None

                        if target_channel:
                            custom_msg = settings.get("vc_custom_msg", "🎙️ Shandaar {user}! Aapka VC level badhkar **Level {level}** ho gaya hai! (XP: {xp})")
                            formatted_msg = custom_msg.format(
                                user=member.mention,
                                level=u_info["vc_level"],
                                xp=u_info["vc_xp"],
                                server=guild.name
                            )
                            embed = discord.Embed(description=formatted_msg, color=discord.Color.purple())
                            try:
                                await target_channel.send(embed=embed)
                            except:
                                pass

        save_data(data)

    @vc_xp_loop.before_loop
    async def before_vc_xp(self):
        await self.bot.wait_until_ready()

    @commands.command(name="leaderboard", help="Show the top members leaderboard.")
    async def leaderboard(self, ctx):
        """Show leaderboard.
        Usage: &leaderboard"""
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id].get("users"):
            embed = discord.Embed(description="❌ Is server par abhi koi level data available nahi hai!", color=discord.Color.red())
            return await ctx.send(embed=embed, delete_after=3)

        users_dict = data[guild_id]["users"]
        sorted_users = sorted(
            users_dict.items(),
            key=lambda x: (x[1]["msg_level"], x[1]["msg_xp"]),
            reverse=True
        )[:10]

        embed = discord.Embed(
            title=f"🏆 Server Leaderboard - {ctx.guild.name}",
            color=discord.Color.gold()
        )

        desc = ""
        for i, (user_id, info) in enumerate(sorted_users, start=1):
            user = ctx.guild.get_member(int(user_id))
            name = user.name if user else f"User ID: {user_id}"
            desc += f"**{i}.** {name} — Level: **{info['msg_level']}** (XP: {info['msg_xp']})\n"

        embed.description = desc
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Level(bot))
