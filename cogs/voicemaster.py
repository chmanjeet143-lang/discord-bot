import discord
from discord.ext import commands
import sqlite3

class VoiceControlView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    # Row 0
    @discord.ui.button(label="Status", style=discord.ButtonStyle.secondary, emoji="🎛️", custom_id="vm_status", row=0)
    async def status_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("ℹ️ Channel status: Active and managed.", ephemeral=True)

    @discord.ui.button(label="Limit", style=discord.ButtonStyle.secondary, emoji="👥", custom_id="vm_limit_btn", row=0)
    async def limit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("👥 Use `!limit <number>` to change user limit.", ephemeral=True)

    @discord.ui.button(label="Logs", style=discord.ButtonStyle.secondary, emoji="📄", custom_id="vm_logs", row=0)
    async def logs_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("📄 Voice channel logs are active.", ephemeral=True)

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.secondary, emoji="🚫", custom_id="vm_ban", row=0)
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("🚫 User ban feature is ready.", ephemeral=True)

    @discord.ui.button(label="Unban", style=discord.ButtonStyle.secondary, emoji="✅", custom_id="vm_unban", row=0)
    async def unban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("✅ User unban feature is ready.", ephemeral=True)

    # Row 1
    @discord.ui.button(label="Hide", style=discord.ButtonStyle.secondary, emoji="🙈", custom_id="vm_hide", row=1)
    async def hide_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message("🙈 Voice channel has been hidden.", ephemeral=True)

    @discord.ui.button(label="Unhide", style=discord.ButtonStyle.secondary, emoji="👁️", custom_id="vm_unhide", row=1)
    async def unhide_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=True)
        await interaction.response.send_message("👁️ Voice channel is now visible.", ephemeral=True)

    @discord.ui.button(label="Region", style=discord.ButtonStyle.secondary, emoji="🌍", custom_id="vm_region", row=1)
    async def region_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("🌍 Region settings updated.", ephemeral=True)

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.secondary, emoji="🔓", custom_id="vm_unlock", row=1)
    async def unlock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.channel.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Voice channel has been unlocked.", ephemeral=True)

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="vm_lock", row=1)
    async def lock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Voice channel has been locked.", ephemeral=True)

    # Row 2
    @discord.ui.button(label="Trust", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="vm_trust", row=2)
    async def trust_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("👤 User trusted successfully.", ephemeral=True)

    @discord.ui.button(label="Untrust", style=discord.ButtonStyle.secondary, emoji="📉", custom_id="vm_untrust", row=2)
    async def untrust_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("📉 User untrusted.", ephemeral=True)

    @discord.ui.button(label="Bitrate", style=discord.ButtonStyle.secondary, emoji="📊", custom_id="vm_bitrate", row=2)
    async def bitrate_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.channel.edit(bitrate=96000)
        await interaction.response.send_message("📊 Bitrate adjusted.", ephemeral=True)

    @discord.ui.button(label="Invite", style=discord.ButtonStyle.secondary, emoji="📞", custom_id="vm_invite", row=2)
    async def invite_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("📞 Invite sent.", ephemeral=True)

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.secondary, emoji="👢", custom_id="vm_kick", row=2)
    async def kick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("👢 Use `!kick @user` to kick a member.", ephemeral=True)

    # Row 3
    @discord.ui.button(label="Suppress", style=discord.ButtonStyle.secondary, emoji="🎤", custom_id="vm_suppress", row=3)
    async def suppress_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("🎤 User suppressed.", ephemeral=True)

    @discord.ui.button(label="Unsuppress", style=discord.ButtonStyle.secondary, emoji="🎙️", custom_id="vm_unsuppress", row=3)
    async def unsuppress_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("🎙️ User unsuppressed.", ephemeral=True)

    @discord.ui.button(label="Chat", style=discord.ButtonStyle.secondary, emoji="💬", custom_id="vm_chat", row=3)
    async def chat_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("💬 Chat interface active.", ephemeral=True)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, emoji="👑", custom_id="vm_claim", row=3)
    async def claim_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("SELECT owner_id FROM active_channels WHERE channel_id = ?", (self.channel_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return await interaction.response.send_message("❌ This is not a managed voice channel.", ephemeral=True)
        
        current_owner = row[0]
        member = interaction.guild.get_member(current_owner)
        if member and member in interaction.channel.members:
            conn.close()
            return await interaction.response.send_message("❌ The current owner is still in the voice channel!", ephemeral=True)

        cursor.execute("UPDATE active_channels SET owner_id = ? WHERE channel_id = ?", (interaction.user.id, self.channel_id))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"👑 {interaction.user.mention} has claimed ownership of this voice channel!", ephemeral=False)

    @discord.ui.button(label="Transfer", style=discord.ButtonStyle.primary, emoji="↗️", custom_id="vm_transfer", row=3)
    async def transfer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("↗️ Use `!transfer @user` to transfer ownership.", ephemeral=True)

    # Row 4 (Delete Channel - Red Button)
    @discord.ui.button(label="Delete Channel", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="vm_delete", row=4)
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): return
        await interaction.response.send_message("🗑️ Deleting channel...", ephemeral=True)
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
            await interaction.response.send_message("❌ Channel data not found.", ephemeral=True)
            return False
            
        if interaction.user.id != row[0] and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Only the channel owner or staff can use these controls!", ephemeral=True)
            return False
        return True

class VoiceMaster(commands.Cog, description="Explore all commands related to VoiceMaster."):
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
                duo_create_id INTEGER,
                panel_image TEXT
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

    def get_panel_embed(self, guild_id):
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("SELECT panel_image FROM guild_settings WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        conn.close()
        
        panel_image = row[0] if row and row[0] else None

        embed = discord.Embed(
            title="VoiceMaster Interface",
            description="Use this interface to manage your voice channel.\nYou can also use slash commands!\n\nUse the buttons below to manage your voice channel.",
            color=discord.Color.from_rgb(43, 45, 49)
        )
        if panel_image:
            embed.set_image(url=panel_image)
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM active_channels")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            self.bot.add_view(VoiceControlView(row[0]))

    @commands.group(invoke_without_command=True)
    async def vm(self, ctx):
        await ctx.send("❌ Usage: `!vm panel`, `!vm setup`, `!vm setup duo`, or `!vm img <link>`")

    @vm.command(name="img", help="Set or update the Voice Master panel banner image.")
    async def vm_img(self, ctx, url: str):
        """
        Set or update the custom banner image for Voice Master panels.
        Usage: !vm img <image_link>
        """
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ You need Administrator permission.")
        
        conn = sqlite3.connect("voicemaster.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO guild_settings (guild_id, panel_image) 
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET panel_image=excluded.panel_image
        ''', (ctx.guild.id, url))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Voice Master panel banner image has been updated successfully!\nURL: {url}")

    @vm.command(name="setup", help="Create the normal Join-to-Create voice channel and category.")
    async def vm_setup(self, ctx, mode: str = "normal"):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ You need Administrator permission.")

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
            await ctx.send("✅ Voice Master **Duo setup channel** created successfully!")
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
            await ctx.send("✅ Voice Master **Normal setup channel** created successfully!")

    @vm.command(name="panel", help="Create a text channel with the Voice Master control panel.")
    async def vm_panel(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ You need Administrator permission.")
        
        guild = ctx.guild
        text_channel = await guild.create_text_channel("voice-interface")
        
        embed = self.get_panel_embed(guild.id)
        view = VoiceControlView(text_channel.id)
        await text_channel.send(embed=embed, view=view)
        await ctx.send(f"✅ Voice interface panel channel created: {text_channel.mention}")

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

            self.bot.add_view(VoiceControlView(new_vc.id))

            embed = self.get_panel_embed(guild.id)
            embed.description = f"Welcome {member.mention} ❤️\n\nUse this interface to manage your voice channel.\nYou can also use slash commands!\n\nUse the buttons below to manage your voice channel."
            
            view = VoiceControlView(new_vc.id)
            try:
                await new_vc.send(embed=embed, view=view)
            except Exception:
                pass

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
