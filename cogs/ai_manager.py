import discord
from discord.ext import commands
import datetime
import random

class MoonlightHumanAssistant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server_rules = [
            "किसी भी लड़की या मेंबर की बेइज्जती या हैरेसमेंट नहीं करनी है।"
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if message.content.startswith('&'):
            return

        content_lower = message.content.lower()
        msg_text = message.content

        # 1. बातचीत और हाल-चाल का इंसानी अंदाज़
        if "hinglish" in content_lower or "language" in content_lower:
            await message.channel.send("समझ गया बॉस! अब से एकदम Hinglish में और तेरी ही भाषा में बात होगी, कोई रोबोटिक सीन नहीं।")
            return

        if any(w in content_lower for w in ["hi", "hello", "hey", "hii", "hai"]):
            replies = [
                f"हाँ भाई {message.author.mention}, बोल क्या चल रहा है?",
                f"नमस्ते सर! बोलो, क्या हाल-चाल हैं?",
                f"सुनाओ {message.author.mention}, सब ठीक-ठाक?"
            ]
            await message.channel.send(random.choice(replies))
            return

        if any(w in content_lower for w in ["kaise ho", "how are you", "कैसा है", "ठीक हो", "tu bta", "तू बता", "me achha hu"]):
            replies = [
                "मैं एकदम बढ़िया भाई! तू सुना, सब सेट है?",
                "मस्त एकदम! तू बता, आज सर्वर में क्या प्लान है?",
                "मैं फर्स्ट क्लास हूँ सर, तू बता तेरी तरफ क्या चल रहा है?"
            ]
            await message.channel.send(random.choice(replies))
            return

        if any(w in content_lower for w in ["bol ab", "chal bol", "bata"]):
            replies = [
                "हाँ बोल भाई, सुन रहा हूँ तेरी पूरी बात।",
                "बताओ सर, क्या हुक्म है? क्या करना है अभी?",
                "बोलो-बोलो, सर्वर की कमान अपने हाथ में है।"
            ]
            await message.channel.send(random.choice(replies))
            return

        if any(w in content_lower for w in ["chup", "shut up", "nikal", "chup kar"]):
            replies = [
                "अरे ठीक है भाई, चुप हो गया! 🤐",
                "चलो ठीक है, अब काम पर ध्यान देता हूँ।",
                "ओके बॉस, शांत!"
            ]
            await message.channel.send(random.choice(replies))
            return

        # 2. नया रूल सीखने या समझाने के लिए
        if "rule" in content_lower and ("add" in content_lower or "जोड़" in content_lower or "ये है" in content_lower or "नया" in content_lower):
            self.server_rules.append(msg_text)
            await message.channel.send(f"✅ एकदम नोट कर लिया भाई! यह नया रूल अब से मेरे दिमाग में है, कोई भी तोड़ेगा तो सीधा एक्शन लूँगा।")
            return

        # 3. ऑटो-मॉडरेशन: बदतमीजी या गाली पकड़े जाने पर बाकायदा समझाकर टाइमआउट देना
        abuse_words = ["gaali", "madarchod", "bhenchod", "bsdk", "chutiya"]
        has_abuse = any(word in content_lower for word in abuse_words)

        if has_abuse:
            try:
                await message.delete()
                duration = datetime.timedelta(minutes=5)
                await message.author.timeout(duration, reason="Server Rule Violation: Harassment/Abuse")
                await message.channel.send(
                    f"⚠️ {message.author.mention} भाई, तूने यहाँ गलत भाषा का इस्तेमाल किया है जो हैरेसमेंट और सर्वर के नियमों के खिलाफ है। इससे माहौल खराब होता है, इसलिए मैं तुझे 5 मिनट का टाइमआउट दे रहा हूँ। आगे से ध्यान रखना!"
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
                    await message.channel.send(f"✅ ओके सर! **{target.name}** को रास्ते से हटा दिया है (बैन कर दिया)।")
                    return
                except Exception as e:
                    await message.channel.send(f"❌ भाई, इसे बैन करने में दिक्कत आ रही है, शायद इसकी परमिशन मुझसे ऊपर है।")

            elif any(k in content_lower for k in ["kick", "किक"]):
                try:
                    await target.kick(reason=f"Action requested by {message.author.name}")
                    await message.channel.send(f"✅ डन सर! **{target.name}** को किक मार दिया है।")
                    return
                except Exception as e:
                    await message.channel.send(f"❌ भाई, इसे किक नहीं कर पा रहा हूँ।")

            elif any(k in content_lower for k in ["timeout", "time out", "चुप करा", "म्यूट"]):
                try:
                    duration = datetime.timedelta(minutes=10)
                    await target.timeout(duration, reason=f"Action requested by {message.author.name}")
                    await message.channel.send(f"✅ ठीक है भाई, **{target.name}** को 10 मिनट की चुप्प करा दी है (टाइमआउट दे दिया है)।")
                    return
                except Exception as e:
                    await message.channel.send(f"❌ भाई, इसे टाइमआउट देने में एरर आ गई।")

async def setup(bot):
    await bot.add_cog(MoonlightHumanAssistant(bot))
