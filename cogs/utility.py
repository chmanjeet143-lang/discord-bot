import discord
from discord.ext import commands
import asyncio
import os
import json
import time

DATA_FILE = "bot_database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"messages": {}, "vc_time": {}, "invites": {}, "counting": {}, "prefixes": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_sessions = {} # {user_id: start_timestamp}
        self.invites_cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                self.invites_cache[guild.id] = await guild.invites()
            except:
                pass

    # --- TRACKERS (Messages, Counting, VC, Invites) ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        data = load_data()
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        # 1. Message Stats Tracking (&m)
        if guild_id not in data["messages"]:
            data["messages"][guild_id] = {}
        data["messages"][guild_id][user_id] = data["messages"][guild_id].get(user_id, 0) + 1
        save_data(data)

        # 2. Counting Game Logic
        counting_info = data.get("counting", {}).get(guild_id)
        if counting_info and message.channel.id == counting_info.get("channel_id"):
            try:
                number = int(message.content.strip())
                expected = counting_info.get("next_number", 1)
                last_user = counting_info.get("last_user", None)
                emoji = counting_info.get("emoji", "✅")

                if number == expected and user_id != last_user:
                    counting_info["next_number"] = expected + 1
                    counting_info["last_user"] = user_id
                    save_data(data)
                    await message.add_reaction(emoji)
                else:
                    await message.channel.send(f"❌ {message.author.mention}, wrong number or consecutive message! Counting reset to `1`.")
                    counting_info["next_number"] = 1
                    counting_info["last_user"] = None
                    save_data(data)
            except ValueError:
                pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        user_id = str(member.id)
        current_time = time.time()

        # Joined a VC
        if before.channel is None and after.channel is not None:
            self.vc_sessions[user_id] = current_time
        # Left a VC
        elif before.channel is not None and after.channel is None:
            if user_id in self.vc_sessions:
                elapsed = int(current_time - self.vc_sessions[user_id])
                del self.vc_sessions[user_id]

                data = load_data()
                guild_id = str(member.guild.id)
                if guild_id not in data["vc_time"]:
                    data["vc_time"][guild_id] = {}
                data["vc_time"][guild_id][user_id] = data["vc_time"][guild_id].get(user_id, 0) + elapsed
                save_data(data)

    # --- COMMANDS ---

    @commands.command(name="say")
    @commands.has_permissions(manage_messages=True)
    async def say_cmd(self, ctx, *, message: str):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(message)

    @commands.command(name="reply")
    @commands.has_permissions(manage_messages=True)
    async def reply_cmd(self, ctx, message_id: int, *, message: str):
        try:
            msg = await ctx.channel.fetch_message(message_id)
            await msg.reply(message)
            try: await ctx.message.delete()
            except: pass
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.command(name="start", aliases=["counting"])
    @commands.has_permissions(administrator=True)
    async def start_counting(self, ctx, amount: int = 1, channel: discord.TextChannel = None, emoji: str = "✅"):
        target_channel = channel or ctx.channel
        data = load_data()
        if "counting" not in data:
            data["counting"] = {}
        
        data["counting"][str(ctx.guild.id)] = {
            "channel_id": target_channel.id,
            "next_number": amount,
            "last_user": None,
            "emoji": emoji
        }
        save_data(data)
        await ctx.send(f"✅ Counting game initialized in {target_channel.mention} starting from `{amount}` with reaction `{emoji}`!")

    @commands.command(name="emojiadd")
    @commands.has_permissions(manage_emojis=True)
    async def emoji_add(self, ctx, url: str, name: str):
        try:
            async with ctx.bot.session.get(url) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    emoji = await ctx.guild.create_custom_emoji(name=name, image=image_bytes)
                    await ctx.send(f"✅ Successfully added emoji: {emoji}")
                else:
                    await ctx.send("❌ Failed to fetch image from URL.")
        except Exception as e:
            await ctx.send(f"❌ Error adding emoji: {e}")

    @commands.command(name="stickeradd")
    @commands.has_permissions(manage_emojis=True)
    async def sticker_add(self, ctx, name: str, url: str = None):
        if not url and ctx.message.attachments:
            url = ctx.message.attachments[0].url
        if not url:
            await ctx.send("❌ Please provide an image URL or attach an image for the sticker.")
            return
        try:
            async with ctx.bot.session.get(url) as resp:
                image_bytes = await resp.read()
                file = discord.File(fp=io.BytesIO(image_bytes), filename="sticker.png")
                sticker = await ctx.guild.create_sticker(name=name, description="Added via bot", file=file, emoji="✨")
                await ctx.send(f"✅ Successfully added sticker: **{sticker.name}**")
        except Exception as e:
            await ctx.send(f"❌ Error adding sticker: {e}")

    @commands.command(name="m")
    async def message_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        data = load_data()
        count = data.get("messages", {}).get(str(ctx.guild.id), {}).get(str(target.id), 0)
        await ctx.send(f"📊 **{target.name}** has sent **{count}** messages in this server.")

    @commands.command(name="v")
    async def voice_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        data = load_data()
        seconds = data.get("vc_time", {}).get(str(ctx.guild.id), {}).get(str(target.id), 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        await ctx.send(f"🎙️ **{target.name}** has spent **{hours} hours and {minutes} minutes** in voice channels.")

    @commands.command(name="i")
    async def invite_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        data = load_data()
        invs = data.get("invites", {}).get(str(ctx.guild.id), {}).get(str(target.id), {"uses": 0})
        await ctx.send(f"✉️ **{target.name}** has invited **{invs['uses']}** members to the server.")

    # --- RESET COMMANDS ---
    @commands.command(name="rm")
    @commands.has_permissions(administrator=True)
    async def reset_messages(self, ctx, option: str):
        if option.lower() == "all":
            data = load_data()
            if str(ctx.guild.id) in data.get("messages", {}):
                data["messages"][str(ctx.guild.id)] = {}
                save_data(data)
            await ctx.send("✅ Successfully reset all message statistics!")

    @commands.command(name="rv")
    @commands.has_permissions(administrator=True)
    async def reset_vc(self, ctx, option: str):
        if option.lower() == "all":
            data = load_data()
            if str(ctx.guild.id) in data.get("vc_time", {}):
                data["vc_time"][str(ctx.guild.id)] = {}
                save_data(data)
            await ctx.send("✅ Successfully reset all voice channel statistics!")

    @commands.command(name="ri")
    @commands.has_permissions(administrator=True)
    async def reset_invites(self, ctx, option: str):
        if option.lower() == "all":
            data = load_data()
            if str(ctx.guild.id) in data.get("invites", {}):
                data["invites"][str(ctx.guild.id)] = {}
                save_data(data)
            await ctx.send("✅ Successfully reset all invite statistics!")

async def setup(bot):
    import io
    await bot.add_cog(Utility(bot))
