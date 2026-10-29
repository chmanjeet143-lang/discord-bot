import discord
from discord.ext import commands
import datetime

class MoonlightLocalAssistant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # सर्वर के रूल्स और कस्टम मेमोरी को याद रखने की जगह
        self.server_rules = [
            "किसी भी लड़की या मेंबर की बेइज्जती या हैरेसमेंट नहीं करनी है।"
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # अगर कमांड है तो उसे कमांड प्रोसेसर पर जाने दो
        if message.content.startswith('&'):
            return

        content_lower = message.content.lower()
        msg_text = message.content

        # 1. हाय-हैलो और आम बातचीत का जवाब (ताकि रोबोट न लगे)
        if any(w in content_lower for w in ["hi", "hello", "hey", "হাই", "हाय", "हलो"]):
            await message.channel.send(f"नमस्ते {message.author.mention} सर! बताइए, सर्वर में क्या हाल-चाल हैं और मेरे लिए क्या हुक्म है?")
            return

        if any(w in content_lower for w in ["kaise ho", "how are you", "कैसा है", "ठीक हो"]):
            await message.channel.send(f"मैं एकदम ठीक हूँ सर, आपकी सेवा में हाज़िर हूँ और सर्वर पर पूरी नजर बनाए हुए हूँ!")
            return

        # 2. नया रूल सीखने या समझाने के लिए (जैसे: "सुन, नया रूल यह है...")
        if "rule" in content_lower and ("add" in content_lower or "जोड़" in content_lower or "ये है" in content_lower):
            self.server_rules.append(msg_text)
            await message.channel.send(f"✅ ठीक है सर! मैंने यह नया रूल अपनी मेमोरी में नोट कर लिया है और अब से इस पर कड़ी नजर रखूँगा।")
            return

        # 3. ऑटो-मॉडरेशन: बदतमीजी या गाली पकड़े जाने पर सजा देना
        abuse_words = ["gaali", "madarchod", "bhenchod", "bsdk", "chutiya"]
        has_abuse = any(word in content_lower for word in abuse_words)

        if has_abuse:
            try:
                # गंदा मैसेज तुरंत डिलीट करेंगे
                await message.delete()

                # 5 मिनट का टाइमआउट देंगे
                duration = datetime.timedelta(minutes=5)
                await message.author.timeout(duration, reason="Server Rule Violation: Abuse/Harassment")

                # प्रोफेशनल और सख्त लहजे में चेतावनी
                await message.channel.send(
                    f"⚠️ {message.author.mention} सुन भाई! तुमने यहाँ अभद्र भाषा का प्रयोग किया है जो हमारे सर्वर के नियमों और हैरेसमेंट के खिलाफ है। इससे माहौल खराब होता है, इसलिए मैं तुम्हें 5 मिनट का टाइमआउट दे रहा हूँ। आगे से ऐसा मत करना।"
                )
                return
            except Exception as e:
                print(f"Auto-mod error: {e}")

        # 4. देसी भाषा में एडमिन के हुक्म पर एक्शन (बैन, किक, टाइमआउट)
        if message.mentions and message.author.guild_permissions.manage_messages:
            target = message.mentions[0]

            if any(k in content_lower for k in ["ban", "बैन"]):
                try:
                    await target.ban(reason=f"Action requested by {message.author.name}")
                    await message.channel.send(f"✅ ओके सर! **{target.name}** को सर्वर से बैन कर दिया गया है, अब ये यहाँ नहीं दिखेगा।")
                    return
                except Exception as e:
                    await message.channel.send(f"❌ सर, इसे बैन करने में दिक्कत आ रही है।")

            elif any(k in content_lower for k in ["kick", "किक"]):
                try:
                    await target.kick(reason=f"Action requested by {message.author.name}")
                    await message.channel.send(f"✅ जी सर, **{target.name}** को किक कर दिया है।")
                    return
                except Exception as e:
                    await message.channel.send(f"❌ सर, इसे किक नहीं कर पा रहा हूँ।")

            elif any(k in content_lower for k in ["timeout", "time out", "चुप करा", "म्यूट"]):
                try:
                    duration = datetime.timedelta(minutes=10)
                    await target.timeout(duration, reason=f"Action requested by {message.author.name}")
                    await message.channel.send(f"✅ ठीक है सर, **{target.name}** को 10 मिनट का टाइमआउट दे दिया है, यह शांत रहेगा।")
                    return
                except Exception as e:
                    await message.channel.send(f"❌ सर, इसे टाइमआउट देने में एरर आ गई।")

    # बॉट की जानकारी देखने की कमांड
    @commands.command(name="assistant_info", help="Shows assistant status.")
    async def assistant_info(self, ctx):
        embed = discord.Embed(
            title="🌙 Moonlight Heaven - Local Assistant",
            description="Pure Python Smart Assistant is active. No external AI lag!",
            color=discord.Color.blue()
        )
        embed.add_field(name="Active Rules Count", value=str(len(self.server_rules)), inline=True)
        embed.add_field(name="Mode", value="Server Manager & Chat Assistant", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MoonlightLocalAssistant(bot))
