import discord
from discord.ext import commands
import os
import json
import time
import io

DATA_FILE = "bot_database.json"
DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"messages": {}, "vc_time": {}, "invites": {}, "counting": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def create_embed(title="", description="", color=0x2B2D31, thumbnail=None):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail or DEFAULT_AVATAR)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_sessions = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        data = load_data()
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        # 1. Message Stats Tracking
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
                    embed = create_embed(
                        title="⚠️ Counting Failed",
                        description=f"❌ {message.author.mention}, wrong number or consecutive message! Counting reset to `1`.",
                        color=0xED4245
                    )
                    await message.channel.send(embed=embed)
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

        if before.channel is None and after.channel is not None:
            self.vc_sessions[user_id] = current_time
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
            embed = create_embed(title="Error", description=f"❌ {e}", color=0xED4245)
            await ctx.send(embed=embed)

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
        embed = create_embed(title="Counting Initialized", description=f"✅ Counting game started in {target_channel.mention} from `{amount}` with reaction `{emoji}`!")
        await ctx.send(embed=embed)

    @commands.command(name="emojiadd")
    @commands.has_permissions(manage_emojis=True)
    async def emoji_add(self, ctx, url: str, name: str):
        try:
            async with ctx.bot.session.get(url) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    emoji = await ctx.guild.create_custom_emoji(name=name, image=image_bytes)
                    embed = create_embed(title="Emoji Added", description=f"✅ Successfully added emoji: {emoji}", thumbnail=url)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(embed=create_embed(title="Error", description="❌ Failed to fetch image from URL.", color=0xED4245))
        except Exception as e:
            await ctx.send(embed=create_embed(title="Error", description=f"❌ Error adding emoji: {e}", color=0xED4245))

    @commands.command(name="stickeradd")
    @commands.has_permissions(manage_emojis=True)
    async def sticker_add(self, ctx, name: str, url: str = None):
        if not url and ctx.message.attachments:
            url = ctx.message.attachments[0].url
        if not url:
            await ctx.send(embed=create_embed(title="Error", description="❌ Please provide an image URL or attach an image for the sticker.", color=0xED4245))
            return
        try:
            async with ctx.bot.session.get(url) as resp:
                image_bytes = await resp.read()
                file = discord.File(fp=io.BytesIO(image_bytes), filename="sticker.png")
                sticker = await ctx.guild.create_sticker(name=name, description="Added via bot", file=file, emoji="✨")
                embed = create_embed(title="Sticker Added", description=f"✅ Successfully added sticker: **{sticker.name}**", thumbnail=url)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=create_embed(title="Error", description=f"❌ Error adding sticker: {e}", color=0xED4245))

    @commands.command(name="m")
    async def message_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        data = load_data()
        count = data.get("messages", {}).get(str(ctx.guild.id), {}).get(str(target.id), 0)
        
        embed = create_embed(
            title=f"Message Statistics",
            description=f"📊 **{target.mention}** has sent **{count}** messages in this server.",
            thumbnail=target.display_avatar.url
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @commands.command(name="v")
    async def voice_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        data = load_data()
        seconds = data.get("vc_time", {}).get(str(ctx.guild.id), {}).get(str(target.id), 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        embed = create_embed(
            title=f"Voice Statistics",
            description=f"🎙️ **{target.mention}** has spent **{hours} hours and {minutes} minutes** in voice channels.",
            thumbnail=target.display_avatar.url
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @commands.command(name="i")
    async def invite_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        data = load_data()
        invs = data.get("invites", {}).get(str(ctx.guild.id), {}).get(str(target.id), {"uses": 0})
        
        embed = create_embed(
            title=f"Invite Statistics",
            description=f"✉️ **{target.mention}** has invited **{invs['uses']}** members to the server.",
            thumbnail=target.display_avatar.url
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # --- RESET COMMANDS ---
    @commands.command(name="rm")
    @commands.has_permissions(administrator=True)
    async def reset_messages(self, ctx, option: str):
        if option.lower() == "all":
            data = load_data()
            if str(ctx.guild.id) in data.get("messages", {}):
                data["messages"][str(ctx.guild.id)] = {}
                save_data(data)
            embed = create_embed(title="Stats Reset", description="✅ Successfully reset all message statistics!")
            await ctx.send(embed=embed)

    @commands.command(name="rv")
    @commands.has_permissions(administrator=True)
    async def reset_vc(self, ctx, option: str):
        if option.lower() == "all":
            data = load_data()
            if str(ctx.guild.id) in data.get("vc_time", {}):
                data["vc_time"][str(ctx.guild.id)] = {}
                save_data(data)
            embed = create_embed(title="Stats Reset", description="✅ Successfully reset all voice channel statistics!")
            await ctx.send(embed=embed)

    @commands.command(name="ri")
    @commands.has_permissions(administrator=True)
    async def reset_invites(self, ctx, option: str):
        if option.lower() == "all":
            data = load_data()
            if str(ctx.guild.id) in data.get("invites", {}):
                data["invites"][str(ctx.guild.id)] = {}
                save_data(data)
            embed = create_embed(title="Stats Reset", description="✅ Successfully reset all invite statistics!")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
