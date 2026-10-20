import discord
from discord.ext import commands, tasks
import json
import os
import time

CONFIG_FILE = "bump_config.json"
DISBOARD_ID = 302094752740937728  # Disboard bot ID

class BumpSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.bump_checker.start()

    def cog_unload(self):
        self.bump_checker.cancel()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving bump config: {e}")

    # Setup Command: &bumpsetup <role>
    @commands.command(name="bumpsetup", help="Sets up the bump reminder system in this channel.")
    @commands.has_permissions(manage_guild=True)
    async def bump_setup(self, ctx, role: discord.Role):
        guild_id = str(ctx.guild.id)
        
        self.config[guild_id] = {
            "channel_id": ctx.channel.id,
            "role_id": role.id,
            "last_bump_time": 0,
            "reminder_sent": True
        }
        self.save_config()

        embed = discord.Embed(
            title="✅ Bump System Setup Successful!",
            description=f"**Channel:** {ctx.channel.mention}\n**Role to Ping:** {role.mention}\n\nTimer shuru ho chuka hai! Ab se har successful bump ke 2 ghante baad reminder bheja jayega.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Moonlight Heaven • Bump System")
        await ctx.send(embed=embed)

    # Listen to messages for Disboard bump success
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return

        guild_id = str(message.guild.id)
        if guild_id not in self.config:
            return

        cfg = self.config[guild_id]

        # Check if message is from Disboard and indicates a successful bump
        if message.author.id == DISBOARD_ID:
            is_success = False
            if message.embeds:
                for embed in message.embeds:
                    if embed.description and "Bump done!" in embed.description:
                        is_success = True
            
            if is_success:
                current_time = time.time()
                cfg["last_bump_time"] = current_time
                cfg["reminder_sent"] = False
                self.save_config()

                # Find who bumped using interaction
                user = None
                if message.interaction and message.interaction.user:
                    user = message.interaction.user
                
                user_mention = user.mention if user else "@User"

                # Exact thank you message requested
                thank_text = f"✨ Much appreciated, {user_mention} ‧₊˚. Your bump keeps Moonlight Heaven 🌙 shining bright at the top ❤️"
                
                try:
                    channel = message.guild.get_channel(cfg["channel_id"])
                    if channel:
                        await channel.send(thank_text)
                    else:
                        await message.channel.send(thank_text)
                except Exception as e:
                    print(f"Error sending bump thank you: {e}")

    # Background task loop checking every 60 seconds if 2 hours have passed
    @tasks.loop(seconds=60)
    async def bump_checker(self):
        current_time = time.time()
        for guild_id, cfg in self.config.items():
            if cfg.get("last_bump_time", 0) == 0 or cfg.get("reminder_sent", True):
                continue

            # 2 hours = 7200 seconds
            elapsed_time = current_time - cfg["last_bump_time"]
            if elapsed_time >= 7200:
                guild = self.bot.get_guild(int(guild_id))
                if not guild:
                    continue

                channel = guild.get_channel(cfg["channel_id"])
                role = guild.get_role(cfg["role_id"])

                if channel and role:
                    # Exact reminder message requested with role ping
                    reminder_text = f"✨ Ready to Glow? 🌙\nTime to give Moonlight Heaven a quick boost! Use the `/bump` command to keep us shining at the top ✨\n{role.mention}"
                    try:
                        await channel.send(reminder_text)
                    except Exception as e:
                        print(f"Error sending bump reminder: {e}")

                cfg["reminder_sent"] = True
                self.save_config()

    @bump_checker.before_loop
    async def before_bump_checker(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(BumpSystem(bot))
