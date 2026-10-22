import discord
from discord.ext import commands
import json
import os

TAG_CONFIG_FILE = "tag_config.json"

def load_tag_config():
    if os.path.exists(TAG_CONFIG_FILE):
        try:
            with open(TAG_CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_tag_config(data):
    try:
        with open(TAG_CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except:
        pass

class TagSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.bot:
            return

        guild = after.guild
        guild_id = str(guild.id)
        config = load_tag_config()

        if guild_id not in config:
            return

        channel_id = config[guild_id].get("channel_id")
        if not channel_id:
            return

        channel = guild.get_channel(int(channel_id))
        if not channel:
            return

        before_clan = getattr(before, "clan", None)
        after_clan = getattr(after, "clan", None)

        # Check if the clan belongs specifically to *this* current server/guild
        before_is_our_guild = False
        if before_clan:
            b_gid = getattr(before_clan, "identity_guild_id", None) or getattr(before_clan, "guild_id", None)
            if str(b_gid) == guild_id:
                before_is_our_guild = True

        after_is_our_guild = False
        if after_clan:
            a_gid = getattr(after_clan, "identity_guild_id", None) or getattr(after_clan, "guild_id", None)
            if str(a_gid) == guild_id:
                after_is_our_guild = True

        # Trigger only when our server's tag is added or removed
        if not before_is_our_guild and after_is_our_guild:
            tag_text = getattr(after_clan, "tag", "Tag")
            await channel.send(f"🟢 **{after.mention}** ne hamare server ka tag **add** kar liya hai: `{tag_text}`")
        elif before_is_our_guild and not after_is_our_guild:
            await channel.send(f"🔴 **{after.mention}** ne hamare server ka tag **remove** kar diya hai.")

    @commands.command(name="tagsetup")
    @commands.has_permissions(manage_guild=True)
    async def tag_setup(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        config = load_tag_config()

        if guild_id not in config:
            config[guild_id] = {}

        config[guild_id]["channel_id"] = channel.id
        save_tag_config(config)

        await ctx.send(f"✅ Tag tracking channel successfully set to {channel.mention}! Ab koi bhi member **sirf hamare server ka tag** lagayega ya hatayega, tabhi bina embed ke yahan update aayega.")

async def setup(bot):
    await bot.add_cog(TagSystem(bot))
