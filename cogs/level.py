import discord
from discord.ext import commands, tasks
import json
import os
import random
import time
import datetime

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"
LEVELS_CONFIG_FILE = "levels_config.json"
LEVELS_DATA_FILE = "levels_data.json"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filename, data):
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
    except:
        pass

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.msg_cooldowns = {}  # {user_id: timestamp}
        self.vc_task.start()

    def cog_unload(self):
        self.vc_task.cancel()

    # --- BACKGROUND TASK FOR VC XP ---
    @tasks.loop(minutes=1)
    async def vc_task(self):
        data = load_json(LEVELS_DATA_FILE)
        config = load_json(LEVELS_CONFIG_FILE)

        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            if guild_id not in data:
                data[guild_id] = {}

            for vc in guild.voice_channels:
                valid_members = [m for m in vc.members if not m.bot]
                if len(valid_members) < 2:
                    continue

                for member in valid_members:
                    user_id = str(member.id)
                    if user_id not in data[guild_id]:
                        data[guild_id][user_id] = {"msg_xp": 0, "msg_lvl": 1, "vc_xp": 0, "vc_lvl": 1}

                    earned_xp = random.randint(10, 15)
                    data[guild_id][user_id]["vc_xp"] += earned_xp

                    lvl = data[guild_id][user_id]["vc_lvl"]
                    needed = lvl * 200

                    if data[guild_id][user_id]["vc_xp"] >= needed:
                        data[guild_id][user_id]["vc_lvl"] += 1
                        new_lvl = data[guild_id][user_id]["vc_lvl"]

                        # Check and assign role if it exists (5, 15, 40, 75, 100)
                        role_name = f"Level {new_lvl}"
                        role = discord.utils.get(guild.roles, name=role_name)
                        if role:
                            try:
                                await member.add_roles(role)
                            except:
                                pass

                        cfg = config.get(guild_id, {})
                        ch_id = cfg.get("vc_channel")
                        custom_msg = cfg.get("vc_msg", "{user} Congratulations! You reached **VC Level {level}** in voice channels! 🎙️")
                        
                        if ch_id:
                            channel = guild.get_channel(int(ch_id))
                            if channel:
                                formatted_msg = custom_msg.replace("{user}", member.mention).replace("{level}", str(new_lvl))
                                try:
                                    embed = create_embed(guild, title="🎙️ VC Level Up!", description=formatted_msg, color=discord.Color.green())
                                    await channel.send(embed=embed)
                                except:
                                    pass

        save_json(LEVELS_DATA_FILE, data)

    @vc_task.before_loop
    async def before_vc_task(self):
        await self.bot.wait_until_ready()

    # --- MESSAGE XP LISTENER ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = str(message.author.id)
        guild_id = str(message.guild.id)

        now = time.time()
        if user_id in self.msg_cooldowns and now - self.msg_cooldowns[user_id] < 60:
            return
        self.msg_cooldowns[user_id] = now

        data = load_json(LEVELS_DATA_FILE)
        config = load_json(LEVELS_CONFIG_FILE)

        if guild_id not in data:
            data[guild_id] = {}
        if user_id not in data[guild_id]:
            data[guild_id][user_id] = {"msg_xp": 0, "msg_lvl": 1, "vc_xp": 0, "vc_lvl": 1}

        earned_xp = random.randint(15, 25)
        data[guild_id][user_id]["msg_xp"] += earned_xp

        lvl = data[guild_id][user_id]["msg_lvl"]
        needed = lvl * 150

        if data[guild_id][user_id]["msg_xp"] >= needed:
            data[guild_id][user_id]["msg_lvl"] += 1
            new_lvl = data[guild_id][user_id]["msg_lvl"]

            # Check and assign role if it exists (5, 15, 40, 75, 100)
            role_name = f"Level {new_lvl}"
            role = discord.utils.get(message.guild.roles, name=role_name)
            if role:
                try:
                    await message.author.add_roles(role)
                except:
                    pass

            cfg = config.get(guild_id, {})
            ch_id = cfg.get("msg_channel", message.channel.id)
            custom_msg = cfg.get("msg_msg", "{user} Congratulations! You reached **Message Level {level}**! 🚀")

            channel = message.guild.get_channel(int(ch_id)) or message.channel
            formatted_msg = custom_msg.replace("{user}", message.author.mention).replace("{level}", str(new_lvl))
            try:
                embed = create_embed(message.guild, title="🎉 Message Level Up!", description=formatted_msg, color=discord.Color.gold())
                await channel.send(embed=embed)
            except:
                pass

        save_json(LEVELS_DATA_FILE, data)

    # --- SETUP COMMAND: Creates exactly 5 roles (5, 15, 40, 75, 100) ---
    @commands.command(name="levelupsetup", aliases=["lvlsetup"])
    @commands.has_permissions(administrator=True)
    async def levelup_setup(self, ctx):
        guild = ctx.guild
        embed = create_embed(guild, title="⚙️ Level System Setup", description="Creating specific milestone roles...", color=discord.Color.blue())
        msg = await ctx.send(embed=embed)

        milestones = [5, 15, 40, 75, 100]
        created_roles = []
        for level in milestones:
            role_name = f"Level {level}"
            existing = discord.utils.get(guild.roles, name=role_name)
            if not existing:
                try:
                    r = await guild.create_role(name=role_name, reason="Automatic Level Role Setup")
                    created_roles.append(r.name)
                except:
                    pass
            else:
                created_roles.append(existing.name)

        embed.description = f"✅ **Level system successfully initialized!**\n\nCreated/Checked Roles: `{', '.join(created_roles)}`\n\nUse:\n• `&setlvlmsg #channel <message>`\n• `&setvcmsg #channel <message>`"
        await msg.edit(embed=embed)

    # --- SET MESSAGE LEVEL CHANNEL & TEXT ---
    @commands.command(name="setlvlmsg")
    @commands.has_permissions(manage_guild=True)
    async def set_lvl_msg(self, ctx, channel: discord.TextChannel, *, message: str):
        config = load_json(LEVELS_CONFIG_FILE)
        guild_id = str(ctx.guild.id)
        if guild_id not in config:
            config[guild_id] = {}

        config[guild_id]["msg_channel"] = channel.id
        config[guild_id]["msg_msg"] = message
        save_json(LEVELS_CONFIG_FILE, config)

        embed = create_embed(ctx.guild, title="✅ Message Level Up Configured", description=f"**Channel:** {channel.mention}\n**Message:** {message}", color=discord.Color.green())
        await ctx.send(embed=embed)

    # --- SET VC LEVEL CHANNEL & TEXT ---
    @commands.command(name="setvcmsg")
    @commands.has_permissions(manage_guild=True)
    async def set_vc_msg(self, ctx, channel: discord.TextChannel, *, message: str):
        config = load_json(LEVELS_CONFIG_FILE)
        guild_id = str(ctx.guild.id)
        if guild_id not in config:
            config[guild_id] = {}

        config[guild_id]["vc_channel"] = channel.id
        config[guild_id]["vc_msg"] = message
        save_json(LEVELS_CONFIG_FILE, config)

        embed = create_embed(ctx.guild, title="✅ VC Level Up Configured", description=f"**Channel:** {channel.mention}\n**Message:** {message}", color=discord.Color.green())
        await ctx.send(embed=embed)

    # --- RANK COMMAND (COMBINED MESSAGE & VC) ---
    @commands.command(name="rank", aliases=["lvl", "level"])
    async def rank_command(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        guild_id = str(ctx.guild.id)
        data = load_json(LEVELS_DATA_FILE)

        user_data = data.get(guild_id, {}).get(str(member.id), {"msg_xp": 0, "msg_lvl": 1, "vc_xp": 0, "vc_lvl": 1})

        msg_lvl = user_data["msg_lvl"]
        msg_xp = user_data["msg_xp"]
        msg_needed = msg_lvl * 150

        vc_lvl = user_data["vc_lvl"]
        vc_xp = user_data["vc_xp"]
        vc_needed = vc_lvl * 200

        m_prog = min(msg_xp / msg_needed, 1.0)
        m_bar = "█" * int(m_prog * 10) + "—" * (10 - int(m_prog * 10))

        v_prog = min(vc_xp / vc_needed, 1.0)
        v_bar = "█" * int(v_prog * 10) + "—" * (10 - int(v_prog * 10))

        desc = (
            f"💬 **Message Rank**\n"
            f"• Level: **{msg_lvl}** | XP: `{msg_xp} / {msg_needed}`\n"
            f"`[{m_bar}]` ({int(m_prog * 100)}%)\n\n"
            f"🎙️ **Voice Channel Rank**\n"
            f"• Level: **{vc_lvl}** | XP: `{vc_xp} / {vc_needed}`\n"
            f"`[{v_bar}]` ({int(v_prog * 100)}%)"
        )

        embed = create_embed(ctx.guild, title=f"📊 Rank Card — {member.name}", description=desc, color=discord.Color.blue())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))
