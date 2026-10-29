import os
import discord
from discord.ext import commands
from google import genai
from google.genai import types

class MoonlightAIManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    @commands.command(name="ai", help="Talk to Moonlight Heaven AI manager.")
    async def ai_talk(self, ctx, *, message: str):
        system_instruction = (
            "You are the official AI management system for the Discord server 'Moonlight Heaven'. "
            "Your creator and developer is 'Zeus'. "
            "Your home is the 'Moonlight Heaven' server. "
            "You are smart, strict, highly professional, and dedicated to server management, "
            "jamming mode, and event modes. Always stay in character, respect your creator Zeus, "
            "and represent Moonlight Heaven with pride. Keep your answers clear, structured, and helpful."
        )

        try:
            async with ctx.typing():
                # यहाँ gemini-3.8-flash सेट कर दिया है जैसा गूगल ने एरर में बताया था
                response = self.client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                    ),
                )
                
                reply_text = response.text
                if len(reply_text) > 2000:
                    for i in range(0, len(reply_text), 2000):
                        await ctx.send(reply_text[i:i+2000])
                else:
                    await ctx.send(reply_text)

        except Exception as e:
            await ctx.send(f"❌ अरे भाई, एआई से कनेक्ट करने में दिक्कत आ रही है: `{e}`")

    @commands.command(name="ai_status", help="Check AI and server identity status.")
    async def ai_status(self, ctx):
        embed = discord.Embed(
            title="🌙 Moonlight Heaven - AI System Status",
            description="AI management system is fully active and integrated.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Bot Name", value="Moonlight Heaven", inline=True)
        embed.add_field(name="Creator", value="Zeus", inline=True)
        embed.add_field(name="Home Server", value="Moonlight Heaven Server", inline=False)
        embed.set_footer(text="Powered by Gemini AI & Railway")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MoonlightAIManager(bot))
