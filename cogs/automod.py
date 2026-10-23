import discord
from discord.ext import commands
import sqlite3
import time
from collections import defaultdict

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Database Setup for AutoMod Settings & Bad Words
        self.db = sqlite3.connect("automod.db")
        self.cursor = self.db.cursor()
        self.create_tables()
        
        # Anti-Spam Tracking Dictionary: { (guild_id, user_id): [timestamps] }
        self.message_tracker = defaultdict(list)

    def cog_unload(self):
        self.db.close()

    def create_tables(self):
        # Guild Settings for AutoMod features (1 = ON, 0 = OFF)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS automod_settings (
                guild_id INTEGER PRIMARY KEY,
                antilink INTEGER DEFAULT 1,
                antiyoutube INTEGER DEFAULT 0,
                antispam INTEGER DEFAULT 1,
                badwords INTEGER DEFAULT 1
            )
        ''')
        # Custom Bad Words List per guild
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bad_words (
                guild_id INTEGER,
                word TEXT,
                PRIMARY KEY (guild_id, word)
            )
        ''')
        self.db.commit()

    def get_settings(self, guild_id):
        self.cursor.execute("SELECT antilink, antiyoutube, antispam, badwords FROM automod_settings WHERE guild_id = ?", (guild_id,))
        res = self.cursor.fetchone()
        if not res:
            self.cursor.execute("INSERT INTO automod_settings (guild_id) VALUES (?)", (guild_id,))
            self.db.commit()
            return (1, 0, 1, 1) # Defaults: antilink ON, antiyoutube OFF, antispam ON, badwords ON
        return res

    # --- AUTOMOD LISTENER (MAIN CHECKER) ---
    @commands.Cog.listener()
    async def on_message(self, message):
        # Bots, DMs, aur Administrators par AutoMod apply nahi hoga
        if message.author.bot or not message.guild or message.author.guild_permissions.administrator:
            return

        guild_id = message.guild.id
        antilink, antiyoutube, antispam, badwords_enabled = self.get_settings(guild_id)
        content_lower = message.content.lower()

        try:
            # 1. Anti-YouTube Filter
            if antiyoutube and ("youtube.com" in content_lower or "youtu.be" in content_lower):
                await message.delete()
                return await message.channel.send(f"⚠️ {message.author.mention}, is server me YouTube links bhejna allowed nahi hai!", delete_after=5)

            # 2. Anti-Link / Anti-Invite Filter
            if antilink and ("discord.gg/" in content_lower or "http://" in content_lower or "https://" in content_lower or "www." in content_lower):
                # Agar antiyoutube on hai aur youtube link hai toh wo upar handle ho chuka hai, warna baaki links block hongi
                if not (antiyoutube and ("youtube.com" in content_lower or "youtu.be" in content_lower)):
                    await message.delete()
                    return await message.channel.send(f"⚠️ {message.author.mention}, is server me links bhejna strict mana hai!", delete_after=5)

            # 3. Bad Words (Profanity) Filter
            if badwords_enabled:
                self.cursor.execute("SELECT word FROM bad_words WHERE guild_id = ?", (guild_id,))
                banned_words = [row[0] for row in self.cursor.fetchall()]
                
                if any(word in content_lower for word in banned_words):
                    await message.delete()
                    return await message.channel.send(f"⚠️ {message.author.mention}, aapka message inappropriate hone ki wajah se delete kar diya gaya hai.", delete_after=5)

            # 4. Anti-Spam Filter (5 seconds me 5 messages threshold)
            if antispam:
                current_time = time.time()
                key = (guild_id, message.author.id)
                
                # Purane timestamps hatao (older than 5 seconds)
                self.message_tracker[key] = [t for t in self.message_tracker[key] if current_time - t < 5]
                self.message_tracker[key].append(current_time)

                if len(self.message_tracker[key]) >= 5:
                    await message.delete()
                    # User ko 5 minute ke liye timeout (mute) dena
                    try:
                        from datetime import timedelta
                        await message.author.timeout(timedelta(minutes=5), reason="AutoMod: Spamming detected")
                        await message.channel.send(f"🚨 {message.author.mention} ko spam karne ke liye **5 minutes ka Timeout** de diya gaya hai!", delete_after=7)
                    except:
                        await message.channel.send(f"⚠️ {message.author.mention}, kripya spam karna band karein!", delete_after=5)
                    
                    # Tracker clear karo taaki baar-baar spam na trigger ho
                    self.message_tracker[key] = []
                    return

        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"AutoMod Error: {e}")

    # --- AUTOMOD TOGGLE COMMANDS (ADMIN ONLY) ---

    @commands.command(name="antilink", help="Toggle anti-link protection on or off. Usage: &antilink on/off")
    @commands.has_permissions(administrator=True)
    async def antilink(self, ctx, status: str):
        status = status.lower()
        val = 1 if status == "on" else 0 if status == "off" else None
        if val is None:
            return await ctx.send("❌ Kripya sahi status dein: `&antilink on` ya `&antilink off`")
        
        self.cursor.execute("UPDATE automod_settings SET antilink = ? WHERE guild_id = ?", (val, ctx.guild.id))
        self.db.commit()
        state = "enabled (ON)" if val == 1 else "disabled (OFF)"
        await ctx.send(f"✅ Anti-Link protection successfully **{state}** kar di gayi hai.")

    @commands.command(name="antiyoutube", help="Toggle anti-youtube link filter on or off. Usage: &antiyoutube on/off")
    @commands.has_permissions(administrator=True)
    async def antiyoutube(self, ctx, status: str):
        status = status.lower()
        val = 1 if status == "on" else 0 if status == "off" else None
        if val is None:
            return await ctx.send("❌ Kripya sahi status dein: `&antiyoutube on` ya `&antiyoutube off`")
        
        self.cursor.execute("UPDATE automod_settings SET antiyoutube = ? WHERE guild_id = ?", (val, ctx.guild.id))
        self.db.commit()
        state = "enabled (ON)" if val == 1 else "disabled (OFF)"
        await ctx.send(f"✅ Anti-YouTube filter successfully **{state}** kar diya gaya hai.")

    @commands.command(name="antispam", help="Toggle anti-spam protection on or off. Usage: &antispam on/off")
    @commands.has_permissions(administrator=True)
    async def antispam(self, ctx, status: str):
        status = status.lower()
        val = 1 if status == "on" else 0 if status == "off" else None
        if val is None:
            return await ctx.send("❌ Kripya sahi status dein: `&antispam on` ya `&antispam off`")
        
        self.cursor.execute("UPDATE automod_settings SET antispam = ? WHERE guild_id = ?", (val, ctx.guild.id))
        self.db.commit()
        state = "enabled (ON)" if val == 1 else "disabled (OFF)"
        await ctx.send(f"✅ Anti-Spam protection successfully **{state}** kar di gayi hai.")

    # --- BAD WORDS MANAGEMENT COMMANDS ---

    @commands.command(name="addbadword", help="Add a word to the server bad words blacklist. Usage: &addbadword <word>")
    @commands.has_permissions(administrator=True)
    async def addbadword(self, ctx, word: str):
        word = word.lower()
        try:
            self.cursor.execute("INSERT INTO bad_words (guild_id, word) VALUES (?, ?)", (ctx.guild.id, word))
            self.db.commit()
            await ctx.send(f"✅ Banned words list me **'{word}'** successfully jodh diya gaya hai.")
        except sqlite3.IntegrityError:
            await ctx.send(f"⚠️ Yeh word pehle se hi blacklist me added hai!")

    @commands.command(name="removebadword", help="Remove a word from the server bad words blacklist. Usage: &removebadword <word>")
    @commands.has_permissions(administrator=True)
    async def removebadword(self, ctx, word: str):
        word = word.lower()
        self.cursor.execute("DELETE FROM bad_words WHERE guild_id = ? AND word = ?", (ctx.guild.id, word))
        self.db.commit()
        await ctx.send(f"✅ Blacklist se **'{word}'** hata diya gaya hai.")

    @commands.command(name="badwords", help="View all banned bad words in the server.")
    @commands.has_permissions(administrator=True)
    async def badwords(self, ctx):
        self.cursor.execute("SELECT word FROM bad_words WHERE guild_id = ?", (ctx.guild.id,))
        rows = self.cursor.fetchall()
        if not rows:
            return await ctx.send("❌ Is server ki bad words blacklist mein koi bhi word nahi hai!")
        
        word_list = ", ".join([f"`{row[0]}`" for row in rows])
        embed = discord.Embed(title=f"🛡️ Banned Words - {ctx.guild.name}", description=word_list, color=discord.Color.red())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
