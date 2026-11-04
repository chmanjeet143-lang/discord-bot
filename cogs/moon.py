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
            print(f"[DEBUG] Member update detect hua: {new_member.name}")
            
            channel = self.bot.get_channel(self.log_channel_id)
            if not channel:
                print(f"[ERROR] Log channel ID {self.log_channel_id} nahi mila! Channel ID check karein.")
                return

            # Clan badge / Server tag check karna (Discord ke naye attribute ke mutabiq)
            old_clan = getattr(old_member, 'clan', None)
            new_clan = getattr(new_member, 'clan', None)

            old_tag = old_clan.tag if old_clan else ""
            new_tag = new_clan.tag if new_clan else ""

            print(f"[DEBUG] Old Tag: '{old_tag}' | New Tag: '{new_tag}'")

            old_has_tag = (old_tag == self.target_tag)
            new_has_tag = (new_tag == self.target_tag)

            # Jab user tag add kare
            if not old_has_tag and new_has_tag:
                embed = discord.Embed(
                    color=0x00FF00,
                    description=f"**{new_member.name}** Thank you for proudly adopting our server tag! 🎉\nYour support means the world to us, and we're thrilled to have you in the community! 🌟\nEvery tag you wear helps us grow stronger and more united. 🤝"
                )
                embed.set_author(name=str(new_member), icon_url=new_member.display_avatar.url)
                embed.set_footer(text=f"{new_member.name} adopted the server tag :)")
                await channel.send(embed=embed)
                print(f"[SUCCESS] {new_member.name} ne tag adopt kar liya hai!")

            # Jab user tag remove kare
            elif old_has_tag and not new_has_tag:
                embed = discord.Embed(
                    color=0xFF0000,
                    description=f"**{new_member.name}** We noticed you removed our server tag. 💔\nThank you for your past support and for being a part of our journey! 🌟\nWe hope you continue to stay awesome and positive vibes! ✨"
                )
                embed.set_author(name=str(new_member), icon_url=new_member.display_avatar.url)
                embed.set_footer(text=f"{new_member.name} removed the server tag :(")
                await channel.send(embed=embed)
                print(f"[SUCCESS] {new_member.name} ne tag remove kar diya hai!")

        except Exception as e:
            # Agar koi bhi error aayega toh woh yahan direct print ho jayega
            print(f"[CRITICAL ERROR in MoonTagTracker]: {e}")

async def setup(bot):
    await bot.add_cog(MoonTagTracker(bot))
    print("[LOADED] MoonTagTracker cog successfully load ho gaya hai!")
