import discord
from discord.ext import commands
import json
import os

class Welcome2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "welcome_config_2.json"
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving welcome 2 config: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        if guild_id not in self.config:
            return

        data = self.config[guild_id]
        channel_id = data.get("channel_id")
        message_template = data.get("message")

        if not channel_id or not message_template:
            return

        channel = member.guild.get_channel(int(channel_id))
        if not channel:
            return

        final_message = message_template.replace("{user}", member.mention)

        try:
            await channel.send(final_message)
        except Exception as e:
            print(f"Error sending welcome 2 message: {e}")

    @commands.command(name="wlcm2setup", help="Sets up the second welcome message in the current channel.")
    @commands.has_permissions(administrator=True)
    async def setup_welcome_2(self, ctx):
        guild_id = str(ctx.guild.id)
        
        # Tera diya hua exact custom message format
        default_message = (
            "<:1_:1534159662063026187> Look who joined us! **Welcome to 🌜Moonlight Heaven ** {user}\n"
            "Great to have you here!<:cinna_flower:1553906067522588705> Check these out: \n"
            "<:GirlOwner:1553725816108621915> https://discord.com/channels/1531581818468569200/1533508168016072885\n"
            "<:GirlOwner:1553725816108621915> <#1533508556316217544> \n"
            "<:GirlOwner:1553725816108621915> <#1561036228474699887> \n"
            "Got questions? Just ping our <@&1533532066254159912> <:musafir_admin:1553725963563434064>"
        )

        self.config[guild_id] = {
            "channel_id": ctx.channel.id,
            "message": default_message
        }
        self.save_config()
        
        await ctx.send(f"✅ Welcome 2 successfully configured in {ctx.channel.mention} using your custom template!")

    @commands.command(name="wlcm2test", help="Tests the second welcome message instantly.")
    @commands.has_permissions(administrator=True)
    async def test_welcome_2(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("❌ No welcome 2 message configured yet! Run `&wlcm2setup` first.")

        data = self.config[guild_id]
        channel_id = data.get("channel_id")
        message_template = data.get("message")

        channel = ctx.guild.get_channel(int(channel_id))
        if not channel:
            return await ctx.send("❌ Configured welcome 2 channel not found!")

        final_message = message_template.replace("{user}", ctx.author.mention)

        try:
            await channel.send(final_message)
            await ctx.send(f"✅ Test welcome 2 message sent to {channel.mention}!")
        except Exception as e:
            await ctx.send(f"❌ Error sending test message: {e}")

async def setup(bot):
    await bot.add_cog(Welcome2(bot))
