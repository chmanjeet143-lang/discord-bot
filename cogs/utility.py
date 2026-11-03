import discord
from discord.ext import commands
import datetime
import json
import os
import io
import aiohttp
import re
import asyncio

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"
PREFIX_FILE = "prefixes.json"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

def format_time(seconds: int):
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def load_prefixes():
    if os.path.exists(PREFIX_FILE):
        try:
            with open(PREFIX_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_prefixes(prefixes):
    try:
        with open(PREFIX_FILE, "w") as f:
            json.dump(prefixes, f, indent=4)
    except Exception:
        pass


class Utility(commands.Cog, name="Utility"):
    """Explore all commands related to Utility and Games."""
    def __init__(self, bot):
        self.bot = bot
        self.current_count = 1
        self.counting_channel = None
        self.success_emoji = "✅"
        self.last_user_id = None
        
        self.message_counts = {}
        self.invite_counts = {}
        self.voice_time_seconds = {}
        self.vc_joins = {}
        self.afk_users = {}

    # --- SIRF EK HI HIDDEN COUNTING COMMAND ---
    @commands.command(name="count", hidden=True, help="Start or configure the counting game.")
    @commands.has_permissions(manage_channels=True)
    async def count_command(self, ctx, number: int, channel: discord.TextChannel = None, emoji: str = "✅"):
        # Admin ka command message aur bot ka response dono delete kar dena taaki bilkul clean lage
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        self.current_count = number
        self.counting_channel = channel or ctx.channel
        self.success_emoji = emoji
        self.last_user_id = None

        embed = create_embed(
            ctx.guild,
            title="🎯 Counting Game Started!",
            description=f"Counting successfully started at **{self.current_count}** in {self.counting_channel.mention}!",
            color=discord.Color.green()
        )
        
        try:
            sent_msg = await ctx.send(embed=embed)
            await asyncio.sleep(2)  # 2 second baad bot apna message bhi uda dega
            await sent_msg.delete()
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        author_id = message.author.id

        if self.counting_channel and message.channel.id == self.counting_channel.id:
            # Agar koi command run ki gayi hai is channel mein, toh usko handle karne do
            if message.content.startswith(tuple(await self.bot.get_prefix(message)) if hasattr(self.bot, 'get_prefix') else "&"):
                return

            try:
                number = int(message.content.strip())
            except ValueError:
                # Agar koi hi, hello ya koi bhi faltu text likhe, toh message turant delete kar do
                if not message.author.guild_permissions.manage_messages:
                    try:
                        await message.delete()
                    except discord.HTTPException:
                        pass
                return  

            # Double count ya wrong number check
            if author_id == self.last_user_id or number != self.current_count:
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass
                
                error_desc = (
                    f"❌ {message.author.mention}, you cannot count twice in a row!" 
                    if author_id == self.last_user_id 
                    else f"❌ {message.author.mention}, that's incorrect! Next correct number is **{self.current_count}**."
                )
                
                embed = create_embed(
                    message.guild,
                    title="⚠️ Counting Error",
                    description=error_desc,
                    color=discord.Color.red()
                )
                err_msg = await message.channel.send(embed=embed)
                
                await asyncio.sleep(4)
                try:
                    await err_msg.delete()
                except discord.HTTPException:
                    pass
                return

            if number == self.current_count:
                try:
                    await message.add_reaction(self.success_emoji)
                except discord.HTTPException:
                    pass
                self.current_count += 1
                self.last_user_id = author_id
                return

        # Baaki AFK aur message tracking logic jo pehle se thi
        if message.mentions:
            for mention in message.mentions:
                if mention.id in self.afk_users:
                    afk_data = self.afk_users[mention.id]
                    afk_data["mentions"].append({
                        "author": message.author.name,
                        "channel": message.channel,
                        "time": datetime.datetime.now(datetime.timezone.utc),
                        "content": message.content
                    })
                    
                    duration = int(datetime.datetime.now(datetime.timezone.utc).timestamp() - afk_data["time"])
                    time_ago = format_time(duration)
                    
                    embed_afk = create_embed(
                        message.guild,
                        title="💤 User is AFK",
                        description=f"**{mention.name}** is currently AFK: {afk_data['reason']}\n⏱️ Went AFK **{time_ago}** ago.",
                        color=discord.Color.blue()
                    )
                    await message.channel.send(embed=embed_afk, delete_after=10)

        if author_id in self.afk_users and not message.content.lower().startswith("&afk"):
            afk_data = self.afk_users.pop(author_id)
            mentions_list = afk_data["mentions"]
            
            desc = f"Welcome back {message.author.mention}, I have removed your AFK status!\n\n"
            if mentions_list:
                desc += "📬 **You were mentioned while you were away:**\n"
                for m in mentions_list:
                    t_str = m["time"].strftime("%H:%M:%S")
                    desc += f"• **{m['author']}** in {m['channel'].mention} at `{t_str}`: {m['content']}\n"
            else:
                desc += "✨ No one mentioned you while you were away."

            try:
                embed_back = create_embed(
                    message.guild,
                    title="👋 Welcome Back!",
                    description=desc,
                    color=discord.Color.green()
                )
                await message.channel.send(embed=embed_back, delete_after=15)
            except discord.HTTPException:
                pass

        self.message_counts[author_id] = self.message_counts.get(author_id, 0) + 1

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()

        if before.channel is None and after.channel is not None:
            self.vc_joins[member.id] = now

        elif before.channel is not None and after.channel is None:
            if member.id in self.vc_joins:
                duration = int(now - self.vc_joins[member.id])
                self.voice_time_seconds[member.id] = self.voice_time_seconds.get(member.id, 0) + duration
                del self.vc_joins[member.id]

    @commands.command(name="afk", help="Set your AFK status with an optional reason.")
    async def afk_command(self, ctx, *, reason: str = "AFK"):
        self.afk_users[ctx.author.id] = {
            "reason": reason,
            "time": datetime.datetime.now(datetime.timezone.utc).timestamp(),
            "mentions": []
        }
        embed = create_embed(
            ctx.guild,
            title="💤 AFK Status Set",
            description=f"**{ctx.author.mention}**, you are now marked as AFK.\n📝 **Reason:** {reason}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="msg", help="Check how many messages a member has sent.")
    async def msg_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        count = self.message_counts.get(target.id, 0)
        embed = create_embed(
            ctx.guild,
            title="💬 Message Count",
            description=f"**{target.mention}** has sent **{count}** messages.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="vc", help="Check how much time a member has spent in voice channels.")
    async def vc_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        total_secs = self.voice_time_seconds.get(target.id, 0)
        if target.id in self.vc_joins:
            total_secs += int(datetime.datetime.now(datetime.timezone.utc).timestamp() - self.vc_joins[target.id])

        formatted_time = format_time(total_secs)
        embed = create_embed(
            ctx.guild,
            title="🎙️ Voice Time",
            description=f"**{target.mention}** has spent **{formatted_time}** in voice channels.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="inv", help="Check how many members a user has invited.")
    async def inv_stats(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        invites = self.invite_counts.get(target.id, 0)
        embed = create_embed(
            ctx.guild,
            title="✉️ Invite Count",
            description=f"**{target.mention}** has successfully invited **{invites}** members.",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="setprefix", help="Changes the bot prefix for this server.")
    @commands.has_permissions(manage_guild=True)
    async def set_prefix(self, ctx, new_prefix: str):
        prefixes = load_prefixes()
        prefixes[str(ctx.guild.id)] = new_prefix
        save_prefixes(prefixes)
        
        embed = create_embed(
            ctx.guild,
            title="⚙️ Prefix Updated",
            description=f"Successfully changed the server prefix to: **{new_prefix}**\nExample: `{new_prefix}help`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


class Clone(commands.Cog, name="Clone"):
    """Explore all commands related to Clone."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clone", help="Clone custom emojis or stickers by replying to a message.")
    @commands.has_permissions(manage_emojis=True)
    async def clone_command(self, ctx):
        if not ctx.message.reference:
            embed = create_embed(ctx.guild, title="❌ Error", description="Please reply to a message containing a custom emoji or sticker that you want to clone!", color=discord.Color.red())
            return await ctx.send(embed=embed)

        try:
            referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except Exception:
            embed = create_embed(ctx.guild, title="❌ Error", description="Could not fetch the referenced message.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        cloned_count = 0
        async with aiohttp.ClientSession() as session:
            emoji_matches = re.findall(r"<(a?):([a-zA-Z0-9\_]+):([0-9]+)>", referenced_msg.content)
            
            for animated, name, emoji_id in emoji_matches:
                extension = "gif" if animated == "a" else "png"
                url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}"
                
                async with session.get(url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        try:
                            await ctx.guild.create_custom_emoji(name=name, image=image_bytes, reason=f"Cloned by {ctx.author}")
                            cloned_count += 1
                        except Exception as e:
                            print(f"Error creating emoji: {e}")

            if referenced_msg.stickers:
                for sticker in referenced_msg.stickers:
                    url = sticker.url
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            try:
                                file = discord.File(io.BytesIO(image_bytes), filename=f"{sticker.name}.png")
                                await ctx.guild.create_sticker(name=sticker.name, description="Cloned sticker", emoji="✨", file=file, reason=f"Cloned by {ctx.author}")
                                cloned_count += 1
                            except Exception as e:
                                print(f"Error creating sticker: {e}")

        if cloned_count > 0:
            embed = create_embed(
                ctx.guild,
                title="✨ Successfully Cloned!",
                description=f"Successfully added **{cloned_count}** emoji/sticker(s) to **Moonlight Heaven**!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = create_embed(ctx.guild, title="❌ Error", description="No valid custom emojis or stickers found in that replied message!", color=discord.Color.red())
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Utility(bot))
    await bot.add_cog(Clone(bot))
