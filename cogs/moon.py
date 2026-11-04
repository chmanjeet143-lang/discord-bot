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

            # Cache ki jagah guild se fresh member data fetch karna taaki official clan tag mil sake
            fetched_member = await new_member.guild.fetch_member(new_member.id)
            
            user_obj = getattr(fetched_member, '_user', fetched_member)
            user_data = getattr(user_obj, '_data', {})
            
            clan_info = user_data.get('clan') if isinstance(user_data, dict) else None
            tag = clan_info.get('tag', '') if isinstance(clan_info, dict) else ''

            print(f"[DEBUG API] User: {new_member.name} | Fetched Clan Tag: '{tag}'")

            # Agar official tag match ho jaye
            if tag == self.target_tag:
                # Aap yahan apna success embed laga sakte hain
                pass

        except Exception as e:
            print(f"[CRITICAL ERROR in MoonTagTracker]: {e}")

async def setup(bot):
    await bot.add_cog(MoonTagTracker(bot))
    print("[LOADED] API Fetcher Tracker loaded successfully!")
