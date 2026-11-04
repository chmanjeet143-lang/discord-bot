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

            # User object ya _user ke andar se data nikalna
            user_obj = getattr(new_member, '_user', new_member)
            user_data = getattr(user_obj, '_data', {})
            
            # Agar _data dictionary mein clan ho
            clan_info = user_data.get('clan') if isinstance(user_data, dict) else None
            tag = clan_info.get('tag', '') if isinstance(clan_info, dict) else ''

            print(f"[DEBUG] User: {new_member.name} | Detected Clan Tag: '{tag}'")

            # Agar tag match kare toh embed bhejain
            if tag == self.target_tag:
                # Aap yahan apna success message ya embed laga sakte hain
                pass

        except Exception as e:
            print(f"[CRITICAL ERROR in MoonTagTracker]: {e}")

async def setup(bot):
    await bot.add_cog(MoonTagTracker(bot))
    print("[LOADED] Updated MoonTagTracker loaded successfully!")
