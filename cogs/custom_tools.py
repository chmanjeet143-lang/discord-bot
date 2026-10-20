import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "custom_tools_config.json"

class CustomTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving custom tools config: {e}")

    # 1. Custom Embed Command
    @commands.command(name="embed", help="Creates an embed with the given text in the current channel.")
    @commands.has_permissions(manage_guild=True)
    async def create_embed(self, ctx, *, text: str):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        embed = discord.Embed(
            description=text,
            color=discord.Color.purple()
        )
        embed.set_footer(text="Moonlight Heaven • Developed By Zeus")
        await ctx.send(embed=embed)

    # 2. Reaction Role on Last Message (Supports multiple reactions on same message)
    @commands.command(name="reactionrole", help="Adds a reaction role to the last message/embed in the channel.")
    @commands.has_permissions(manage_guild=True)
    async def reaction_role(self, ctx, role: discord.Role, emoji: str):
        # Fetch last message in the channel (excluding the command message itself)
        target_msg = None
        async for m in ctx.channel.history(limit=5):
            if m.id != ctx.message.id:
                target_msg = m
                break

        if not target_msg:
            return await ctx.send("❌ Is channel me koi pichhla message nahi mila!", delete_after=5)

        try:
            await target_msg.add_reaction(emoji)
        except Exception as e:
            return await ctx.send(f"❌ Reaction add karne me error aayi (Check karein emoji valid hai ya nahi): {e}", delete_after=5)

        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        if "reaction_roles" not in self.config[guild_id]:
            self.config[guild_id]["reaction_roles"] = {}

        msg_id_str = str(target_msg.id)
        if msg_id_str not in self.config[guild_id]["reaction_roles"]:
            self.config[guild_id]["reaction_roles"][msg_id_str] = {}

        # Save mapping: emoji -> role_id (allows multiple roles on the same message)
        self.config[guild_id]["reaction_roles"][msg_id_str][emoji] = role.id
        self.save_config()

        await ctx.send(f"✅ Success! Is message par {emoji} dabane par ab **{role.name}** role mil jayega.", delete_after=5)

    # 3. Tag Auto-Reaction Command (Multiple roles supported)
    @commands.command(name="addreaction", help="Sets an auto-reaction when a specific role is tagged.")
    @commands.has_permissions(manage_guild=True)
    async def add_tag_reaction(self, ctx, role: discord.Role, emoji: str):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        if "tag_reactions" not in self.config[guild_id]:
            self.config[guild_id]["tag_reactions"] = {}

        self.config[guild_id]["tag_reactions"][str(role.id)] = emoji
        self.save_config()

        await ctx.send(f"✅ Auto-reaction set! Jab bhi **{role.name}** ko tag kiya jayega, bot {emoji} reaction dega.")

    # Listener for Reaction Roles (Add)
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.member or payload.member.bot or not payload.guild_id:
            return

        guild_id = str(payload.guild_id)
        if guild_id not in self.config:
            return

        rr = self.config[guild_id].get("reaction_roles", {})
        msg_id = str(payload.message_id)

        if msg_id in rr:
            emoji_str = str(payload.emoji)
            roles_map = rr[msg_id]
            
            matched_role_id = None
            for saved_emoji, r_id in roles_map.items():
                if emoji_str == saved_emoji or payload.emoji.name in saved_emoji:
                    matched_role_id = r_id
                    break

            if matched_role_id:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(matched_role_id)
                if role:
                    try:
                        await payload.member.add_roles(role)
                    except Exception as e:
                        print(f"Error adding role: {e}")

    # Listener for Reaction Roles (Remove)
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not payload.guild_id:
            return

        guild_id = str(payload.guild_id)
        if guild_id not in self.config:
            return

        rr = self.config[guild_id].get("reaction_roles", {})
        msg_id = str(payload.message_id)

        if msg_id in rr:
            emoji_str = str(payload.emoji)
            roles_map = rr[msg_id]
            
            matched_role_id = None
            for saved_emoji, r_id in roles_map.items():
                if emoji_str == saved_emoji or payload.emoji.name in saved_emoji:
                    matched_role_id = r_id
                    break

            if matched_role_id:
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                if member and not member.bot:
                    role = guild.get_role(matched_role_id)
                    if role:
                        try:
                            await member.remove_roles(role)
                        except Exception as e:
                            print(f"Error removing role: {e}")

    # Listener for Tag Auto-Reaction
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        if guild_id not in self.config:
            return

        tag_reactions = self.config[guild_id].get("tag_reactions", {})
        if not tag_reactions:
            return

        for role in message.role_mentions:
            role_id_str = str(role.id)
            if role_id_str in tag_reactions:
                emoji = tag_reactions[role_id_str]
                try:
                    await message.add_reaction(emoji)
                except Exception as e:
                    print(f"Error adding tag auto-reaction: {e}")

async def setup(bot):
    await bot.add_cog(CustomTools(bot))
