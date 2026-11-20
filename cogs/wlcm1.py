import discord
from discord.ext import commands
import json
import os

BANNER_IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1532422031650455655/"
    "1573444294839369738/IMG_3070.png"
    "?ex=6b0207b1&is=6b00b631&hm=6b89a015d4120ecda71e296b62187932543d5f536676e671784601c07ec1aa7e&"
)

LAWZ_URL = "https://discord.com/channels/1531581818468569200/1561804737420992542"
HEX_URL = "https://discord.com/channels/1531581818468569200/1533508556316217544"
INTRO_URL = "https://discord.com/channels/1531581818468569200/1533508168016072885"


class Welcome1(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "welcome_config.json"
        self.load_config()

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
            print(f"Error saving welcome config: {e}")

    def build_welcome_payload(self, member: discord.Member, config_data: dict):
        content_template = config_data.get("content", "Welcome to love heaven {user}")
        embed_title = config_data.get("title", "Welcome to Love Heaven 🌸✨")
        image_url = config_data.get("image_url", BANNER_IMAGE_URL)

        lawz_url = config_data.get("lawz_url", LAWZ_URL)
        hex_url = config_data.get("hex_url", HEX_URL)
        intro_url = config_data.get("intro_url", INTRO_URL)

        content = content_template.replace("{user}", member.mention)

        description = (
            f"🌺 **Check these out !**\n"
            f"💕 [**Lawz**]({lawz_url}) . [**Hex**]({hex_url})\n"
            f"▷◁ [**Intro**]({intro_url})\n"
            f"🍃 **Enjoy Ur Stay With Us** 🦋"
        )

        embed = discord.Embed(
            title=embed_title,
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
            return

        data = self.config[guild_id]
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
            print(f"Error sending welcome message: {e}")

    @commands.command(name="wlcm1setup", help="Sets up the Love Heaven welcome embed in the current channel.")
    @commands.has_permissions(administrator=True)
    async def setup_welcome_1(self, ctx):
        guild_id = str(ctx.guild.id)

        self.config[guild_id] = {
            "channel_id": ctx.channel.id,
            "content": "Welcome to love heaven {user}",
            "title": "Welcome to Love Heaven 🌸✨",
            "image_url": BANNER_IMAGE_URL,
            "lawz_url": LAWZ_URL,
            "hex_url": HEX_URL,
            "intro_url": INTRO_URL,
        }
        self.save_config()

        await ctx.send(f"✅ Welcome 1 setup complete in {ctx.channel.mention}! Use `&wlcm1test` to preview it.")

    @commands.command(name="wlcm1test", help="Tests the Love Heaven welcome message instantly.")
    @commands.has_permissions(administrator=True)
    async def test_welcome_1(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            return await ctx.send("❌ No welcome message configured yet! Run `&wlcm1setup` first.")

        data = self.config[guild_id]
        channel_id = data.get("channel_id")
        channel = ctx.guild.get_channel(int(channel_id)) if channel_id else ctx.channel

        if not channel:
            return await ctx.send("❌ Configured welcome channel not found!")

        content, embed = self.build_welcome_payload(ctx.author, data)

        try:
            await channel.send(content=content, embed=embed)
            await ctx.send(f"✅ Test welcome message sent to {channel.mention}!")
        except Exception as e:
            await ctx.send(f"❌ Error sending test message: {e}")


async def setup(bot):
    await bot.add_cog(Welcome1(bot))
