import discord
from discord.ext import commands
import sqlite3
import asyncio

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.guild_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("voicemaster.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            category_id INTEGER,
            normal_create_id INTEGER,
            duo_create_id INTEGER
        )
    '''\)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_channels (
            channel_id INTEGER PRIMARY KEY,
            guild_id INTEGER,
            owner_id INTEGER,
            channel_type TEXT
        )
    '''\)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trusted_users (
            channel_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (channel_id, user_id)
        )
    '''\)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            channel_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (channel_id, user_id)
        )
    '''\)
    conn.commit()
    conn.close()

init_db()

# --- INTERACTIVE CONTROL PANEL VIEW ---
class VoiceControlView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.red, emoji="ð", custom_id="vm_lock", row=0)
    async def lock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("ð Voice channel has been locked.", ephemeral=True)

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.green, emoji="ð", custom_id="vm_unlock", row=0)
    async def unlock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.channel.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("ð Voice channel has been unlocked.", ephemeral=True)

    @discord.ui.button(label="Hide", style=discord.ButtonStyle.grey, emoji="ð", custom_id="vm_hide", row=1)
    async def hide_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message("ð Voice channel is now hidden.", ephemeral=True)

    @discord.ui.button(label="Unhide", style=discord.ButtonStyle.grey, emoji="ðï¸", custom_id="vm_unhide", row=1)
    async def unhide_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=True)
        await interaction.response.send_message("ðï¸ Voice channel is now visible.", ephemeral=True)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.blurple, emoji="ð", custom_id="vm_claim", row=2)
    async def claim_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("SELECT owner_id FROM active_channels WHERE channel_id = ?", (self.channel_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return await interaction.response.send_message("â This is not a managed voice channel.", ephemeral=True)
        
        current_owner = row[0]
        member = interaction.guild.get_member(current_owner)
        
        if member and member in interaction.channel.members:
            conn.close()
            return await interaction.response.send_message("â The current owner is still in the voice channel!", ephemeral=True)

        cursor.execute("UPDATE active_channels SET owner_id = ? WHERE channel_id = ?", (interaction.user.id, self.channel_id))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"ð {interaction.user.mention} has claimed ownership of this voice channel!", ephemeral=False)

    @discord.ui.button(label="Delete Channel", style=discord.ButtonStyle.danger, emoji="ðï¸", custom_id="vm_delete", row=2)
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.response.send_message("ðï¸ Deleting channel...", ephemeral=True)
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM active_channels WHERE channel_id = ?", (self.channel_id,))
        cursor.execute("DELETE FROM trusted_users WHERE channel_id = ?", (self.channel_id,))
        cursor.execute("DELETE FROM banned_users WHERE channel_id = ?", (self.channel_id,))
        conn.commit()
        conn.close()
        await interaction.channel.delete()

    async def check_owner(self, interaction: discord.Interaction) -> bool:
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("SELECT owner_id FROM active_channels WHERE channel_id = ?", (self.channel_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            await interaction.response.send_message("â Channel data not found.", ephemeral=True)
            return False
            
        owner_id = row[0]
        if interaction.user.id != owner_id:
            conn = sqlite3.connect("voicemaster.db")
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM trusted_users WHERE channel_id = ? AND user_id = ?", (self.channel_id, interaction.user.id))
            is_trusted = cursor.fetchone()
            conn.close()
            
            if not is_trusted and not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("â Only the channel owner or trusted members can use these controls!", ephemeral=True)
                return False
        return True

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Voicemaster.py is online and active!")

# --- BOT COMMANDS ---
@bot.group(invoke_without_command=True)
async def vm(ctx):
    await ctx.send("â Usage: `!vm setup`, `!vm setup duo`, or `!vm panel`")

@vm.command(name="setup")
async def vm_setup(ctx, mode: str = "normal"):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("â You need **Administrator** permissions to setup Voice Master.")

    guild = ctx.guild
    category = await guild.create_category("ðï¸ Voice Master")
    
    if mode.lower() == "duo":
        create_channel = await guild.create_voice_channel("â Create Duo VC", category=category, user_limit=2)
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO guild_settings (guild_id, category_id, duo_create_id) VALUES (?, ?, ?)", 
                       (guild.id, category.id, create_channel.id))
        conn.commit()
        conn.close()
        await ctx.send("â Voicemaster **Duo** setup completed successfully!")
    else:
        create_channel = await guild.create_voice_channel("â Create VC", category=category)
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO guild_settings (guild_id, category_id, normal_create_id) VALUES (?, ?, ?)", 
                       (guild.id, category.id, create_channel.id))
        conn.commit()
        conn.close()
        await ctx.send("â Voicemaster **Normal** setup completed successfully!")

@vm.command(name="panel")
async def vm_panel(ctx):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("â You need Administrator permissions.")
    
    embed = discord.Embed(
        title="VoiceMaster Interface",
        description="Use this interface to manage your voice channel.\nUse the buttons below to manage your voice channel.",
        color=discord.Color.teal()
    )
    view = VoiceControlView(ctx.channel.id)
    await ctx.send(embed=embed, view=view)

# --- PREFIX COMMANDS FOR VC ---
@bot.command(name="lock")
async def cmd_lock(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("â You must be in a voice channel.")
    channel = ctx.author.voice.channel
    await channel.set_permissions(ctx.guild.default_role, connect=False)
    await ctx.message.add_reaction("ð")

@bot.command(name="unlock")
async def cmd_unlock(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("â You must be in a voice channel.")
    channel = ctx.author.voice.channel
    await channel.set_permissions(ctx.guild.default_role, connect=True)
    await ctx.message.add_reaction("ð")

@bot.command(name="limit")
async def cmd_limit(ctx, limit: int):
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("â You must be in a voice channel.")
    channel = ctx.author.voice.channel
    await channel.edit(user_limit=limit)
    await ctx.message.add_reaction("â")

@bot.command(name="kick")
async def cmd_kick(ctx, member: discord.Member):
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("â You must be in a voice channel.")
    channel = ctx.author.voice.channel
    if member.voice and member.voice.channel == channel:
        await member.move_to(None)
        await ctx.message.add_reaction("ð¢")
    else:
        await ctx.send("â That member is not in your voice channel.")

# --- VOICE STATE HANDLER ---
@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    conn = sqlite3.connect("voicemaster.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category_id, normal_create_id, duo_create_id FROM guild_settings WHERE guild_id = ?", (guild.id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return

    category_id, normal_create_id, duo_create_id = row

    # 1. User joined create room
    if after.channel and after.channel.id in (normal_create_id, duo_create_id):
        is_duo = (after.channel.id == duo_create_id)
        limit = 2 if is_duo else 0
        channel_type = "duo" if is_duo else "normal"
        
        category = guild.get_channel(category_id)
        
        new_vc = await guild.create_voice_channel(
            name=f"{member.display_name}'s Room",
            category=category,
            user_limit=limit
        )
        
        await member.move_to(new_vc)
        
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO active_channels (channel_id, guild_id, owner_id, channel_type) VALUES (?, ?, ?, ?)",
                       (new_vc.id, guild.id, member.id, channel_type))
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="VoiceMaster Interface",
            description=f"Welcome {member.mention} â¤ï¸\n\nUse this interface or prefix commands (`!lock`, `!unlock`, `!limit`, `!kick`) to manage your voice channel.",
            color=discord.Color.teal()
        )
        view = VoiceControlView(new_vc.id)
        try:
            await new_vc.send(embed=embed, view=view)
        except Exception:
            pass

    # 2. Cleanup empty rooms
    if before.channel:
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM active_channels WHERE channel_id = ?", (before.channel.id,))
        res = cursor.fetchone()
        conn.close()

        if res and len(before.channel.members) == 0:
            conn = sqlite3.connect("voicemaster.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_channels WHERE channel_id = ?", (before.channel.id,))
            cursor.execute("DELETE FROM trusted_users WHERE channel_id = ?", (before.channel.id,))
            cursor.execute("DELETE FROM banned_users WHERE channel_id = ?", (before.channel.id,))
            conn.commit()
            conn.close()
            try:
                await before.channel.delete()
            except Exception:
                pass

# bot.run("TOKEN")
