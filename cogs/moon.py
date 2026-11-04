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
                return

            # Discord ke raw payload se official clan data nikalna
            old_data = getattr(old_member, '_data', {})
            new_data = getattr(new_member, '_data', {})

            old_clan = old_data.get('clan') if isinstance(old_data, dict) else None
            new_clan = new_data.get('clan') if isinstance(new_data, dict) else None

            # Clan object ke andar se 'tag' extract karna
            old_tag = old_clan.get('tag', '') if isinstance(old_clan, dict) else ''
            new_tag = new_clan.get('tag', '') if isinstance(new_clan, dict) else ''

            print(f"[DEBUG] User: {new_member.name} | Official Old Clan Tag: '{old_tag}' | Official New Clan Tag: '{new_tag}'")

            old_has_tag = (old_tag == self.target_tag)
            new_has_tag = (new_tag == self.target_tag)

            # Jab user official clan badge add kare
            if not old_has_tag and new_has_tag:
                embed = discord.Embed(
                    color=0x00FF00,
                    description=f"**{new_member.name}** Thank you for proudly adopting our server tag! 🎉\nYour support means the world to us, and we're thrilled to have you in the community! 🌟\nEvery tag you wear helps us grow stronger and more united. 🤝"
                )
                embed.set_author(name=str(new_member), icon_url=new_member.display_avatar.url)
                embed.set_footer(text=f"{new_member.name} adopted the server tag :)")
                await channel.send(embed=embed)
                print(f"[SUCCESS] {new_member.name} ne official clan tag adopt kiya!")

            # Jab user official clan badge remove kare
            elif old_has_tag and not new_has_tag:
                embed = discord.Embed(
                    color=0xFF0000,
                    description=f"**{new_member.name}** We noticed you removed our server tag. 💔\nThank you for your past support and for being a part of our journey! 🌟\nWe hope you continue to stay awesome and positive vibes! ✨"
                )
                embed.set_author(name=str(new_member), icon_url=new_member.display_avatar.url)
                embed.set_footer(text=f"{new_member.name} removed the server tag :(")
                await channel.send(embed=embed)
                print(f"[SUCCESS] {new_member.name} ne official clan tag remove kiya!")

        except Exception as e:
            print(f"[CRITICAL ERROR in MoonTagTracker]: {e}")

async def setup(bot):
    await bot.add_cog(MoonTagTracker(bot))
    print("[LOADED] Official Clan Badge Tracker successfully loaded!")
