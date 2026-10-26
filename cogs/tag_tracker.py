import discord
from discord.ext import commands

# Configuration
SERVER_TAG = "Moon"  # Apna server tag yahan daalein (Case-insensitive check hoga)
REWARD_ROLE_IDS = [
    123456789012345678,  # Extra Emojis perm role ID
    987654321098765432   # Extra Sticker perm role ID
]
LOG_CHANNEL_ID = 123456789012345678  # Jahan reward message bhejna hai (channel ID)

class TagTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_tag(self, member: discord.Member) -> bool:
        """User ke username, global name ya nickname mein tag check karta hai."""
        name_to_check = [
            member.name,
            member.global_name or "",
            member.nick or ""
        ]
        return any(SERVER_TAG.lower() in text.lower() for text in name_to_check)

    @commands.Cog.listener()
    async def on_member_update(before: discord.Member, after: discord.Member):
        # Bot updates ko ignore karein
        if after.bot:
            return

        before_has = self.has_tag(before)
        after_has = self.has_tag(after)

        # Agar pehle tag nahi tha, ab lagaa liya hai
        if not before_has and after_has:
            channel = after.guild.get_channel(LOG_CHANNEL_ID)
            added_roles = []

            for role_id in REWARD_ROLE_IDS:
                role = after.guild.get_role(role_id)
                if role and role not in after.roles:
                    try:
                        await after.add_roles(role, reason="Added server tag reward")
                        added_roles.append(role)
                    except discord.Forbidden:
                        print(f"Failed to add role {role.name} due to missing permissions.")

            # Embed message bhejne ke liye
            if channel:
                embed = discord.Embed(
                    title="Guild Tag Added",
                    description=f"{after.mention} Thanks for wearing our server tag!",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Tag", value=f"`{SERVER_TAG}`", inline=True)
                embed.set_thumbnail(url=after.display_avatar.url)
                
                # Agar kuch roles mile hain toh unka zikr kar sakte hain
                await channel.send(embed=embed)

        # Agar pehle tag tha, ab hata diya hai
        elif before_has and not after_has:
            for role_id in REWARD_ROLE_IDS:
                role = after.guild.get_role(role_id)
                if role and role in after.roles:
                    try:
                        await after.remove_roles(role, reason="Removed server tag")
                    except discord.Forbidden:
                        print(f"Failed to remove role {role.name} due to missing permissions.")

async def setup(bot):
    await bot.add_cog(TagTracker(bot))
