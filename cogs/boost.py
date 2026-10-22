import discord
from discord.ext import commands
import json
import os

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"
BOOST_CONFIG_FILE = "boost_config.json"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

def load_boost_config():
    if os.path.exists(BOOST_CONFIG_FILE):
        try:
            with open(BOOST_CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_boost_config(data):
    try:
        with open(BOOST_CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except:
        pass

class BoostSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.bot:
            return

        # Check if user started boosting the server
        if before.premium_since is None and after.premium_since is not None:
            guild = after.guild
            guild_id = str(guild.id)
            config = load_boost_config()

            if guild_id in config:
                channel_id = config[guild_id].get("channel_id")
                if channel_id:
                    channel = guild.get_channel(int(channel_id))
                    if channel:
                        default_msg = (
                            "<:boosters:1534157159418560542> ** BOOST ALERT ! **\n"
                            "Huge thanks to {user} for boosting the server ! <:cute_billi:1534157984001822791>\n\n"
                            "We really appreciate your awesome support !"
                        )
                        custom_msg = config[guild_id].get("message", default_msg)
                        formatted_msg = custom_msg.replace("{user}", after.mention)

                        try:
                            embed = create_embed(
                                guild,
                                title="🚀 New Server Boost!",
                                description=formatted_msg,
                                color=discord.Color.magenta()
                            )
                            await channel.send(embed=embed)
                        except:
                            pass

    @commands.command(name="boostsetup")
    @commands.has_permissions(manage_guild=True)
    async def boost_setup(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        config = load_boost_config()

        if guild_id not in config:
            config[guild_id] = {}

        config[guild_id]["channel_id"] = channel.id
        default_msg = (
            "<:boosters:1534157159418560542> ** BOOST ALERT ! **\n"
            "Huge thanks to {user} for boosting the server ! <:cute_billi:1534157984001822791>\n\n"
            "We really appreciate your awesome support !"
        )
        config[guild_id]["message"] = default_msg
        save_boost_config(config)

        embed = create_embed(
            ctx.guild,
            title="⚙️ Boost Alert Configured",
            description=f"Successfully set boost alert channel to {channel.mention}!\n\n**Message Preview:**\n" + default_msg.replace("{user}", ctx.author.mention),
            color=discord.Color.magenta()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BoostSystem(bot))
