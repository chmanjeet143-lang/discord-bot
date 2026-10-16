import discord
from discord.ext import commands
import io
import aiohttp
import re

DEFAULT_AVATAR = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60"

def create_embed(guild, title="", description="", color=0x2B2D31):
    thumbnail_url = guild.icon.url if guild and guild.icon else DEFAULT_AVATAR
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
    return embed

class Clone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clone")
    @commands.has_permissions(manage_emojis=True)
    async def clone_command(self, ctx):
        if not ctx.message.reference:
            return await ctx.send("❌ Please reply to a message containing a custom emoji or sticker that you want to clone!")

        try:
            referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except Exception:
            return await ctx.send("❌ Could not fetch the referenced message.")

        cloned_count = 0
        async with aiohttp.ClientSession() as session:
            # 1. Custom Emojis check karo
            emoji_matches = re.findall(r"<(a?):([a-zA-Z0-9\_]+):([0-9]+)>", referenced_msg.content)
            
            for animated, name, emoji_id in emoji_matches:
                extension = "gif" if animated == "a" else "png"
                url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}"
                
                async with session.get(url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        try:
                            await ctx.guild.create_custom_emoji(name=name, image=image_bytes, reason=f"Cloned by {ctx.author}")
                            cloned_count += 1
                        except Exception as e:
                            print(f"Error creating emoji: {e}")

            # 2. Custom Stickers check karo
            if referenced_msg.stickers:
                for sticker in referenced_msg.stickers:
                    url = sticker.url
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            try:
                                file = discord.File(io.BytesIO(image_bytes), filename=f"{sticker.name}.png")
                                await ctx.guild.create_sticker(name=sticker.name, description="Cloned sticker", emoji="✨", file=file, reason=f"Cloned by {ctx.author}")
                                cloned_count += 1
                            except Exception as e:
                                print(f"Error creating sticker: {e}")

        if cloned_count > 0:
            embed = create_embed(
                ctx.guild,
                title="✨ Successfully Cloned!",
                description=f"Successfully added **{cloned_count}** emoji/sticker(s) to **Moonlight Heaven**!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No valid custom emojis or stickers found in that replied message!")

async def setup(bot):
    await bot.add_cog(Clone(bot))
