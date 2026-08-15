import discord
from discord.ext import commands


class HelpDropdown(discord.ui.Select):

  def __init__(self):
    options = [
        discord.SelectOption(
            label="Moderation",
            description="Kick, ban, clear and mute commands",
            emoji="🛡️",
        ),
        discord.SelectOption(
            label="Music",
            description="Play, skip and queue songs",
            emoji="🎵",
        ),
        discord.SelectOption(
            label="Fun Commands",
            description="Games and entertainment features",
            emoji="✨",
        ),
    ]
    super().__init__(
        placeholder="Select a module to see...",
        min_values=1,
        max_values=1,
        options=options,
    )

  async def callback(self, interaction: discord.Interaction):
    if self.values[0] == "Moderation":
      embed = discord.Embed(
          title="🛡️ Moderation Commands",
          description=(
              "Server control commands:\n\n`.kick` - Member ko kick"
              " karein\n`.ban` - Member ko ban karein\n`.clear` - Messages delete"
              " karein"
          ),
          color=discord.Color.red(),
      )
      await interaction.response.edit_message(embed=embed, view=self.view)

    elif self.values[0] == "Music":
      embed = discord.Embed(
          title="🎵 Music Commands",
          description=(
              "Music player commands:\n\n`.play` - Gaana play"
              " karein\n`.skip` - Song skip karein\n`.stop` - Music rokein"
          ),
          color=discord.Color.blue(),
      )
      await interaction.response.edit_message(embed=embed, view=self.view)

    elif self.values[0] == "Fun Commands":
      embed = discord.Embed(
          title="✨ Fun Commands",
          description="Entertainment commands jald hi add honge!",
          color=discord.Color.gold(),
      )
      await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):

  def __init__(self):
    super().__init__()
    self.add_item(HelpDropdown())


class HelpCog(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command(name="help")
  async def help(self, ctx):
    embed = discord.Embed(
        title="🤖 Custom Bot Help Menu",
        description=(
            "• My prefix for this server is `.` (ya jo aapne set kiya ho)\n•"
            " Total modules: 3 active categories\n\nSelect a module from the"
            " dropdown below 👇"
        ),
        color=discord.Color.blurple(),
    )
    view = HelpView()
    await ctx.reply(embed=embed, view=view)


async def setup(bot):
  await bot.add_cog(HelpCog(bot))
