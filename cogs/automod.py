import discord
from discord.ext import commands
import sqlite3
import time
from datetime import timedelta
from collections import defaultdict

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Database Setup for AutoMod Settings & Bad Words
        self.db = sqlite3.connect("automod.db", check_same_thread=False)
        self.cursor = self.db.cursor()
        self.create_tables()
        
        # Anti-Spam Tracking Dictionary: { (guild_id, user_id): [timestamps] }
        self.message_tracker = defaultdict(list)

    def cog_unload(self):
        try:
            self.db.close()
        except:
            pass

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS automod_settings (
                guild_id INTEGER PRIMARY KEY,
                antilink INTEGER DEFAULT 1,
                antilink_punishment TEXT DEFAULT 'delete',
                antilink_duration INTEGER DEFAULT 5,
                
                antiyoutube INTEGER DEFAULT 0,
                antiyoutube_punishment TEXT DEFAULT 'delete',
                antiyoutube_duration INTEGER DEFAULT 5,
                
                antispam INTEGER DEFAULT 1,
                antispam_limit INTEGER DEFAULT 5,
                antispam_seconds INTEGER DEFAULT 5,
                antispam_punishment TEXT DEFAULT 'timeout',
                antispam_duration INTEGER DEFAULT 5,
                
                badwords INTEGER DEFAULT 1,
                badwords_punishment TEXT DEFAULT 'delete',
                badwords_duration INTEGER DEFAULT 5
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bad_words (
                guild_id INTEGER,
                word TEXT,
                PRIMARY KEY (guild_id, word)
            )
        ''')
        self.db.commit()

    def get_settings(self, guild_id):
        self.cursor.execute("SELECT * FROM automod_settings WHERE guild_id = ?", (guild_id,))
        res = self.cursor.fetchone()
        if not res:
            self.cursor.execute("INSERT OR IGNORE INTO automod_settings (guild_id) VALUES (?)", (guild_id,))
            self.db.commit()
            self.cursor.execute("SELECT * FROM automod_settings WHERE guild_id = ?", (guild_id,))
            res = self.cursor.fetchone()
        return res # Returns full row of settings

    async def handle_punishment(self, message, punishment, duration, reason):
        guild = message.guild
        member = message.author
        
        # Always delete the message unless punishment is strictly invalid, but delete is base rule
        try:
            await message.delete()
        except:
            pass

        if punishment == "timeout":
            try:
                await member.timeout(timedelta(minutes=duration), reason=reason)
                embed = discord.Embed(
                    description=f"🚨 {member.mention} has been given a **{duration}-minute timeout** for {reason}!",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed, delete_after=7)
            except:
                pass
        elif punishment == "kick":
            try:
                await member.kick(reason=reason)
                embed = discord.Embed(
                    description=f"🚨 {member.mention} has been **kicked** for {reason}!",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed, delete_after=7)
            except:
                pass
        elif punishment == "ban":
            try:
                await member.ban(reason=reason)
                embed = discord.Embed(
                    description=f"🚨 {member.mention} has been **banned** for {reason}!",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed, delete_after=7)
            except:
                pass
        # If punishment is 'delete', message is already deleted, no extra action.

    # --- AUTOMOD LISTENER (MAIN CHECKER) ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or message.author.guild_permissions.administrator:
            return

        guild_id = message.guild.id
        row = self.get_settings(guild_id)
        # Unpack settings
        # row indices: 0:guild_id, 1:antilink, 2:antilink_punishment, 3:antilink_duration, 4:antiyoutube, 5:antiyoutube_punishment, 6:antiyoutube_duration, 7:antispam, 8:antispam_limit, 9:antispam_seconds, 10:antispam_punishment, 11:antispam_duration, 12:badwords, 13:badwords_punishment, 14:badwords_duration
        
        antilink, antilink_p, antilink_d = row[1], row[2], row[3]
        antiyoutube, antiyoutube_p, antiyoutube_d = row[4], row[5], row[6]
        antispam, spam_limit, spam_secs, antispam_p, antispam_d = row[7], row[8], row[9], row[10], row[11]
        badwords_enabled, badwords_p, badwords_d = row[12], row[13], row[14]

        content_lower = message.content.lower()

        try:
            # 1. Anti-YouTube Filter
            if antiyoutube and ("youtube.com" in content_lower or "youtu.be" in content_lower):
                await self.handle_punishment(message, antiyoutube_p, antiyoutube_d, "YouTube links violation")
                return

            # 2. Anti-Link Filter (Allowing GIFs)
            has_link = "discord.gg/" in content_lower or "http://" in content_lower or "https://" in content_lower or "www." in content_lower
            is_gif = "tenor.com" in content_lower or "giphy.com" in content_lower or ".gif" in content_lower
            
            if antilink and has_link and not is_gif:
                if not (antiyoutube and ("youtube.com" in content_lower or "youtu.be" in content_lower)):
                    await self.handle_punishment(message, antilink_p, antilink_d, "Unauthorized link violation")
                    return

            # 3. Bad Words Filter
            if badwords_enabled:
                self.cursor.execute("SELECT word FROM bad_words WHERE guild_id = ?", (guild_id,))
                banned_words = [r[0] for r in self.cursor.fetchall()]
                
                if any(word in content_lower for word in banned_words):
                    await self.handle_punishment(message, badwords_p, badwords_d, "Banned word usage")
                    return

            # 4. Anti-Spam Filter
            if antispam:
                current_time = time.time()
                key = (guild_id, message.author.id)
                
                self.message_tracker[key] = [t for t in self.message_tracker[key] if current_time - t < spam_secs]
                self.message_tracker[key].append(current_time)

                if len(self.message_tracker[key]) >= spam_limit:
                    self.message_tracker[key] = []
                    await self.handle_punishment(message, antispam_p, antispam_d, "Spamming detected")
                    return

        except Exception as e:
            print(f"AutoMod Error: {e}")

    # --- ANTILINK CONFIGURATION COMMANDS ---
    @commands.command(name="antilink", help="Toggle anti-link protection ON or OFF.\nUsage: &antilink on / off")
    @commands.has_permissions(administrator=True)
    async def cmd_antilink(self, ctx, status: str = None):
        if not status or status.lower() not in ["on", "off"]:
            embed = discord.Embed(title="🛡️ Anti-Link Settings", description="Toggle anti-link protection.\n\n**Usage:**\n`&antilink on`\n`&antilink off`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        val = 1 if status.lower() == "on" else 0
        self.cursor.execute("UPDATE automod_settings SET antilink = ? WHERE guild_id = ?", (val, ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Anti-Link protection is now **{'Enabled (ON)' if val == 1 else 'Disabled (OFF)'}**.", color=discord.Color.green()))

    @commands.command(name="antilinkaction", help="Set punishment for anti-link violation.\nUsage: &antilinkaction delete / timeout / kick / ban")
    @commands.has_permissions(administrator=True)
    async def cmd_antilinkaction(self, ctx, action: str = None):
        valid = ["delete", "timeout", "kick", "ban"]
        if not action or action.lower() not in valid:
            embed = discord.Embed(title="🛡️ Anti-Link Action", description="Set punishment when someone sends a link.\n\n**Valid Actions:** `delete`, `timeout`, `kick`, `ban`\n**Usage:** `&antilinkaction timeout`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        self.cursor.execute("UPDATE automod_settings SET antilink_punishment = ? WHERE guild_id = ?", (action.lower(), ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Anti-Link punishment updated to: **{action.lower()}**.", color=discord.Color.green()))

    @commands.command(name="antilinktime", help="Set timeout duration in minutes for anti-link.\nUsage: &antilinktime <minutes>")
    @commands.has_permissions(administrator=True)
    async def cmd_antilinktime(self, ctx, minutes: int = None):
        if minutes is None or minutes < 1:
            embed = discord.Embed(title="⏱️ Anti-Link Timeout Time", description="Set timeout duration in minutes.\n\n**Usage:** `&antilinktime 5`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        self.cursor.execute("UPDATE automod_settings SET antilink_duration = ? WHERE guild_id = ?", (minutes, ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Anti-Link timeout duration set to **{minutes} minutes**.", color=discord.Color.green()))

    # --- ANTIYOUTUBE CONFIGURATION COMMANDS ---
    @commands.command(name="antiyoutube", help="Toggle anti-youtube filter ON or OFF.\nUsage: &antiyoutube on / off")
    @commands.has_permissions(administrator=True)
    async def cmd_antiyoutube(self, ctx, status: str = None):
        if not status or status.lower() not in ["on", "off"]:
            embed = discord.Embed(title="🛡️ Anti-YouTube Settings", description="Toggle anti-youtube filter.\n\n**Usage:**\n`&antiyoutube on`\n`&antiyoutube off`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        val = 1 if status.lower() == "on" else 0
        self.cursor.execute("UPDATE automod_settings SET antiyoutube = ? WHERE guild_id = ?", (val, ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Anti-YouTube filter is now **{'Enabled (ON)' if val == 1 else 'Disabled (OFF)'}**.", color=discord.Color.green()))

    @commands.command(name="antiyoutubeaction", help="Set punishment for anti-youtube violation.\nUsage: &antiyoutubeaction delete / timeout / kick / ban")
    @commands.has_permissions(administrator=True)
    async def cmd_antiyoutubeaction(self, ctx, action: str = None):
        valid = ["delete", "timeout", "kick", "ban"]
        if not action or action.lower() not in valid:
            embed = discord.Embed(title="🛡️ Anti-YouTube Action", description="Set punishment when someone sends a YouTube link.\n\n**Valid Actions:** `delete`, `timeout`, `kick`, `ban`\n**Usage:** `&antiyoutubeaction delete`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        self.cursor.execute("UPDATE automod_settings SET antiyoutube_punishment = ? WHERE guild_id = ?", (action.lower(), ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Anti-YouTube punishment updated to: **{action.lower()}**.", color=discord.Color.green()))

    @commands.command(name="antiyoutubetime", help="Set timeout duration in minutes for anti-youtube.\nUsage: &antiyoutubetime <minutes>")
    @commands.has_permissions(administrator=True)
    async def cmd_antiyoutubetime(self, ctx, minutes: int = None):
        if minutes is None or minutes < 1:
            embed = discord.Embed(title="⏱️ Anti-YouTube Timeout Time", description="Set timeout duration in minutes.\n\n**Usage:** `&antiyoutubetime 5`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        self.cursor.execute("UPDATE automod_settings SET antiyoutube_duration = ? WHERE guild_id = ?", (minutes, ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Anti-YouTube timeout duration set to **{minutes} minutes**.", color=discord.Color.green()))

    # --- ANTISPAM CONFIGURATION COMMANDS ---
    @commands.command(name="antispam", help="Toggle anti-spam protection ON or OFF.\nUsage: &antispam on / off")
    @commands.has_permissions(administrator=True)
    async def cmd_antispam(self, ctx, status: str = None):
        if not status or status.lower() not in ["on", "off"]:
            embed = discord.Embed(title="🛡️ Anti-Spam Settings", description="Toggle anti-spam protection.\n\n**Usage:**\n`&antispam on`\n`&antispam off`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        val = 1 if status.lower() == "on" else 0
        self.cursor.execute("UPDATE automod_settings SET antispam = ? WHERE guild_id = ?", (val, ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Anti-Spam protection is now **{'Enabled (ON)' if val == 1 else 'Disabled (OFF)'}**.", color=discord.Color.green()))

    @commands.command(name="antispamlimit", help="Set message count and time window for spam.\nUsage: &antispamlimit <messages> <seconds>")
    @commands.has_permissions(administrator=True)
    async def cmd_antispamlimit(self, ctx, messages: int = None, seconds: int = None):
        if messages is None or seconds is None or messages < 1 or seconds < 1:
            embed = discord.Embed(title="⚙️ Anti-Spam Limit Settings", description="Set how many messages in how many seconds counts as spam.\n\n**Usage:** `&antispamlimit 5 5` (5 msgs in 5 seconds)", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        self.cursor.execute("UPDATE automod_settings SET antispam_limit = ?, antispam_seconds = ? WHERE guild_id = ?", (messages, seconds, ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Anti-spam limit updated: **{messages} messages** within **{seconds} seconds**.", color=discord.Color.green()))

    @commands.command(name="antispamaction", help="Set punishment for spamming.\nUsage: &antispamaction delete / timeout / kick / ban")
    @commands.has_permissions(administrator=True)
    async def cmd_antispamaction(self, ctx, action: str = None):
        valid = ["delete", "timeout", "kick", "ban"]
        if not action or action.lower() not in valid:
            embed = discord.Embed(title="🛡️ Anti-Spam Action", description="Set punishment when someone spams.\n\n**Valid Actions:** `delete`, `timeout`, `kick`, `ban`\n**Usage:** `&antispamaction timeout`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        self.cursor.execute("UPDATE automod_settings SET antispam_punishment = ? WHERE guild_id = ?", (action.lower(), ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Anti-Spam punishment updated to: **{action.lower()}**.", color=discord.Color.green()))

    @commands.command(name="antispamtime", help="Set timeout duration in minutes for spamming.\nUsage: &antispamtime <minutes>")
    @commands.has_permissions(administrator=True)
    async def cmd_antispamtime(self, ctx, minutes: int = None):
        if minutes is None or minutes < 1:
            embed = discord.Embed(title="⏱️ Anti-Spam Timeout Time", description="Set timeout duration in minutes.\n\n**Usage:** `&antispamtime 5`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        self.cursor.execute("UPDATE automod_settings SET antispam_duration = ? WHERE guild_id = ?", (minutes, ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Anti-Spam timeout duration set to **{minutes} minutes**.", color=discord.Color.green()))

    # --- BAD WORDS MANAGEMENT & CONFIG COMMANDS ---
    @commands.command(name="badwords", help="Toggle bad words filter ON/OFF or view list.\nUsage: &badwords on / off / view")
    @commands.has_permissions(administrator=True)
    async def cmd_badwords_toggle(self, ctx, status: str = None):
        if not status:
            # View banned words list if no argument provided
            self.cursor.execute("SELECT word FROM bad_words WHERE guild_id = ?", (ctx.guild.id,))
            rows = self.cursor.fetchall()
            if not rows:
                embed = discord.Embed(description="❌ There are no bad words in the blacklist for this server!", color=discord.Color.orange())
                return await ctx.send(embed=embed)
            word_list = ", ".join([f"`{row[0]}`" for row in rows])
            embed = discord.Embed(title=f"🛡️ Banned Words - {ctx.guild.name}", description=word_list, color=discord.Color.red())
            return await ctx.send(embed=embed)

        status = status.lower()
        if status in ["on", "off"]:
            val = 1 if status == "on" else 0
            self.cursor.execute("UPDATE automod_settings SET badwords = ? WHERE guild_id = ?", (val, ctx.guild.id))
            self.db.commit()
            return await ctx.send(embed=discord.Embed(description=f"✅ Bad Words filter is now **{'Enabled (ON)' if val == 1 else 'Disabled (OFF)'}**.", color=discord.Color.green()))
        else:
            embed = discord.Embed(title="🛡️ Bad Words Command", description="**Usage:**\n`&badwords on`\n`&badwords off`\n`&badwords` (to view list)", color=discord.Color.blue())
            await ctx.send(embed=embed)

    @commands.command(name="badwordsaction", help="Set punishment for bad words violation.\nUsage: &badwordsaction delete / timeout / kick / ban")
    @commands.has_permissions(administrator=True)
    async def cmd_badwordsaction(self, ctx, action: str = None):
        valid = ["delete", "timeout", "kick", "ban"]
        if not action or action.lower() not in valid:
            embed = discord.Embed(title="🛡️ Bad Words Action", description="Set punishment when someone uses a bad word.\n\n**Valid Actions:** `delete`, `timeout`, `kick`, `ban`\n**Usage:** `&badwordsaction delete`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        self.cursor.execute("UPDATE automod_settings SET badwords_punishment = ? WHERE guild_id = ?", (action.lower(), ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Bad Words punishment updated to: **{action.lower()}**.", color=discord.Color.green()))

    @commands.command(name="badwordstime", help="Set timeout duration in minutes for bad words.\nUsage: &badwordstime <minutes>")
    @commands.has_permissions(administrator=True)
    async def cmd_badwordstime(self, ctx, minutes: int = None):
        if minutes is None or minutes < 1:
            embed = discord.Embed(title="⏱️ Bad Words Timeout Time", description="Set timeout duration in minutes.\n\n**Usage:** `&badwordstime 5`", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        self.cursor.execute("UPDATE automod_settings SET badwords_duration = ? WHERE guild_id = ?", (minutes, ctx.guild.id))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ Bad Words timeout duration set to **{minutes} minutes**.", color=discord.Color.green()))

    @commands.command(name="addbadword", help="Add one or multiple bad words to the blacklist.\nUsage: &addbadword word1 word2, word3")
    @commands.has_permissions(administrator=True)
    async def addbadword(self, ctx, *, words: str = None):
        if not words:
            embed = discord.Embed(title="🚫 Add Bad Word(s)", description="Add one or multiple words to blacklist.\n\n**Usage:**\n`&addbadword badword1`\n`&addbadword word1, word2, word3`", color=discord.Color.blue())
            return await ctx.send(embed=embed)

        word_list = [w.strip().lower() for w in words.replace(",", " ").split() if w.strip()]
        added, exists = [], []

        for word in word_list:
            try:
                self.cursor.execute("INSERT INTO bad_words (guild_id, word) VALUES (?, ?)", (ctx.guild.id, word))
                added.append(word)
            except sqlite3.IntegrityError:
                exists.append(word)
        self.db.commit()

        embed = discord.Embed(title="🛡️ Bad Words Management", color=discord.Color.green())
        if added:
            embed.add_field(name="Successfully Added", value=", ".join([f"`{w}`" for w in added]), inline=False)
        if exists:
            embed.add_field(name="Already in Blacklist", value=", ".join([f"`{w}`" for w in exists]), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="removebadword", help="Remove a word from the server bad words blacklist.\nUsage: &removebadword <word>")
    @commands.has_permissions(administrator=True)
    async def removebadword(self, ctx, word: str = None):
        if not word:
            embed = discord.Embed(title="🚫 Remove Bad Word", description="Remove a word from blacklist.\n\n**Usage:**\n`&removebadword <word>`", color=discord.Color.blue())
            return await ctx.send(embed=embed)

        word = word.lower()
        self.cursor.execute("DELETE FROM bad_words WHERE guild_id = ? AND word = ?", (ctx.guild.id, word))
        self.db.commit()
        await ctx.send(embed=discord.Embed(description=f"✅ The word **'{word}'** has been removed from the blacklist.", color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
