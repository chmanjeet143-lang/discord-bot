import os
import time
import discord
from discord.ext import commands
from google import genai


class AIChat(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    self.request_timestamps = []
    self.max_requests = 15

  # 1. &aichat command jo channel banayegi
  @commands.command(name="aichat")
  @commands.has_permissions(
      manage_channels=True
  )  # Sirf wahi use kar sakega jiske pas channel manage karne ki permission ho
  async def create_ai_channel(self, ctx):
    guild = ctx.guild

    # Check karo ki kya server me pehle se 'ai-chat' naam ka channel hai ya nahi
    existing_channel = discord.utils.get(guild.text_channels, name="ai-chat")
    if existing_channel:
      await ctx.send(
          f"⚠️ Bhai, `ai-chat` channel pehle se hi bana hua hai: {existing_channel.mention}"
      )
      return

    try:
      # Naya text channel banayega
      overwrites = {
          guild.default_role: discord.PermissionOverwrite(
              read_messages=True, send_messages=True
          ),
          guild.me: discord.PermissionOverwrite(
              read_messages=True, send_messages=True, manage_channels=True
          ),
      }

      new_channel = await guild.create_text_channel(
          "ai-chat",
          overwrites=overwrites,
          topic=(
              "Moonlight Heaven AI Chat Room! Yahan aap bina prefix ke AI se"
              " baatein kar sakte hain."
          ),
      )

      await ctx.send(
          f"✅ AI Chat channel successfully ban gaya hai: {new_channel.mention}!"
          " Ab aap wahan jaakar baat kar sakte hain."
      )

      # Naye channel me welcome message bhej dega
      await new_channel.send(
          "👋 Hello everyone! Main Moonlight Heaven Bot hu, mujhe Zeus ne banaya"
          " hai. Aap yahan bina kisi prefix ke mujhse hello, mazaak, ya kisi"
          " bhi command ke baare me baat kar sakte hain!"
      )

    except Exception as e:
      await ctx.send(
          f"❌ Channel banane me error aa gaya hai. Check karein ki mere paas"
          f" 'Manage Channels' ki permission hai ya nahi. Error: {e}"
      )

  # Agar koi &aichat command bina permission ke use kare toh error handle karne ke liye
  @create_ai_channel.error
  async def aichat_error(self, ctx, error):
    if isinstance(error, commands.MissingPermissions):
      await ctx.send(
          "❌ Aapke paas yeh command use karne ke liye 'Manage Channels' ki"
          " permission nahi hai!"
      )

  # 2. Sirf 'ai-chat' channel me bina prefix ke baatein aur mazaak handle karne ka event
  @commands.Cog.listener()
  async def on_message(self, message):
    if message.author == self.bot.user:
      return
    if message.author.bot:
      return

    # Check karo ki message sirf 'ai-chat' naam wale channel me hi kiya gaya hai ya nahi
    if message.channel.name != "ai-chat":
      return

    # Rate limiting (1 minute me max 15 replies)
    current_time = time.time()
    self.request_timestamps = [
        t for t in self.request_timestamps if current_time - t < 60
    ]

    if len(self.request_timestamps) >= self.max_requests:
      try:
        await message.reply(
            "⏳ Arre bhai/behen! 1 minute me bohot saare messages ho gaye hain."
            " Thodi der saans lo, phir baat karte hain!"
        )
      except Exception:
        pass
      return

    self.request_timestamps.append(current_time)

    user_message = message.content.strip()
    if not user_message:
      return

    # Typing status dikhana jab tak AI soch raha hai
    async with message.channel.typing():
      try:
        system_instruction = (
            "Aapka naam 'Moonlight Heaven Bot' hai. Aapko 'Zeus' ne banaya"
            " hai. "
            "Aap duniya ki kisi bhi bhasha (Hindi, English, Hinglish, Spanish,"
            " French, etc.) me baat kar sakte hain. "
            "Aap users ke sath dosti se, mazaak-masti me, aur normal chat bhi"
            " kar sakte hain (hello, jokes, chit-chat, etc.). "
            "User jis bhasha ya tone me baat kare, aapko usi bhasha me jawab dena"
            " hai. "
            "Agar koi aapse server ki kisi bhi command ka use karne ka tareeqa"
            " ya example puche "
            "(jaise /ban, /kick, /mute, /giveaway, /clear, etc.), toh aapko"
            " har command ka proper, "
            "sahi tarika aur step-by-step example dena hai ki usko kaise use"
            " karein."
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
            ),
        )

        await message.reply(response.text)

      except Exception as e:
        print(f"❌ AI Chat Error: {e}")
        try:
          await message.reply(
              "⚠️ Oops! Thodi technical problem ho gayi hai, baad me try"
              " karein."
          )
        except Exception:
          pass


async def setup(bot):
  await bot.add_cog(AIChat(bot))
