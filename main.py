import discord
from discord.ext import commands
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Render Web Service ke liye chhota server jo port 10000 par chalega
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Moonlight Heaven Bot is alive!")

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

# Server ko background thread mein start karna
threading.Thread(target=run_server, daemon=True).start()

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

# Setup Hook to load all cogs automatically
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

# Bot Token (Yahan apna wahi token daal dein)
bot.run("YOUR_BOT_TOKEN_HERE")
