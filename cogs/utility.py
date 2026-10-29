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
        except:
            return {}
    return {}

def save_prefixes(prefixes):
    try:
        with open(PREFIX_FILE, "w") as f:
            json.dump(prefixes, f, indent=4)
    except:
        pass


class Utility(commands.Cog, name="Utility"):
    """Explore all commands related to Utility and Games."""
    def __init__(self, bot):
        self.bot = bot
        self.current_count = 1
        self.counting_channel = None
        self.success_emoji = "✅"
        self.last_user_id = None  # To prevent double counting by the same user
        
        self.message_counts = {}
        self.invite_counts = {}
        self.voice_time_seconds = {}
        self.vc_joins = {}
        self.afk_users = {}

    @commands.command(name="start", hidden=True, help="Start or configure the counting game with a custom starting number and emoji.\n\n**Example:** &start 1 #counting ✅")
    @commands.has_permissions(manage_channels=True)
    async def start_counting(self, ctx, number: int, channel: discord.TextChannel = None, emoji: str = "✅"):
        # User ka command message delete karna
        try:
            await ctx.message.delete()
        except:
            pass

        self.current_count = number
        self.counting_channel = channel or ctx.channel
        self.success_emoji = emoji
        self.last_user_id = None

        embed = create_embed(
            ctx.guild,
            title="🎯 Counting Game Started!",
            description=f"The counting game has been configured successfully!\n\n"
                        f"📂 **Channel:** {self.counting_channel.mention}\n"
                        f"🔢 **Start Number:** **{self.current_count}**\n"
                        f"✨ **Reaction Emoji:** {self.success_emoji}",
            color=discord.Color.green()
        )
        
        # Bot ka message bhejna aur kuch seconds baad delete karna
        sent_msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        try:
            await sent_msg.delete()
        except:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        author_id = message.author.id

        if message.mentions:
            for mention in message.mentions:
                if mention.id in self.afk_users:
                    afk_data = self.afk_users[mention.id]
                    
                    afk_data["mentions"].append({
                        "author": message.author.name,
                        "channel": message.channel,
                        "time": datetime.datetime.utcnow(),
                        "content": message.content
                    })
                    
                    duration = int(datetime.datetime.utcnow().timestamp() - afk_data["time"])
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
            except:
                pass

        self.message_counts[author_id] = self.message_counts.get(author_id, 0) + 1

        if self.counting_channel and message.channel.id == self.counting_channel.id:
            try:
                number = int(message.content.strip())
            except ValueError:
                # Agar koi number ki jagah text/kuch aur likhe, toh sirf uska message delete kar do
                try:
                    await message.delete()
                except:
                    pass
                return  

            # Anti-Double Count & Wrong Number Check with Auto-Delete
            if author_id == self.last_user_id or number != self.current_count:
                try:
                    await message.delete()
                except:
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
                except:
                    pass
                return

            if number == self.current_count:
                try:
                    await message.add_reaction(self.success_emoji)
                except:
                    pass
                self.current_count += 1
                self.last_user_id = author_id

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        
        now = datetime.datetime.utcnow().timestamp()

        if before.channel is None and after.channel is not None:
            self.vc_joins[member.id] = now

        elif before.channel is not None and after.channel is None:
            if member.id in self.vc_joins:
                duration = int(now - self.vc_joins[member.id])
                self.voice_time_seconds[member.id] = self.voice_time_seconds.get(member.id, 0) + duration
                del self.vc_joins[member.id]

    @commands.command(name="afk", help="Set your AFK status with an optional reason.\n\n**Example:** &afk Sleeping")
    async def afk_command(self, ctx, *, reason: str = "AFK"):
        self.afk_users[ctx.author.id] = {
            "reason": reason,
            "time": datetime.datetime.utcnow().timestamp(),
            "mentions": []
        }
        embed = create_embed(
            ctx.guild,
            title="💤 AFK Status Set",
            description=f"**{ctx.author.mention}**, you are now marked as AFK.\n📝 **Reason:** {reason}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="setprefix", help="Changes the bot prefix for this server.\n\n**Example:** &setprefix !")
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

    @commands.command(name="m", help="Check how many messages you have sent.\n\n**Example:** &m")
    async def message_count(self, ctx):
        count = self.message_counts.get(ctx.author.id, 0)
        embed = create_embed(
            ctx.guild,
            title="💬 Message Count",
            description=f"You have sent **{count}** messages.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="v", help="Check how much time you have spent in voice channels.\n\n**Example:** &v")
    async def voice_count(self, ctx):
        total_secs = self.voice_time_seconds.get(ctx.author.id, 0)
        if ctx.author.id in self.vc_joins:
            total_secs += int(datetime.datetime.utcnow().timestamp() - self.vc_joins[ctx.author.id])

        formatted_time = format_time(total_secs)
        embed = create_embed(
            ctx.guild,
            title="🎙️ Voice Time",
            description=f"You have spent **{formatted_time}** in voice channels.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="i", help="Check how many members you have successfully invited.\n\n**Example:** &i")
    async def invite_count(self, ctx):
        invites = self.invite_counts.get(ctx.author.id, 0)
        embed = create_embed(
            ctx.guild,
            title="✉️ Invite Count",
            description=f"You have successfully invited **{invites}** members.",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="rm", help="Reset message counts for all users.\n\n**Example:** &rm all")
    @commands.has_permissions(manage_messages=True)
    async def remove_messages_all(self, ctx, action: str = None):
        if action and action.lower() == "all":
            self.message_counts.clear()
            embed = create_embed(ctx.guild, title="💬 Messages Reset", description="Successfully cleared message counts for all users.", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Usage: `&rm all`")

    @commands.command(name="rv", help="Reset voice time counts for all users.\n\n**Example:** &rv all")
    @commands.has_permissions(manage_messages=True)
    async def remove_voice_all(self, ctx, action: str = None):
        if action and action.lower() == "all":
            self.voice_time_seconds.clear()
            self.vc_joins.clear()
            embed = create_embed(ctx.guild, title="🎙️ Voice Time Reset", description="Successfully cleared voice time counts for all users.", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Usage: `&rv all`")

    @commands.command(name="ri", help="Reset invite counts for all users.\n\n**Example:** &ri all")
    @commands.has_permissions(manage_messages=True)
    async def remove_invites_all(self, ctx, action: str = None):
        if action and action.lower() == "all":
            self.invite_counts.clear()
            embed = create_embed(ctx.guild, title="✉️ Invites Reset", description="Successfully cleared invite counts for all users.", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Usage: `&ri all`")

    @commands.command(name="lm", help="View the messages leaderboard.\n\n**Example:** &lm")
    async def leaderboard_messages(self, ctx):
        if not self.message_counts:
            embed = create_embed(ctx.guild, title="💬 Messages Leaderboard", description="No message data recorded yet.", color=discord.Color.blue())
            return await ctx.send(embed=embed)

        sorted_users = sorted(self.message_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        desc = ""
        for idx, (uid, count) in enumerate(sorted_users, 1):
            desc += f"`#{idx}` <@{uid}> — **{count}** messages\n"

        embed = create_embed(ctx.guild, title="💬 Messages Leaderboard", description=desc, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command(name="lv", help="View the voice time leaderboard.\n\n**Example:** &lv")
    async def leaderboard_voice(self, ctx):
        if not self.voice_time_seconds and not self.vc_joins:
            embed = create_embed(ctx.guild, title="🎙️ Voice Leaderboard", description="No voice time recorded yet.", color=discord.Color.green())
            return await ctx.send(embed=embed)

        current_data = self.voice_time_seconds.copy()
        now = datetime.datetime.utcnow().timestamp()
        for uid, join_time in self.vc_joins.items():
            current_data[uid] = current_data.get(uid, 0) + int(now - join_time)

        sorted_users = sorted(current_data.items(), key=lambda x: x[1], reverse=True)[:10]
        desc = ""
        for idx, (uid, secs) in enumerate(sorted_users, 1):
            desc += f"`#{idx}` <@{uid}> — **{format_time(secs)}**\n"

        embed = create_embed(ctx.guild, title="🎙️ Voice Time Leaderboard", description=desc, color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name="li", help="View the invites leaderboard.\n\n**Example:** &li")
    async def leaderboard_invites(self, ctx):
        if not self.invite_counts:
            embed = create_embed(ctx.guild, title="✉️ Invites Leaderboard", description="No invite data recorded yet.", color=discord.Color.purple())
            return await ctx.send(embed=embed)

        sorted_users = sorted(self.invite_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        desc = ""
        for idx, (uid, count) in enumerate(sorted_users, 1):
            desc += f"`#{idx}` <@{uid}> — **{count}** invites\n"

        embed = create_embed(ctx.guild, title="✉️ Invites Leaderboard", description=desc, color=discord.Color.purple())
        await ctx.send(embed=embed)

    @commands.command(name="say", help="Make the bot say a message and delete your command message.\n\n**Example:** &say Hello everyone!")
    async def say_command(self, ctx, *, message: str):
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(message)

    @commands.command(name="reply", help="Make the bot reply to a specific message.\n\n**Example:** &reply Hello!")
    async def reply_command(self, ctx, *, message: str):
        if ctx.message.reference:
            original_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            await original_msg.reply(message)
        else:
            await ctx.send(message)


class Clone(commands.Cog, name="Clone"):
    """Explore all commands related to Clone."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clone", help="Clone custom emojis or stickers by replying to a message.\n\n**Example:** &clone (replying to an emoji/sticker)")
    @commands.has_permissions(manage_emojis=True)
    async def clone_command(self, ctx):
        if not ctx.message.reference:
            return await ctx.send("❌ Please reply to a message containing a custom emoji or sticker that you want to clone!")

        try:
            referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except Exception:
            return await ctx.send("❌ Could not fetch the referenced message.")

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
            await ctx.send("❌ No valid custom emojis or stickers found in that replied message!")


async def setup(bot):
    await bot.add_cog(Utility(bot))
    await bot.add_cog(Clone(bot))
