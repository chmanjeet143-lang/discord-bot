import discord
from discord.ext import commands
import datetime

class MoonlightProAssistant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server_rules = [
            "Kisi bhi member ki beij्जati ya harassment nahi karni hai."
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content_lower = message.content.lower()
        msg_text = message.content

        # Check if the bot was triggered via '&ask' OR if the user replied directly to the bot's message
        is_triggered = False
        
        if content_lower.startswith('&ask'):
            is_triggered = True
            # Remove '&ask' from the content for processing
            content_lower = content_lower.replace('&ask', '').strip()
            msg_text = msg_text[4:].strip()
        elif message.reference and message.reference.message_id:
            try:
                referenced_message = await message.channel.fetch_message(message.reference.message_id)
                if referenced_message.author.id == self.bot.user.id:
                    is_triggered = True
            except Exception:
                pass

        # 1. AUTO-MODERATION (Yeh hamesha background mein bina trigger ke chalega)
        abuse_words = ["gaali", "madarchod", "bhenchod", "bsdk", "chutiya"]
        has_abuse = any(word in content_lower for word in abuse_words)

        if has_abuse and not message.author.guild_permissions.manage_messages:
            try:
                await message.delete()
                duration = datetime.timedelta(minutes=5)
                await message.author.timeout(duration, reason="Server Rule Violation: Abuse/Harassment")
                await message.channel.send(
                    f"⚠️ {message.author.mention} Yahan galat bhasha ka use karna server rules ke khilaf hai. Aapko 5 minute ka timeout diya jata hai."
                )
                return
            except Exception as e:
                print(f"Auto-mod error: {e}")

        # 2. CHAT & ASSISTANT COMMANDS (Yeh sirf tab chalengi jab '&ask' use ho ya reply kiya jaye)
        if is_triggered:
            # Greetings & Status
            if any(w in content_lower for w in ["hi", "hello", "hey", "kaise ho", "thik ho"]):
                await message.channel.send("Main ekdam thik hoon sir. Server par puri nazar hai, bataye kya kaam hai.")
                return

            # Adding new rules
            if "rule" in content_lower and ("add" in content_lower or "jod" in content_lower or "ye hai" in content_lower):
                self.server_rules.append(msg_text)
                await message.channel.send("Naya rule successfully note kar liya hai. Ab se ispar strict action liya jayega.")
                return

            # Admin Actions (Ban, Kick, Timeout via Mention)
            if message.mentions and message.author.guild_permissions.manage_messages:
                target = message.mentions[0]

                if any(k in content_lower for k in ["ban", "ban kar"]):
                    try:
                        await target.ban(reason=f"Action requested by {message.author.name}")
                        await message.channel.send(f"User {target.name} ko successfully ban kar diya gaya hai.")
                        return
                    except Exception as e:
                        await message.channel.send(f"Error: Is user ko ban nahi kar pa raha hoon ({e}).")

                elif any(k in content_lower for k in ["kick", "kick kar"]):
                    try:
                        await target.kick(reason=f"Action requested by {message.author.name}")
                        await message.channel.send(f"User {target.name} ko server se kick kar diya hai.")
                        return
                    except Exception as e:
                        await message.channel.send(f"Error: Is user ko kick nahi kar pa raha hoon ({e}).")

                elif any(k in content_lower for k in ["timeout", "mute"]):
                    try:
                        duration = datetime.timedelta(minutes=10)
                        await target.timeout(duration, reason=f"Action requested by {message.author.name}")
                        await message.channel.send(f"User {target.name} ko 10 minute ka timeout de diya gaya hai.")
                        return
                    except Exception as e:
                        await message.channel.send(f"Error: Timeout apply karne mein problem aayi ({e}).")

            # General fallback for triggered queries (Professional tone)
            await message.channel.send("Aapke is command ya baat ka data mere paas set nahi hai sir. Kripya sahi format mein instructions dein.")
            return

async def setup(bot):
    await bot.add_cog(MoonlightProAssistant(bot))
