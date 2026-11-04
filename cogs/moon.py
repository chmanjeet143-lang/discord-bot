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

            # Poora raw data print karke dekhte hain ki clan kahan hai
            print(f"[RAW DEBUG] Member Data: {getattr(new_member, '_data', {})}")

            new_user_data = getattr(new_member, '_data', {}).get('user', {})
            new_clan = new_user_data.get('clan') if isinstance(new_user_data, dict) else None
            new_tag = new_clan.get('tag', '') if isinstance(new_clan, dict) else ''

            print(f"[DEBUG] User: {new_member.name} | Found Tag: '{new_tag}'")

            if new_tag == self.target_tag:
                # Agar tag match ho jaye
                pass

        except Exception as e:
            print(f"[CRITICAL ERROR in MoonTagTracker]: {e}")

async def setup(bot):
    await bot.add_cog(MoonTagTracker(bot))
    print("[LOADED] Raw Debugger loaded successfully!")
