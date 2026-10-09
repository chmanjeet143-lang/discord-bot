import discord
from discord.ext import commands
import asyncio

# Intents Setup (Message content & guilds enabled)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Bot Prefix as '&'
bot = commands.Bot(command_prefix="&", intents=intents)

@bot.event
async def on_ready():
    print(f'-----------------------------------')
    print(f'Logged in as: {bot.user.name} (ID: {bot.user.id})')
    print(f'Moonlight Heaven Bot is 100% Online!')
    print(f'-----------------------------------')

# Function to load all cogs/extensions automatically
async def load_extensions():
    initial_cogs = [
        "cogs.tickets",          # Staff Recruitment Button Panel
        "cogs.support_tickets",  # Support Center Dropdown Panel
        "cogs.moderation",       # Moderation commands
        "cogs.utility",          # Utility commands
        "cogs.help_menu",        # Help menu
        "cogs.info"              # Info commands
    ]
    
    for cog in initial_cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded Cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load Cog {cog}: {e}")

async def main():
    async with bot:
        await load_extensions()
        # Apna Bot Token yahan daalein (ya apna purana token use karein)
        await bot.run("YOUR_BOT_TOKEN_HERE")

if __name__ == "__main__":
    # Agar aapka setup_hook wala tarika purana chal raha hai toh niche wala standard run use kar sakte hain:
    pass

# Alternative Standard Runner (Agar upar wala use na karna ho toh yeh use karein):
@bot.event
async def setup_hook():
    await load_extensions()

# Bot Token (Yahan apna token daal dein jo pehle se tha)
# bot.run("YOUR_BOT_TOKEN_HERE")
