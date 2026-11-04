import discord
from discord.ext import commands

class MoonTagTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_tag = "M00N"
        self.log_channel_id = 1562820194236366868

    @commands.Cog.listener()
    async def on_member_update(self, old_member, new_member):
        try:
            channel = self.bot.get_channel(self.log_channel_id)
            if not channel:
                print(f"[DEBUG] Channel ID {self.log_channel_id} nahi mila!")
                return

            old_nick = old_member.nickname or old_member.name
            new_nick = new_member.nickname or new_member.name

            old_has_tag = self.target_tag in old_nick
            new_has_tag = self.target_tag in new_nick

            if not old_has_tag and new_has_tag:
                embed = discord.Embed(
                    color=0x00FF00,
                    description=f"**{new_member.name}** Thank you for proudly adopting our server tag! 🎉\nYour support means the world to us, and we're thrilled to have you in the community! 🌟\nEvery tag you wear helps us grow stronger and more united. 🤝"
                )
                embed.set_author(name=str(new_member), icon_url=new_member.display_avatar.url)
                embed.set_footer(text=f"{new_member.name} adopted the server tag :)")
                await channel.send(embed=embed)

            elif old_has_tag and not new_has_tag:
                embed = discord.Embed(
                    color=0xFF0000,
                    description=f"**{new_member.name}** We noticed you removed our server tag. 💔\nThank you for your past support and for being a part of our journey! 🌟\nWe hope you continue to stay awesome and positive vibes! ✨"
                )
                embed.set_author(name=str(new_member), icon_url=new_member.display_avatar.url)
                embed.set_footer(text=f"{new_member.name} removed the server tag :(")
                await channel.send(embed=embed)
        except Exception as e:
            print(f"[ERROR in MoonTagTracker]: {e}")

async def setup(bot):
    await bot.add_cog(MoonTagTracker(bot))
    print("[LOADED] MoonTagTracker cog successfully loaded!")
