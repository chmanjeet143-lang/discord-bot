import os
import discord
from discord.ext import commands
from google import genai
from google.genai import types
import datetime

class MoonlightAIManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if message.content.startswith('&'):
            return

        # एआई को चेक करने और साथ में कारण भी तैयार करने को कहेंगे
        moderation_prompt = (
            "Analyze the following Discord message. Check if it contains severe abuse, vulgar cuss words, "
            "or harassment/disrespect directed at someone (especially degrading women). "
            "If it is a VIOLATION, generate a short, strict warning sentence in Hindi explaining what they did wrong "
            "and that they are getting a timeout (e.g., 'तुमने यहाँ अभद्र भाषा का प्रयोग किया है जो हैरेसमेंट के अंतर्गत आता है, इसलिए तुम्हें 5 मिनट का टाइमआउट दिया जाता है'). "
            "Format your reply strictly as: [VERDICT]|[REASON_IN_HINDI] where VERDICT is either SAFE or VIOLATION."
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"Message: '{message.content}'\n\n{moderation_prompt}",
                config=types.GenerateContentConfig(temperature=0.1)
            )
            
            result_text = response.text.strip()
            
            if "|" in result_text:
                verdict, reason = result_text.split("|", 1)
                verdict = verdict.strip().upper()
                reason = reason.strip()
            else:
                verdict = "SAFE"
                reason = ""

            if "VIOLATION" in verdict:
                try:
                    # पहले गंदा मैसेज डिलीट करेंगे
                    await message.delete()

                    # यूजर को उसकी गलती बताकर चेतावनी देंगे और साथ ही टाइमआउट देंगे
                    timeout_duration = datetime.timedelta(minutes=5)
                    await message.author.timeout(timeout_duration, reason="AI Automated Moderation: Harassment/Abuse")
                    
                    # बॉट तगड़े अंदाज़ में बताएगा कि क्यों सजा मिली है
                    await message.channel.send(
                        f"🚨 {message.author.mention} सुन! {reason}"
                    )
                except Exception as ex:
                    print(f"Action lene mein error: {ex}")

        except Exception as e:
            pass

    @commands.command(name="ai", help="Strict server management command.")
    async def ai_talk(self, ctx, *, message: str):
        system_instruction = (
            "You are the strict, professional AI server manager for the Discord server 'Moonlight Heaven', "
            "created by 'Zeus'. "
            "RULES:\n"
            "1. NO chit-chat, NO hello, NO small talk.\n"
            "2. Keep responses strictly 1 or 2 lines maximum.\n"
            "3. Focus ONLY on server management, rules, moderation, and keeping the community safe."
        )

        try:
            async with ctx.typing():
                response = self.client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    ),
                )
                
                reply_text = response.text.strip()
                if len(reply_text) > 250:
                    reply_text = reply_text[:250] + "..."

                await ctx.send(reply_text)

        except Exception as e:
            await ctx.send(f"❌ एरर: `{e}`")

async def setup(bot):
    await bot.add_cog(MoonlightAIManager(bot))
