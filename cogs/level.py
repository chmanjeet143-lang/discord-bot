import discord
from discord.ext import commands, tasks
import sqlite3
import math
import time
import io
from PIL import Image, ImageDraw, ImageFont, ImageOps
import aiohttp

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        
        # Database Connection Setup
        self.db = sqlite3.connect("levels.db")
        self.cursor = self.db.cursor()
        self.create_tables()
        
        # Start Voice XP Loop
        self.voice_xp_loop.start()

    def cog_unload(self):
        self.voice_xp_loop.cancel()
        self.db.close()

    def create_tables(self):
        # Users XP Table with background URL support
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                guild_id INTEGER,
                msg_xp INTEGER DEFAULT 0,
                vc_xp INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                bg_url TEXT DEFAULT NULL,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        # Guild Settings Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                msg_channel INTEGER DEFAULT 0,
                vc_channel INTEGER DEFAULT 0,
                msg_text TEXT DEFAULT 'Congratulations {user}, you just advanced to level {level} through texting! 🎉',
                vc_text TEXT DEFAULT 'Great job {user}, your voice activity earned you level {level}! 🎙️'
            )
        ''')
        # Role Rewards Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS rewards (
                guild_id INTEGER,
                level INTEGER,
                role_id INTEGER,
                PRIMARY KEY (guild_id, level)
            )
        ''')
        self.db.commit()

    def get_settings(self, guild_id):
        self.cursor.execute("SELECT msg_channel, vc_channel, msg_text, vc_text FROM guild_settings WHERE guild_id = ?", (guild_id,))
        res = self.cursor.fetchone()
        if not res:
            self.cursor.execute("INSERT INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
            self.db.commit()
            return (0, 0, 'Congratulations {user}, you just advanced to level {level} through texting! 🎉', 'Great job {user}, your voice activity earned you level {level}! 🎙️')
        return res

    def calculate_level(self, xp):
        return int(math.sqrt(xp / 100))

    def xp_for_level(self, level):
        return (level + 1) ** 2 * 100

    # --- MESSAGE XP LISTENER ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        current_time = time.time()

        # Cooldown check (60 seconds)
        if user_id in self.cooldowns and current_time - self.cooldowns[user_id] < 60:
            return
        self.cooldowns[user_id] = current_time

        self.cursor.execute("SELECT msg_xp, vc_xp, level FROM users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        data = self.cursor.fetchone()
        
        earned_msg_xp = 20
        if not data:
            new_msg_xp = earned_msg_xp
            new_vc_xp = 0
            total_xp = new_msg_xp
            new_level = self.calculate_level(total_xp)
            self.cursor.execute("INSERT INTO users (user_id, guild_id, msg_xp, vc_xp, xp, level) VALUES (?, ?, ?, ?, ?, ?)", 
                                (user_id, guild_id, new_msg_xp, new_vc_xp, total_xp, new_level))
        else:
            old_msg_xp, vc_xp, old_level = data
            new_msg_xp = old_msg_xp + earned_msg_xp
            total_xp = new_msg_xp + vc_xp
            new_level = self.calculate_level(total_xp)
            self.cursor.execute("UPDATE users SET msg_xp = ?, xp = ?, level = ? WHERE user_id = ? AND guild_id = ?", 
                                (new_msg_xp, total_xp, new_level, user_id, guild_id))
        
        self.db.commit()

        # Check Level Up & Send Embed Message
        if data and new_level > data[2]:
            msg_chan, _, msg_txt, _ = self.get_settings(guild_id)
            channel = message.guild.get_channel(msg_chan) or message.channel
            
            formatted_text = msg_txt.replace("{user}", message.author.mention).replace("{level}", str(new_level))
            
            embed = discord.Embed(title="🎉 Level Up! (Text)", description=formatted_text, color=discord.Color.green())
            embed.set_thumbnail(url=message.author.display_avatar.url)
            await channel.send(embed=embed)
            
            await self.check_rewards(message.author, new_level)

    # --- VOICE XP BACKGROUND LOOP ---
    @tasks.loop(minutes=5.0)
    async def voice_xp_loop(self):
        for guild in self.bot.guilds:
            msg_chan, vc_chan, _, vc_txt = self.get_settings(guild.id)
            for vc in guild.voice_channels:
                active_members = [m for m in vc.members if not m.bot and not m.voice.self_mute]
                if len(active_members) >= 2:
                    for member in active_members:
                        self.cursor.execute("SELECT msg_xp, vc_xp, level FROM users WHERE user_id = ? AND guild_id = ?", (member.id, guild.id))
                        data = self.cursor.fetchone()
                        
                        earned_vc_xp = 15
                        if not data:
                            msg_xp = 0
                            new_vc_xp = earned_vc_xp
                            total_xp = new_vc_xp
                            new_level = self.calculate_level(total_xp)
                            self.cursor.execute("INSERT INTO users (user_id, guild_id, msg_xp, vc_xp, xp, level) VALUES (?, ?, ?, ?, ?, ?)", 
                                                (member.id, guild.id, msg_xp, new_vc_xp, total_xp, new_level))
                        else:
                            msg_xp, old_vc_xp, old_level = data
                            new_vc_xp = old_vc_xp + earned_vc_xp
                            total_xp = msg_xp + new_vc_xp
                            new_level = self.calculate_level(total_xp)
                            self.cursor.execute("UPDATE users SET vc_xp = ?, xp = ?, level = ? WHERE user_id = ? AND guild_id = ?", 
                                                (new_vc_xp, total_xp, new_level, member.id, guild.id))
                        self.db.commit()

                        if data and new_level > data[2]:
                            channel = guild.get_channel(vc_chan) or guild.system_channel
                            if channel:
                                formatted_text = vc_txt.replace("{user}", member.mention).replace("{level}", str(new_level))
                                embed = discord.Embed(title="🎙️ Level Up! (Voice)", description=formatted_text, color=discord.Color.blue())
                                embed.set_thumbnail(url=member.display_avatar.url)
                                await channel.send(embed=embed)
                            await self.check_rewards(member, new_level)

    @voice_xp_loop.before_loop
    async def before_voice_loop(self):
        await self.bot.wait_until_ready()

    async def check_rewards(self, member, level):
        self.cursor.execute("SELECT role_id FROM rewards WHERE guild_id = ? AND level = ?", (member.guild.id, level))
        res = self.cursor.fetchone()
        if res:
            role = member.guild.get_role(res[0])
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass

    # --- MODERN BANNER & OVERLAPPING AVATAR RANK CARD GENERATOR ---
    async def generate_rank_card(self, member, msg_xp, vc_xp, total_xp, level, rank_pos, bg_url):
        card = Image.new("RGBA", (900, 350), (24, 25, 28, 255))
        draw = ImageDraw.Draw(card)

        # Top Banner Area (0 to 140 height)
        if bg_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(bg_url) as resp:
                        if resp.status == 200:
                            bg_bytes = await resp.read()
                            bg_img = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
                            bg_img = bg_img.resize((900, 140))
                            card.paste(bg_img, (0, 0))
            except:
                draw.rectangle([0, 0, 900, 140], fill=(45, 52, 70, 255))
        else:
            draw.rectangle([0, 0, 900, 140], fill=(45, 52, 70, 255))

        # Lower Body Area Background
        draw.rectangle([0, 140, 900, 350], fill=(24, 25, 28, 255))

        # Outer Border Outline
        draw.rounded_rectangle([10, 10, 890, 340], radius=16, outline=(88, 101, 242, 180), width=3)

        # Avatar overlapping banner and lower body
        avatar_url = member.display_avatar.replace(size=128, format="png").url
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as resp:
                if resp.status == 200:
                    avatar_bytes = await resp.read()
                    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                    avatar_img = avatar_img.resize((130, 130))
                    
                    mask = Image.new("L", (130, 130), 0)
                    draw_mask = ImageDraw.Draw(mask)
                    draw_mask.ellipse((0, 0, 130, 130), fill=255)
                    avatar_img = ImageOps.fit(avatar_img, mask.size, centering=(0.5, 0.5))
                    avatar_img.putalpha(mask)
                    
                    card.paste(avatar_img, (45, 75), avatar_img)
                    draw.ellipse([42, 72, 178, 208], outline=(114, 137, 218, 255), width=4)

        try:
            font_name = ImageFont.truetype("arial.ttf", 36)
            font_sub = ImageFont.truetype("arial.ttf", 20)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except:
            font_name = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # User Details
        draw.text((200, 155), member.display_name, fill=(255, 255, 255), font=font_name)
        draw.text((200, 200), f"RANK: #{rank_pos}   •   LEVEL: {level}", fill=(114, 137, 218), font=font_sub)
        
        breakdown_text = f"💬 Msg XP: {msg_xp}  |  🎙️ VC XP: {vc_xp}"
        draw.text((200, 230), breakdown_text, fill=(180, 187, 196), font=font_small)

        # Progress Bar Calculations
        current_level_xp = self.xp_for_level(level - 1) if level > 0 else 0
        next_level_xp = self.xp_for_level(level)
        xp_needed_this_lvl = next_level_xp - current_level_xp
        xp_user_has = total_xp - current_level_xp
        
        if xp_needed_this_lvl <= 0:
            percentage = 1.0
        else:
            percentage = max(0.0, min(1.0, xp_user_has / xp_needed_this_lvl))

        bar_x, bar_y, bar_w, bar_h = 200, 275, 650, 26
        draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=12, fill=(47, 49, 54))
        
        fill_width = int(bar_w * percentage)
        if fill_width > 0:
            draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_h], radius=12, fill=(88, 101, 242))

        xp_text = f"{total_xp} / {next_level_xp} XP"
        draw.text((bar_x + 240, bar_y + 4), xp_text, fill=(255, 255, 255), font=font_small)

        buffer = io.BytesIO()
        card.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    # --- CUSTOM BACKGROUND COMMAND ---
    @commands.command(name="setbg", help="Set a custom background image for your rank card using image URL or attachment.")
    async def setbg(self, ctx, url: str = None):
        if not url and ctx.message.attachments:
            url = ctx.message.attachments[0].url
        
        if not url:
            return await ctx.send("❌ Kripya image ka URL dein ya image attach karein!")
        
        self.cursor.execute("SELECT user_id FROM users WHERE user_id = ? AND guild_id = ?", (ctx.author.id, ctx.guild.id))
        data = self.cursor.fetchone()
        if not data:
            self.cursor.execute("INSERT INTO users (user_id, guild_id, bg_url) VALUES (?, ?, ?)", (ctx.author.id, ctx.guild.id, url))
        else:
            self.cursor.execute("UPDATE users SET bg_url = ? WHERE user_id = ? AND guild_id = ?", (url, ctx.author.id, ctx.guild.id))
        self.db.commit()
        await ctx.send("✅ Aapka custom rank card background successfully set ho gaya hai!")

    # --- USER COMMANDS ---
    @commands.command(name="rank", help="Check your current level, XP breakdown, and stylish rank card.")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        guild_id = ctx.guild.id

        self.cursor.execute("SELECT msg_xp, vc_xp, xp, level, bg_url FROM users WHERE user_id = ? AND guild_id = ?", (member.id, guild_id))
        data = self.cursor.fetchone()
        
        msg_xp = data[0] if data else 0
        vc_xp = data[1] if data else 0
        total_xp = data[2] if data else 0
        level = data[3] if data else 0
        bg_url = data[4] if data and len(data) > 4 else None

        self.cursor.execute("SELECT user_id FROM users WHERE guild_id = ? ORDER BY xp DESC", (guild_id,))
        all_users = self.cursor.fetchall()
        rank_pos = 1
        for idx, row in enumerate(all_users):
            if row[0] == member.id:
                rank_pos = idx + 1
                break

        async with ctx.typing():
            buffer = await self.generate_rank_card(member, msg_xp, vc_xp, total_xp, level, rank_pos, bg_url)
            file = discord.File(buffer, filename="rank.png")
            await ctx.send(file=file)

    @commands.command(name="leaderboard", aliases=["lb"], help="Check the top active users in the server.")
    async def leaderboard(self, ctx):
        guild_id = ctx.guild.id
        self.cursor.execute("SELECT user_id, msg_xp, vc_xp, xp, level FROM users WHERE guild_id = ? ORDER BY xp DESC LIMIT 10", (guild_id,))
        top_users = self.cursor.fetchall()

        if not top_users:
            return await ctx.send("❌ Is server me abhi tak koi leveling data nahi mila!")

        embed = discord.Embed(title=f"🏆 Leaderboard - {ctx.guild.name}", color=discord.Color.gold())
        description = ""
        for idx, (uid, m_xp, v_xp, total_x, lvl) in enumerate(top_users, start=1):
            user = ctx.guild.get_member(uid)
            name = user.name if user else f"User ID: {uid}"
            description += f"**{idx}.** {name} — Level: **{lvl}** (Total: {total_x} XP | 💬 {m_xp} | 🎙️ {v_xp})\n"

        embed.description = description
        await ctx.send(embed=embed)

    # --- ADMIN CONFIGURATION COMMANDS ---
    @commands.command(name="setmsgchannel", help="Set the channel for text message level-up notifications.")
    @commands.has_permissions(administrator=True)
    async def setmsgchannel(self, ctx, channel: discord.TextChannel):
        self.cursor.execute("UPDATE guild_settings SET msg_channel = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
        self.db.commit()
        await ctx.send(f"✅ Text level-up channel successfully set to {channel.mention}!")

    @commands.command(name="setvcchannel", help="Set the channel for voice XP level-up notifications.")
    @commands.has_permissions(administrator=True)
    async def setvcchannel(self, ctx, channel: discord.TextChannel):
        self.cursor.execute("UPDATE guild_settings SET vc_channel = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
        self.db.commit()
        await ctx.send(f"✅ Voice level-up channel successfully set to {channel.mention}!")

    @commands.command(name="setmsgtext", help="Customize the text level-up message.")
    @commands.has_permissions(administrator=True)
    async def setmsgtext(self, ctx, *, message: str):
        self.cursor.execute("UPDATE guild_settings SET msg_text = ? WHERE guild_id = ?", (message, ctx.guild.id))
        self.db.commit()
        await ctx.send(f"✅ Text level-up message successfully update ho gaya hai!")

    @commands.command(name="setvctext", help="Customize the voice level-up message.")
    @commands.has_permissions(administrator=True)
    async def setvctext(self, ctx, *, message: str):
        self.cursor.execute("UPDATE guild_settings SET vc_text = ? WHERE guild_id = ?", (message, ctx.guild.id))
        self.db.commit()
        await ctx.send(f"✅ Voice level-up message successfully update ho gaya hai!")

    @commands.command(name="addreward", help="Set a role reward for a specific level.")
    @commands.has_permissions(administrator=True)
    async def addreward(self, ctx, level: int, role: discord.Role):
        self.cursor.execute("INSERT OR REPLACE INTO rewards (guild_id, level, role_id) VALUES (?, ?, ?)", (ctx.guild.id, level, role.id))
        self.db.commit()
        await ctx.send(f"✅ Successfully added reward: Level **{level}** par {role.mention} role milega!")

    @commands.command(name="removereward", help="Remove the role reward from a specific level.")
    @commands.has_permissions(administrator=True)
    async def removereward(self, ctx, level: int):
        self.cursor.execute("DELETE FROM rewards WHERE guild_id = ? AND level = ?", (ctx.guild.id, level))
        self.db.commit()
        await ctx.send(f"✅ Level **{level}** ka role reward hata diya gaya hai.")

    @commands.command(name="rewards", help="View the list of all level role rewards.")
    async def rewards(self, ctx):
        self.cursor.execute("SELECT level, role_id FROM rewards WHERE guild_id = ? ORDER BY level ASC", (ctx.guild.id,))
        rows = self.cursor.fetchall()
        if not rows:
            return await ctx.send("❌ Is server me koi level rewards configured nahi hain!")
        
        embed = discord.Embed(title=f"🎁 Level Rewards - {ctx.guild.name}", color=discord.Color.purple())
        desc = ""
        for lvl, rid in rows:
            role = ctx.guild.get_role(rid)
            role_name = role.mention if role else f"Deleted Role (ID: {rid})"
            desc += f"Level **{lvl}** ➔ {role_name}\n"
        embed.description = desc
        await ctx.send(embed=embed)

    @commands.command(name="givexp", help="Add custom XP to a user.")
    @commands.has_permissions(administrator=True)
    async def givexp(self, ctx, member: discord.Member, amount: int):
        self.cursor.execute("SELECT msg_xp, vc_xp, xp, level FROM users WHERE user_id = ? AND guild_id = ?", (member.id, ctx.guild.id))
        data = self.cursor.fetchone()
        if not data:
            new_msg_xp = amount
            vc_xp = 0
            total_xp = new_msg_xp
            new_level = self.calculate_level(total_xp)
            self.cursor.execute("INSERT INTO users (user_id, guild_id, msg_xp, vc_xp, xp, level) VALUES (?, ?, ?, ?, ?, ?)", (member.id, ctx.guild.id, new_msg_xp, vc_xp, total_xp, new_level))
        else:
            msg_xp, vc_xp, old_total, old_lvl = data
            new_msg_xp = msg_xp + amount
            total_xp = new_msg_xp + vc_xp
            new_level = self.calculate_level(total_xp)
            self.cursor.execute("UPDATE users SET msg_xp = ?, xp = ?, level = ? WHERE user_id = ? AND guild_id = ?", (new_msg_xp, total_xp, new_level, member.id, ctx.guild.id))
        self.db.commit()
        await ctx.send(f"✅ {member.mention} ko **{amount} XP** add kar diye gaye hain!")

    @commands.command(name="removexp", help="Remove XP from a user.")
    @commands.has_permissions(administrator=True)
    async def removexp(self, ctx, member: discord.Member, amount: int):
        self.cursor.execute("SELECT msg_xp, vc_xp, xp, level FROM users WHERE user_id = ? AND guild_id = ?", (member.id, ctx.guild.id))
        data = self.cursor.fetchone()
        if not data:
            return await ctx.send(f"❌ {member.mention} ke paas koi XP data nahi hai.")
        
        msg_xp, vc_xp, old_total, old_lvl = data
        new_msg_xp = max(0, msg_xp - amount)
        total_xp = new_msg_xp + vc_xp
        new_level = self.calculate_level(total_xp)
        self.cursor.execute("UPDATE users SET msg_xp = ?, xp = ?, level = ? WHERE user_id = ? AND guild_id = ?", (new_msg_xp, total_xp, new_level, member.id, ctx.guild.id))
        self.db.commit()
        await ctx.send(f"✅ {member.mention} se **{amount} XP** kam kar diye gaye hain!")

async def setup(bot):
    await bot.add_cog(Leveling(bot))
