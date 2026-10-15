import discord


# Dropdown Menu class (agar aapke paas pehle se hai toh aap apne wale ko use kar sakte hain)
class HelpDropdown(discord.ui.Select):

  def __init__(self):
    options = [
        discord.SelectOption(
            label="Moderation",
            description="View server moderation commands",
            emoji="🛡️",
        ),
        discord.SelectOption(
            label="Fun & Games",
            description="View fun and interactive commands",
            emoji="🎮",
        ),
        discord.SelectOption(
            label="Utility",
            description="View utility and general commands",
            emoji="⚙️",
        ),
    ]
    super().__init__(
        placeholder="Select a category to view commands...",
        min_values=1,
        max_values=1,
        options=options,
    )

  async def callback(self, interaction: discord.Interaction):
    # Yahan aap category ke hisaab se logic likh sakte hain
    await interaction.response.send_message(
        f"You selected: {self.values[0]}", ephemeral=True
    )


class HelpView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)
    self.add_item(HelpDropdown())


# Help Command
@bot.command(name="help")
async def help_command(ctx):
  embed = discord.Embed(
      title="Moonlight Heaven • Help Center",
      description=(
          "👋 Hello there! I am **Moonlight Heaven**, your personal advanced"
          " Discord bot.\nCreated with love and dedication by **Zeus** to keep"
          " your server secure, fun, and fully automated.\n\nSelect a category"
          " from the dropdown menu below to view the commands!"
      ),
      color=discord.Color.from_rgb(138, 43, 226),  # Purple aesthetic theme
  )

  # Thumbnail ya image agar set karni ho (screenshot wali styling ke liye)
  embed.set_thumbnail(
      url="YOUR_IMAGE_URL_HERE"
  )  apni image ka link ya remove kar dein
  embed.set_footer(
      text="Moonlight Heaven • Developed By Zeus",
      icon_url=ctx.guild.me.display_avatar.url,
  )

  view = HelpView()
  await ctx.send(embed=embed, view=view)
