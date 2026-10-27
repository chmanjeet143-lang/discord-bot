import discord
from discord.ext import commands
import sqlite3

class VoiceHelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Voice Master",
                description="View all available Voice Master commands and usage.",
                emoji="🎙️",
                value="vm_commands_help"
            )
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            description="📁 **Category • Voice Master**\n\n"
                        "Here are all the available commands under **Voice Master**:\n\n"
                        "• `!vm panel` - Toggle or create the voice interface control channel.\n"
                        "Usage: `!vm panel`\n\n"
                        "• `!vm setup` - Create the normal Join-to-Create voice channel and category.\n"
                        "Usage: `!vm setup`\n\n"
                        "• `!vm setup duo` - Create the Duo Join-to-Create voice channel (Limit: 2).\n"
                        "Usage: `!vm setup duo`",
            color=discord.Color.from_rgb(43, 45, 49)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class VoiceHelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(VoiceHelpSelect())

class VoiceControlView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.red, emoji="🔒", custom_id="vm_lock", row=0)
    async def lock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Voice channel lock kar diya gaya hai.", ephemeral=True)

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.green, emoji="🔓", custom_id="vm_unlock", row=0)
    async def unlock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.channel.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Voice channel unlock kar diya gaya hai.", ephemeral=True)

    @discord.ui.button(label="Hide", style=discord.ButtonStyle.grey, emoji="🙈", custom_id="vm_hide", row=1)
    async def hide_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message("🙈 Voice channel hidden kar diya gaya hai.", ephemeral=True)

    @discord.ui.button(label="Unhide", style=discord.ButtonStyle.grey, emoji="👁️", custom_id="vm_unhide", row=1)
    async def unhide_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=True)
        await interaction.response.send_message("👁️ Voice channel visible kar diya gaya hai.", ephemeral=True)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.blurple, emoji="👑", custom_id="vm_claim", row=2)
    async def claim_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("SELECT owner_id FROM active_channels WHERE channel_id = ?", (self.channel_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return await interaction.response.send_message("❌ Yeh managed voice channel nahi hai.", ephemeral=True)
        
        current_owner = row[0]
        member = interaction.guild.get_member(current_owner)
        if member and member in interaction.channel.members:
            conn.close()
            return await interaction.response.send_message("❌ Current owner abhi bhi channel ke andar maujood hai!", ephemeral=True)

        cursor.execute("UPDATE active_channels SET owner_id = ? WHERE channel_id = ?", (interaction.user.id, self.channel_id))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"👑 {interaction.user.mention} ne is voice channel ki ownership claim kar li hai!", ephemeral=False)

    @discord.ui.button(label="Delete Channel", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="vm_delete", row=2)
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.response.send_message("🗑️ Channel delete kiya ja raha hai...", ephemeral=True)
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM active_channels WHERE channel_id = ?", (self.channel_id,))
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
            await interaction.response.send_message("❌ Channel data nahi mila.", ephemeral=True)
            return False
            
        if interaction.user.id != row[0] and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Sirf channel owner ya staff hi ise control kar sakte hain!", ephemeral=True)
            return False
        return True

class VoiceMaster(commands.Cog, description="Dynamic Voice Channel system with custom help format."):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                category_id INTEGER,
                normal_create_id INTEGER,
                duo_create_id INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_channels (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                owner_id INTEGER,
                channel_type TEXT
            )
        ''')
        conn.commit()
        conn.close()

    @commands.group(invoke_without_command=True)
    async def vm(self, ctx):
        """Voice Master help menu."""
        embed = discord.Embed(
            title="🎙️ Voice Master Help Menu",
            description="Neeche diye gaye dropdown menu se Voice Master category select karein.",
            color=discord.Color.teal()
        )
        view = VoiceHelpView()
        await ctx.send(embed=embed, view=view)

    @vm.command(name="setup")
    async def vm_setup(self, ctx, mode: str = "normal"):
        """Creates the Voice Master create-vc channel."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Aapko Administrator permission chahiye.")

        guild = ctx.guild
        category = discord.utils.get(guild.categories, name="🎙️ Voice Master")
        if not category:
            category = await guild.create_category("🎙️ Voice Master")
        
        if mode.lower() == "duo":
            create_channel = await guild.create_voice_channel("➕ Create Duo VC", category=category, user_limit=2)
            conn = sqlite3.connect("voicemaster.db")
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO guild_settings (guild_id, category_id, duo_create_id) 
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET category_id=excluded.category_id, duo_create_id=excluded.duo_create_id
            ''', (guild.id, category.id, create_channel.id))
            conn.commit()
            conn.close()
            await ctx.send("✅ Voice Master **Duo setup channel** successfully ban gaya hai!")
        else:
            create_channel = await guild.create_voice_channel("➕ Create VC", category=category)
            conn = sqlite3.connect("voicemaster.db")
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO guild_settings (guild_id, category_id, normal_create_id) 
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET category_id=excluded.category_id, normal_create_id=excluded.normal_create_id
            ''', (guild.id, category.id, create_channel.id))
            conn.commit()
            conn.close()
            await ctx.send("✅ Voice Master **Normal setup channel** successfully ban gaya hai!")

    @vm.command(name="panel")
    async def vm_panel(self, ctx):
        """Creates a text channel with the Voice Master control panel."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Aapko Administrator permission chahiye.")
        
        guild = ctx.guild
        text_channel = await guild.create_text_channel("voice-interface")
        
        embed = discord.Embed(
            title="VoiceMaster Interface",
            description="Use this interface to manage your voice channel.\nUse the buttons below.",
            color=discord.Color.teal()
        )
        view = VoiceControlView(text_channel.id)
        await text_channel.send(embed=embed, view=view)
        await ctx.send(f"✅ Voice interface panel channel successfully ban gaya hai: {text_channel.mention}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = member.guild
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, normal_create_id, duo_create_id FROM guild_settings WHERE guild_id = ?", (guild.id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return

        category_id, normal_create_id, duo_create_id = row

        # User joined create room
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

            # Send panel in newly created VC chat
            embed = discord.Embed(
                title="VoiceMaster Interface",
                description=f"Welcome {member.mention} ❤️\n\nUse this interface to manage your voice channel.",
                color=discord.Color.teal()
            )
            view = VoiceControlView(new_vc.id)
            try:
                await new_vc.send(embed=embed, view=view)
            except Exception:
                pass

        # Cleanup empty rooms
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
                conn.commit()
                conn.close()
                try:
                    await before.channel.delete()
                except Exception:
                    pass

async def setup(bot):
    await bot.add_cog(VoiceMaster(bot))
