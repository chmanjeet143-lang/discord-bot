import discord
from discord.ext import commands


class HelpDropdown(discord.ui.Select):

  def __init__(self):
    options = [
        discord.SelectOption(
            label="Moderation",
            description="Server moderation commands (kick, ban, clear)",
            emoji="🛡️",
        ),
        discord.SelectOption(
            label="Music",
            description="Music player commands (play, skip, stop)",
            emoji="🎵",
        ),
    ]
    super().__init__(
        placeholder="Select a module to see commands...",
        min_values=1,
        max_values=1,
        options=options,
    )

  async def callback(self, interaction: discord.Interaction):
    if self.values[0] == "Moderation":
      embed = discord.Embed(
          title="🛡️ Moderation Commands",
          description=(
              "Server ko control karne ke liye commands:\n\n`&kick` - Member ko"
              " kick karein\n`&ban` - Member ko ban karein\n`&clear` - Messages"
              " delete karein"
          ),
          color=discord.Color.red(),
      )
      await interaction.response.edit_message(embed=embed, view=self.view)

    elif self.values[0] == "Music":
      embed = discord.Embed(
          title="🎵 Music Commands",
          description=(
              "Gaane sunne ke liye commands:\n\n`&play` - Gaana play karein\n`&skip`"
              " - Song skip karein\n`&stop` - Music rokein"
          ),
          color=discord.Color.blue(),
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
        title="🤖 Bot Help Menu",
        description=(
            "Niche diye gaye dropdown menu se category select karein taaki aapko"
            " commands ki list dikh sake!"
        ),
        color=discord.Color.green(),
    )
    view = HelpView()
    await ctx.reply(embed=embed, view=view)


async def setup(bot):
  await bot.add_cog(HelpCog(bot))
