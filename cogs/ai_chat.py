import os
import time
import discord
from discord.ext import commands
from google import genai


class AIChat(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    # Gemini API Key environment variable se uthayenge (Render par variable dalna hoga)
    self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    self.request_timestamps = []
    self.max_requests = 15

  @commands.Cog.listener()
  async def on_message(self, message):
    # Bot apne khud ke message ko ignore karega
    if message.author == self.bot.user:
      return

    # Jab bhi bot ko mention kiya jaye
    if self.bot.user in message.mentions:
      current_time = time.time()

      # 1 minute purane timestamps hatao (Rate limiting)
      self.request_timestamps = [
          t for t in self.request_timestamps if current_time - t < 60
      ]

      if len(self.request_timestamps) >= self.max_requests:
        try:
          await message.reply(
              "⏳ Arre bhai/behen! Bohot zyada messages aa rahe hain. Thodi"
              " der baad try karo!"
          )
        except Exception:
          pass
        return

      self.request_timestamps.append(current_time)

      # Message clean karna (mention hatana)
      user_message = message.content.replace(
          f"<@!{self.bot.user.id}>", ""
      ).strip()
      user_message = user_message.replace(f"<@{self.bot.user.id}>", "").strip()

      if not user_message:
        try:
          await message.reply(
              "Hello! Main Moonlight Heaven bot hu, mujhe Zeus ne banaya hai. Aap"
              " mujhse kisi bhi command ka example ya help maang sakte hain!"
          )
        except Exception:
          pass
        return

      # Typing status dikhana jab tak AI soch raha hai
      async with message.channel.typing():
        try:
          system_instruction = (
              "Aapka naam 'Moonlight Heaven Bot' hai. Aapko 'Zeus' ne banaya"
              " hai. "
              "Aap duniya ki kisi bhi bhasha (Hindi, English, Hinglish, Spanish,"
              " French, etc.) me baat kar sakte hain. "
              "User jis bhasha me sawaal puche, aapko usi bhasha me jawab dena"
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
          # Yeh block bot ko crash hone se bachayega aur sirf console me error print karega
          print(f"❌ AI Chat Error: {e}")
          try:
            await message.reply(
                "⚠️ Oops! AI response lane me thodi problem ho gayi, baad me"
                " try karein."
            )
          except Exception:
            pass


async def setup(bot):
  await bot.add_cog(AIChat(bot))
