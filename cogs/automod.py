import discord
from discord.ext import commands
import datetime
import json
import os
import collections

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = "warnings.json"
        
        # Features on/off toggles
        self.toggles = {
            "youtube": True,
            "discord": True,
            "spam": True,
            "abuse": True
        }
        
        # Abuse words list (manageable via commands)
        self.abuse_words = ["badword1", "badword2", "gaali1"]
        
        # Spam tracking: {user_id: [timestamps]}
        self.message_tracker = collections.defaultdict(list)
        self.spam_time_limit = 5  # seconds window
        self.spam_message_limit = 4  # max messages allowed in window

    def add_warning_to_file(self, guild_id, user_id, reason):
        warnings_store = {}
        if os.path.exists(self.warnings_file):
            try:
                with open(self.warnings_file, "r") as f:
                    warnings_store = json.load(f)
            except Exception:
                warnings_store = {}

        g_id = str(guild_id)
        u_id = str(user_id)

        if g_id not in warnings_store:
            warnings_store[g_id] = {}
        if u_id not in warnings_store[g_id]:
            warnings_store[g_id][u_id] = []

        warnings_store[g_id][u_id].append(reason)

        try:
            with open(self.warnings_file, "w") as f:
                json.dump(warnings_store, f, indent=4)
        except Exception as e:
            print(f"Error saving automod warning: {e}")

        return len(warnings_store[g_id][u_id])

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Admins/Mods par automod apply nahi hoga
        if message.author.guild_permissions.manage_messages:
            return

        content_lower = message.content.lower()
        guild = message.guild
        author = message.author
        now = datetime.datetime.utcnow().timestamp()

        violation_reason = None
        give_timeout = False

        # 1. YouTube Link Check
        if self.toggles["youtube"] and ("youtube.com" in content_lower or "youtu.be" in content_lower):
            violation_reason = "Posted YouTube Link"

        # 2. Discord Server Invite Check
        elif self.toggles["discord"] and ("discord.gg" in content_lower or "discord.com/invite" in content_lower):
            violation_reason = "Posted Discord Server Invite Link"

        # 3. Abuse / Bad Words Check
        elif self.toggles["abuse"]:
            for word in self.abuse_words:
                if word in content_lower:
                    violation_reason = "Used Abusive Language"
                    give_timeout = True
                    break

        # 4. Spam Check
        if not violation_reason and self.toggles["spam"]:
            self.message_tracker[author.id].append(now)
            # Purane timestamps hatao
            self.message_tracker[author.id] = [t for t in self.message_tracker[author.id] if now - t < self.spam_time_limit]
            if len(self.message_tracker[author.id]) > self.spam_message_limit:
                violation_reason = "Spamming in Chat"
                give_timeout = True
                self.message_tracker[author.id] = []

        # Agar koi bhi rule break hua hai
        if violation_reason:
            try:
                await message.delete()
            except Exception:
                pass

            # Warning save karo aur total count lo
            total_warns = self.add_warning_to_file(guild.id, author.id, violation_reason)

            # Agar spam يا abuse hai toh 5 min ka timeout do
            if give_timeout:
                try:
                    await author.timeout(datetime.timedelta(minutes=5), reason=violation_reason)
                except Exception:
                    pass

            # Warning embed bhejo
            embed = create_embed(
                guild,
                title="⚠️ Auto-Mod Action Taken",
                description=f"**{author.mention}**, your message was deleted.\n\n"
                            f"📝 **Reason:** `{violation_reason}`\n"
                            f"📊 **Total Warnings:** {total_warns}"
                            f"{'\n⏱️ **Penalty:** 5-minute timeout applied.' if give_timeout else ''}",
                color=discord.Color.red()
            )
            
            warning_msg = await message.channel.send(embed=embed)
            await discord.utils.sleep_until(datetime.datetime.utcnow() + datetime.timedelta(seconds=5))
            try:
                await warning_msg.delete()
            except Exception:
                pass

    # --- AUTOMOD SETTINGS & MANAGEMENT COMMANDS ---

    @commands.group(name="automod", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod(self, ctx):
        embed = create_embed(
            ctx.guild,
            title="🛡️ Auto-Mod Control Panel",
            description=f"**Current Status:**\n"
                        f"• YouTube Link Filter: `{'ON' if self.toggles['youtube'] else 'OFF'}`\n"
                        f"• Discord Link Filter: `{'ON' if self.toggles['discord'] else 'OFF'}`\n"
                        f"• Spam Filter: `{'ON' if self.toggles['spam'] else 'OFF'}`\n"
                        f"• Abuse Filter: `{'ON' if self.toggles['abuse'] else 'OFF'}`\n\n"
                        f"**How to Use:**\n"
                        f"`&automod toggle [youtube/discord/spam/abuse] [on/off]`\n"
                        f"`&abuse add [word]` | `&abuse remove [word]` | `&abuse list`",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @automod.command(name="toggle")
    @commands.has_permissions(administrator=True)
    async def automod_toggle(self, ctx, feature: str, status: str):
        feature = feature.lower()
        status = status.lower()
        if feature not in self.toggles:
            return await ctx.send("❌ Invalid feature! Choose from: `youtube`, `discord`, `spam`, `abuse`.")
        
        if status == "on":
            self.toggles[feature] = True
        elif status == "off":
            self.toggles[feature] = False
        else:
            return await ctx.send("❌ Please specify status as `on` or `off`.")

        await ctx.send(f"✅ Auto-Mod **{feature}** filter is now **{status.upper()}**.")

    @commands.group(name="abuse", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def abuse(self, ctx):
        embed = create_embed(
            ctx.guild,
            title="🛑 Abuse Filter Usage",
            description="Please specify a valid action:\n\n"
                        "• `&abuse add [word]` — Add a word to the filter\n"
                        "• `&abuse remove [word]` — Remove a word from the filter\n"
                        "• `&abuse list` — View all filtered abusive words",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @abuse.command(name="add")
    @commands.has_permissions(administrator=True)
    async def abuse_add(self, ctx, word: str):
        word = word.lower()
        if word in self.abuse_words:
            return await ctx.send(f"⚠️ `{word}` is already in the abuse list.")
        self.abuse_words.append(word)
        await ctx.send(f"✅ Successfully added `{word}` to the abuse filter list.")

    @abuse.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def abuse_remove(self, ctx, word: str):
        word = word.lower()
        if word not in self.abuse_words:
            return await ctx.send(f"⚠️ `{word}` was not found in the abuse list.")
        self.abuse_words.remove(word)
        await ctx.send(f"✅ Successfully removed `{word}` from the abuse filter list.")

    @abuse.command(name="list")
    @commands.has_permissions(administrator=True)
    async def abuse_list(self, ctx):
        words = ", ".join([f"`{w}`" for w in self.abuse_words]) if self.abuse_words else "No words added yet."
        embed = create_embed(ctx.guild, title="🛑 Abusive Words List", description=words, color=discord.Color.orange())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
