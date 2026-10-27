import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "boost_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Boost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. Boost Channel Set karne ka command
    @commands.command(name="setboostchannel", help="Set the text channel where boost messages will be sent.")
    @commands.has_permissions(administrator=True)
    async def set_boost_channel(self, ctx, channel: discord.TextChannel):
        """Set the text channel where boost messages will be sent.
        Usage: &setboostchannel #channel"""
        config = load_config()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in config:
            config[guild_id] = {}
            
        config[guild_id]["channel_id"] = channel.id
        if "message" not in config[guild_id]:
            config[guild_id]["message"] = "🎉 Thank you {user} for boosting **{server}**! We now have {boost_count} boosts."
            
        save_config(config)
        
        embed = discord.Embed(
            description=f"✅ Boost channel successfully set to {channel.mention}!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    # 2. Custom Boost Message Set karne ka command
    @commands.command(name="setboostmsg", help="Set a custom boost message using placeholders.")
    @commands.has_permissions(administrator=True)
    async def set_boost_msg(self, ctx, *, message: str):
        """Set a custom boost message using placeholders ({user}, {server}, {boost_count}).
        Usage: &setboostmsg Thanks {user} for boosting {server}!"""
        config = load_config()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in config:
            config[guild_id] = {}
            
        config[guild_id]["message"] = message
        save_config(config)
        
        preview = message.format(user=ctx.author.mention, server=ctx.guild.name, boost_count=ctx.guild.premium_subscription_count)
        
        embed = discord.Embed(
            title="✅ Boost Message Updated",
            description=f"**New Message:**\n{message}\n\n**Preview:**\n{preview}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    # 3. Boost Test Command (New)
    @commands.command(name="boosttest", help="Test the boost message to see how it looks.")
    @commands.has_permissions(administrator=True)
    async def boost_test(self, ctx):
        """Test the boost message by sending a simulated boost notification.
        Usage: &boosttest"""
        config = load_config()
        guild_id = str(ctx.guild.id)
        
        if guild_id not in config or "channel_id" not in config[guild_id]:
            embed = discord.Embed(
                description="❌ Pehle `&setboostchannel` use karke boost channel set karein!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        channel_id = config[guild_id]["channel_id"]
        channel = ctx.guild.get_channel(channel_id)
        
        if not channel:
            embed = discord.Embed(
                description="❌ Set kiya gaya channel mil nahi raha hai. Kripya dobara channel set karein.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
            
        raw_msg = config[guild_id].get("message", "Thanks {user} for boosting!")
        formatted_msg = raw_msg.format(
            user=ctx.author.mention,
            server=ctx.guild.name,
            boost_count=ctx.guild.premium_subscription_count
        )
        
        # Designated channel par test message bhejna
        await channel.send(formatted_msg)
        
        embed = discord.Embed(
            description=f"✅ Test boost message successfully {channel.mention} par bhej diya gaya hai!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    # 4. Event Listener jo actual boost detect karega
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.premium_since is None and after.premium_since is not None:
            config = load_config()
            guild_id = str(after.guild.id)
            
            if guild_id in config and "channel_id" in config[guild_id]:
                channel_id = config[guild_id]["channel_id"]
                channel = after.guild.get_channel(channel_id)
                
                if channel:
                    raw_msg = config[guild_id].get("message", "Thanks {user} for boosting!")
                    
                    formatted_msg = raw_msg.format(
                        user=after.mention,
                        server=after.guild.name,
                        boost_count=after.guild.premium_subscription_count
                    )
                    
                    await channel.send(formatted_msg)

async def setup(bot):
    await bot.add_cog(Boost(bot))
