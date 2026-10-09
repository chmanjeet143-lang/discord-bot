import discord
from discord.ext import commands

# Intents Setup
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

# Setup Hook to load all cogs automatically before bot starts
async def setup_hook():
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

# Bot Token (Yahan apna wahi purana bot token daal dein)
bot.run("YOUR_BOT_TOKEN_HERE")
