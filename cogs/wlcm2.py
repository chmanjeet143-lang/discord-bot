import discord
from discord.ext import commands
import json
import os

DEFAULT_WELCOME2_CHANNEL_ID = 1560207671942971482

BANNER_IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1532422031650455655/"
    "1573444294839369738/IMG_3070.png"
    "?ex=6b0207b1&is=6b00b631&hm=6b89a015d4120ecda71e296b62187932543d5f536676e671784601c07ec1aa7e&"
)

LAWZ_URL = "https://discord.com/channels/1531581818468569200/1561804737420992542"
HEX_URL = "https://discord.com/channels/1531581818468569200/1533508556316217544"
INTRO_URL = "https://discord.com/channels/1531581818468569200/1533508168016072885"


class Welcome2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "welcome_config_2.json"
        self.load_config()

    def _default_guild_config(self, channel_id: int) -> dict:
        return {
            "channel_id": int(channel_id),
            "image_url": BANNER_IMAGE_URL,
            "lawz_url": LAWZ_URL,
            "hex_url": HEX_URL,
            "intro_url": INTRO_URL,
        }

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving welcome 2 config: {e}")

    def ensure_default_welcome_for_guild(self, guild: discord.Guild):
        if not guild:
            return
        guild_id = str(guild.id)
        channel = guild.get_channel(DEFAULT_WELCOME2_CHANNEL_ID)
        if not channel:
            return

        if guild_id not in self.config or not self.config[guild_id].get("channel_id"):
            self.config[guild_id] = self._default_guild_config(DEFAULT_WELCOME2_CHANNEL_ID)
            self.save_config()

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.ensure_default_welcome_for_guild(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.ensure_default_welcome_for_guild(guild)

    def build_welcome_payload(self, member: discord.Member, config_data: dict):
        image_url = config_data.get("image_url", BANNER_IMAGE_URL)
        lawz_url = config_data.get("lawz_url", LAWZ_URL)
        hex_url = config_data.get("hex_url", HEX_URL)
        intro_url = config_data.get("intro_url", INTRO_URL)

        content = f"**Welcome to Love Heaven 🌸✨** {member.mention}"

        description = (
            f"🌺 **Check these out !**\n"
            f"💕 [**Lawz**]({lawz_url}) . [**Hex**]({hex_url})\n"
            f"▷◁ [**Intro**]({intro_url})\n"
            f"🍃 **Enjoy Ur Stay With Us** 🦋"
        )

        embed = discord.Embed(
            description=description,
            color=discord.Color.from_rgb(245, 215, 225),
        )

        avatar_url = member.display_avatar.url if member.display_avatar else None
        embed.set_author(name=member.name, icon_url=avatar_url)

        if image_url:
            embed.set_image(url=image_url)

        member_count = member.guild.member_count or 0
        embed.set_footer(text=f"We've Got {member_count} Members!")

        return content, embed

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id not in self.config:
            self.ensure_default_welcome_for_guild(member.guild)

        data = self.config.get(guild_id)
        if not data:
            return

        channel_id = data.get("channel_id")
        if not channel_id:
            return

        channel = member.guild.get_channel(int(channel_id))
        if not channel:
            return

        content, embed = self.build_welcome_payload(member, data)

        try:
            await channel.send(content=content, embed=embed)
        except Exception as e:
            print(f"Error sending welcome 2 message: {e}")

    @commands.command(name="wlcm2setup", help="Sets up the Love Heaven welcome 2 embed in the current channel.")
    @commands.has_permissions(administrator=True)
    async def setup_welcome_2(self, ctx):
        guild_id = str(ctx.guild.id)
        self.config[guild_id] = self._default_guild_config(ctx.channel.id)
        self.save_config()

        await ctx.send(f"✅ Welcome 2 setup complete in {ctx.channel.mention}! Use `&wlcm2test` to preview it.")

    @commands.command(name="wlcm2test", help="Tests the Love Heaven welcome 2 message instantly.")
    @commands.has_permissions(administrator=True)
    async def test_welcome_2(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            self.ensure_default_welcome_for_guild(ctx.guild)

        data = self.config.get(guild_id)
        if not data:
            return await ctx.send("❌ No welcome 2 message configured yet! Run `&wlcm2setup` first.")

        channel_id = data.get("channel_id")
        channel = ctx.guild.get_channel(int(channel_id)) if channel_id else ctx.channel

        if not channel:
            return await ctx.send("❌ Configured welcome 2 channel not found!")

        content, embed = self.build_welcome_payload(ctx.author, data)

        try:
            await channel.send(content=content, embed=embed)
            await ctx.send(f"✅ Test welcome 2 message sent to {channel.mention}!")
        except Exception as e:
            await ctx.send(f"❌ Error sending test message: {e}")


async def setup(bot):
    await bot.add_cog(Welcome2(bot))
