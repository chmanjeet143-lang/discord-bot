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
            label="Music", description="Play, skip and queue songs", emoji="🎵"
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
              "• `.kick @user` - Member ko kick karein\n• `.ban @user` - Member"
              " ko ban karein\n• `.clear [amount]` - Messages delete karein"
          ),
          color=discord.Color.red(),
      )
    elif self.values[0] == "Music":
      embed = discord.Embed(
          title="🎵 Music Commands",
          description=(
              "• `.play [song]` - Gaana play karein\n• `.skip` - Next song"
              " bajayein\n• `.stop` - Music rok dein"
          ),
          color=discord.Color.blue(),
      )
    elif self.values[0] == "Fun Commands":
      embed = discord.Embed(
          title="✨ Fun Commands",
          description=(
              "• `.meme` - Random memes dekhein\n• `.coinflip` - Head or tail"
              " game"
          ),
          color=discord.Color.green(),
      )

    await interaction.response.send_message(embed=embed, ephemeral=True)


class HelpView(discord.ui.View):

  def __init__(self):
    super().__init__()
    self.add_item(HelpDropdown())


class HelpCog(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command(name="help")
  async def help_command(self, ctx):
    embed = discord.Embed(
        title="Hey, I'm Your Custom Bot",
        description=(
            "• My prefix for this server is `.`\n• Type `.help` for more"
            " info\n• Total modules: 3 active categories"
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Select a module from the dropdown below 👇")
    await ctx.send(embed=embed, view=HelpView())


async def setup(bot):
  await bot.add_cog(HelpCog(bot))

