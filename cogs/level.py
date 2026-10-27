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
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class AdvancedLeveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_xp_loop.start()

    def cog_unload(self):
        self.vc_xp_loop.cancel()

    @commands.command(name="setmsgchannel", help="Set the channel for Message XP.")
    @commands.has_permissions(administrator=True)
    async def set_msg_channel(self, ctx, channel: discord.TextChannel):
        """Set message XP channel.
        Usage: &setmsgchannel #channel-name"""
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {"settings": {}, "users": {}}
        data[guild_id]["settings"]["msg_channel"] = channel.id
        save_data(data)
        await ctx.send(f"✅ Message XP channel successfully set to {channel.mention}!")

    @commands.command(name="setvcchannel", help="Set the channel for VC XP.")
    @commands.has_permissions(administrator=True)
    async def set_vc_channel(self, ctx, channel: discord.TextChannel):
        """Set VC XP channel.
        Usage: &setvcchannel #channel-name"""
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {"settings": {}, "users": {}}
        data[guild_id]["settings"]["vc_channel"] = channel.id
        save_data(data)
        await ctx.send(f"✅ VC XP channel successfully set to {channel.mention}!")

    @commands.command(name="setlevelmsg", help="Set a custom level-up message.")
    @commands.has_permissions(administrator=True)
    async def set_level_msg(self, ctx, *, message: str):
        """Set custom level up message.
        Usage: &setlevelmsg Congrats {user} for reaching level {level}!"""
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {"settings": {}, "users": {}}
        data[guild_id]["settings"]["custom_msg"] = message
        save_data(data)
        await ctx.send("✅ Custom level-up message updated successfully!")

    @commands.command(name="setrankbg", help="Set a custom background image URL for your VIP rank card.")
    async def set_rank_bg(self, ctx, url: str):
        """Set custom rank card background.
        Usage: &setrankbg https://image-url.com/bg.png"""
        data = load_data()
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        if guild_id not in data:
            data[guild_id] = {"settings": {}, "users": {}}
        if "users" not in data[guild_id]:
            data[guild_id]["users"] = {}
        if user_id not in data[guild_id]["users"]:
            data[guild_id]["users"][user_id] = {"msg_xp": 0, "msg_level": 1, "vc_xp": 0, "vc_level": 1}
        
        data[guild_id]["users"][user_id]["custom_bg"] = url
        save_data(data)
        await ctx.send("✅ Aapka VIP rank card background successfully set ho gaya hai!")

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

            custom_msg = settings.get("custom_msg", "🎉 Badhai ho {user}, aapka message level badhkar **Level {level}** ho gaya hai!")
            formatted_msg = custom_msg.format(
                user=message.author.mention,
                level=user_data["msg_level"],
                server=message.guild.name
            )
            await target_channel.send(formatted_msg)

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
                if len(active_members) < 2:
                    continue

                for member in active_members:
                    user_id = str(member.id)
                    if user_id not in users_data:
                        users_data[user_id] = {"msg_xp": 0, "msg_level": 1, "vc_xp": 0, "vc_level": 1}

                    vc_earned = random.randint(1, 2)
                    u_info = users_data[user_id]
                    u_info["vc_xp"] += vc_earned

                    next_vc_xp = u_info["vc_level"] * 100
                    if u_info["vc_xp"] >= next_vc_xp:
                        u_info["vc_level"] += 1
                        u_info["vc_xp"] = 0

                        target_channel_id = settings.get("vc_channel")
                        target_channel = guild.get_channel(target_channel_id) if target_channel_id else None

                        if target_channel:
                            custom_msg = settings.get("custom_msg", "🎙️ Shandaar {user}! Aapka VC level badhkar **Level {level}** ho gaya hai!")
                            formatted_msg = custom_msg.format(
                                user=member.mention,
                                level=u_info["vc_level"],
                                server=guild.name
                            )
                            await target_channel.send(formatted_msg)

        save_data(data)

    @vc_xp_loop.before_loop
    async def before_vc_xp(self):
        await self.bot.wait_until_ready()

    @commands.command(name="rank", help="Check your VIP rank card with custom background.")
    async def rank(self, ctx, member: discord.Member = None):
        """Check your VIP rank card.
        Usage: &rank @username"""
        member = member or ctx.author
        data = load_data()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id not in data or user_id not in data[guild_id].get("users", {}):
            await ctx.send("❌ Is user ka koi level data nahi mila!")
            return

        u_info = data[guild_id]["users"][user_id]
        bg_url = u_info.get("custom_bg", None)

        async with ctx.typing():
            card_width, card_height = 930, 282
            card = Image.new("RGBA", (card_width, card_height), (20, 20, 25, 255))
            
            # Custom Background Image Load Karna
            if bg_url:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(bg_url) as resp:
                            if resp.status == 200:
                                bg_bytes = await resp.read()
                                bg_image = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
                                bg_image = bg_image.resize((card_width, card_height))
                                card.paste(bg_image, (0, 0))
                except Exception:
                    pass

            # Dark Overlay for Readability
            overlay = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 160))
            card = Image.alpha_composite(card, overlay)
            draw = ImageDraw.Draw(card)

            # User Avatar Circular Shape me Paste Karna
            avatar_url = member.display_avatar.url
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(avatar_url) as resp:
                        if resp.status == 200:
                            avatar_bytes = await resp.read()
                            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                            avatar = avatar.resize((180, 180))
                            
                            mask = Image.new("L", (180, 180), 0)
                            mask_draw = ImageDraw.Draw(mask)
                            mask_draw.ellipse((0, 0, 180, 180), fill=255)
                            
                            card.paste(avatar, (51, 51), mask)
            except Exception:
                pass

            try:
                font_large = ImageFont.truetype("arial.ttf", 36)
                font_medium = ImageFont.truetype("arial.ttf", 26)
            except IOError:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()

            # Username & Big Stats Display
            draw.text((260, 45), f"{member.name}", fill=(255, 255, 255, 255), font=font_large)
            
            msg_level = u_info['msg_level']
            msg_xp = u_info['msg_xp']
            next_xp = msg_level * 100
            
            draw.text((260, 105), f"LEVEL: {msg_level}", fill=(153, 45, 255, 255), font=font_large)
            draw.text((600, 110), f"XP: {msg_xp} / {next_xp}", fill=(220, 220, 220, 255), font=font_medium)

            # Progress Bar
            bar_x, bar_y, bar_w, bar_h = 260, 175, 600, 30
            draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=15, fill=(50, 50, 60, 255))
            
            progress = min(msg_xp / next_xp, 1.0)
            fill_w = int(bar_w * progress)
            if fill_w > 0:
                draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], radius=15, fill=(153, 45, 255, 255))

            buffer = io.BytesIO()
            card.save(buffer, format="PNG")
            buffer.seek(0)
            
            file = discord.File(buffer, filename="rank.png")
            await ctx.send(file=file)

    @commands.command(name="leaderboard", help="Show the top members leaderboard.")
    async def leaderboard(self, ctx):
        """Show leaderboard.
        Usage: &leaderboard"""
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id].get("users"):
            await ctx.send("❌ Is server par abhi koi level data available nahi hai!")
            return

        users_dict = data[guild_id]["users"]
        sorted_users = sorted(
            users_dict.items(),
            key=lambda x: (x[1]["msg_level"], x[1]["msg_xp"]),
            reverse=True
        )[:10]

        embed = discord.Embed(
            title="🏆 Server Message Leaderboard",
            color=discord.Color.gold()
        )

        desc = ""
        for i, (user_id, info) in enumerate(sorted_users, start=1):
