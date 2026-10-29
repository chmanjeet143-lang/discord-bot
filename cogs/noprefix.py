import discord
from discord.ext import commands
import json
import os

# JSON file ka path
DATA_FILE = "noprefix.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class NoPrefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. &no prefix add / remove / list group command
    @commands.group(name="no", invoke_without_command=True)
    async def no_prefix(self, ctx):
        await ctx.send("❌ Use `&no prefix add @user`, `&no prefix remove @user`, ya `&no prefix list`.")

    @no_prefix.group(name="prefix", invoke_without_command=True)
    async def no_prefix_sub(self, ctx):
        await ctx.send("❌ Sahi format use karein: `&no prefix add/remove/list`")

    # &no prefix add <user>
    @no_prefix_sub.command(name="add")
    @commands.has_permissions(administrator=True)
    async def no_prefix_add(self, ctx, member: discord.Member):
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data:
            data[guild_id] = []

        if member.id in data[guild_id]:
            return await ctx.send(f"⚠️ **{member.display_name}** pehle se hi no-prefix list mein hai!")

        data[guild_id].append(member.id)
        save_data(data)
        await ctx.send(f"✅ Successfully **{member.display_name}** ko no-prefix list mein add kar diya gaya hai!")

    # &no prefix remove <user>
    @no_prefix_sub.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def no_prefix_remove(self, ctx, member: discord.Member):
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or member.id not in data[guild_id]:
            return await ctx.send(f"❌ **{member.display_name}** no-prefix list mein maujood nahi hai!")

        data[guild_id].remove(member.id)
        save_data(data)
        await ctx.send(f"✅ Successfully **{member.display_name}** ko no-prefix list se hata diya gaya hai!")

    # &no prefix list
    @no_prefix_sub.command(name="list")
    async def no_prefix_list(self, ctx):
        data = load_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id]:
            return await ctx.send("📂 Is server par koi bhi user no-prefix list mein nahi hai.")

        mentions = [f"<@{uid}>" for uid in data[guild_id]]
        
        embed = discord.Embed(
            setTitle="📜 Server No-Prefix Users",
            description="\n".join(mentions),
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    # 2. Listener: Jab no-prefix user bina prefix ke message kare
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        data = load_data()
        guild_id = str(message.guild.id)
        
        # Check agar user is guild ki no-prefix list mein hai
        if guild_id in data and message.author.id in data[guild_id]:
            # Agar message '&' ya kisi aur prefix se shuru nahi hota, toh usko command banakar process karein
            # (Aapka bot ka default prefix check karke ya direct invoke kara sakte hain)
            prefix = "&" # Aapke bot ka jo bhi prefix ho
            if not message.content.startswith(prefix):
                # Message ko command mein convert karne ke liye bot ka process_commands use hota hai
                # Lekin uske liye message content ke aage prefix lagana padega temporarily
                message.content = prefix + message.content
                await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(NoPrefix(bot))
