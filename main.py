import discord
from discord.ext import commands

@bot.command(name="help")
async def help_command(ctx, category: str = None):
    prefix = "&" # Aapka prefix yahan aayega
    
    if not category:
        embed = discord.Embed(
            title="🤖 Bot Command Categories",
            description=f"Kisi bhi category ki commands dekhne ke liye use karein: `{prefix}help <category>`",
            color=discord.Color.blue()
        )
        embed.add_field(name="🛠️ Utility & Info", value="Tools, info, aur server navigation commands.", inline=False)
        embed.add_field(name="🛡️ Moderation", value="Ban, kick, mute, aur server moderation tools.", inline=False)
        embed.add_field(name="🎮 Games & Simulation", value="Board games, virtual simulation aur fun games.", inline=False)
        embed.add_field(name="🎨 Profile & Image Editing", value="User profile customization aur image filters.", inline=False)
        embed.add_field(name="🐾 Animals & Nature", value="Animals ki random pictures aur info.", inline=False)
        embed.add_field(name="💰 Economy & Fun", value="Virtual money, banking, aur community fun commands.", inline=False)
        embed.add_field(name="📊 Leveling & Social", value="XP, levels, welcome, aur reaction roles.", inline=False)
        embed.add_field(name="🎟️ Tickets & Support", value="Support ticket system aur management.", inline=False)
        embed.add_field(name="🎉 Giveaway & Events", value="Giveaways, events, aur polls.", inline=False)
        embed.add_field(name="⚙️ Management & AutoMod", value="Server setup, logs, rules aur configuration.", inline=False)
        await ctx.send(embed=embed)
        return

    category = category.lower()
    embed = discord.Embed(color=discord.Color.green())

    if category == "utility" or category == "info":
        embed.title = "🛠️ Utility & Info Commands"
        embed.description = (
            "`&ping` - Bot ka response time check karne ke liye\n"
            "`&afk` - Away From Keyboard status set karne ke liye\n"
            "`&qr` - QR code banane ke liye\n"
            "`&shorten` - URL chota karne ke liye\n"
            "`&password` - Secure password generate karne ke liye\n"
            "`&ascii` - Text ko ASCII art mein badalne ke liye\n"
            "`&say` - Bot se kuch bulane ke liye\n"
            "`&dm` - User ko direct message bhejne ke liye\n"
            "`&report` - Kisi ki report karne ke liye\n"
            "`&feedback` / `&bug` - Bot ya server ko feedback dene ke liye\n"
            "`&stats` - Server stats dekhne ke liye\n"
            "`&donate` - Donation info ke liye\n"
            "`&rules` / `&staff` / `&support` / `&verify` - Server navigation ke liye\n"
            "`&reminder` - Kisi kaam ke liye reminder set karne ke liye\n"
            "`&translate` - Text ko doosri language mein translate karne ke liye\n"
            "`&weather` - Mausam ki jankari lene ke liye\n"
            "`&urban` - Slang words ka meaning dekhne ke liye\n"
            "`&calculator` - Math calculation karne ke liye\n"
            "`&roleinfo` - Role ki details dekhne ke liye\n"
            "`&channelinfo` - Channel ki details dekhne ke liye\n"
            "`&emojiinfo` - Emoji ki details dekhne ke liye\n"
            "`&botinfo` - Bot ki info dekhne ke liye\n"
            "`&uptime` - Bot kitne time se online hai check karne ke liye\n"
            "`&invite` - Bot ka invite link lene ke liye\n"
            "`&poll` - Voting ya poll create karne ke liye\n"
            "`&embed` - Custom formatted embed message banane ke liye\n"
            "`&serverinfo` - Server ki details dekhne ke liye\n"
            "`&userinfo` - User ki profile details dekhne ke liye\n"
            "`&banner` - Server ya user ka banner dekhne ke liye\n"
            "`&permissions` - User ya role ki permissions check karne ke liye\n"
            "`&whois` - User ki deep profile check karne ke liye\n"
            "`&steam` - Steam game details search karne ke liye\n"
            "`&color` / `&random` / `&quote` / `&dictionary` / `&wiki` / `&lyrics` / `&covid` / `&crypto` / `&stock`"
        )

    elif category == "moderation" or category == "mod":
        embed.title = "🛡️ Moderation Commands"
        embed.description = (
            "`&ban` - User ko permanent server se nikalne ke liye\n"
            "`&unban` - Ban kiye hue user ki entry wapas allow karne ke liye\n"
            "`&kick` - User ko bina ban kiye server se remove karne ke liye\n"
            "`&timeout` - User ko kuch samay ke liye mute ya restrict karne ke liye\n"
            "`&unmute` - Timeout hataane ke liye\n"
            "`&warn` - User ko galti par warning dene ke liye\n"
            "`&clear` - Chat se messages bulk mein delete karne ke liye\n"
            "`&lock` - Channel par typing lock karne ke liye\n"
            "`&unlock` - Channel ko wapas open karne ke liye\n"
            "`&slowmode` - Messages ke beech time gap set karne ke liye\n"
            "`&massban` - Ek sath kai users ko ban karne ke liye\n"
            "`&softban` - Ban karke turant unban karna (purane messages delete karne ke liye)\n"
            "`&nuke` - Channel ke saare messages delete karke fresh karne ke liye\n"
            "`&lockdown` - Pure server ya multiple channels ko lock karne ke liye\n"
            "`&unlockdown` - Lockdown hatane ke liye\n"
            "`&clearwarns` - User ki warnings clear karne ke liye\n"
            "`&case` - Moderation action ki case history dekhne ke liye\n"
            "`&nick` - User ka nickname change karne ke liye\n"
            "`&role` - User ko specific role dene ya hatane ke liye\n"
            "`&temprole` - Temporary role assign karne ke liye"
        )

    elif category == "games":
        embed.title = "🎮 Games & Simulation Commands"
        embed.description = (
            "`&chess` / `&uno` / `&poker` - Board/card games\n"
            "`&fishing` / `&mining` / `&hunt` / `&pet` / `&feed` / `&heal` / `&train` - Virtual simulation games\n"
            "`&slots` - Slot machine game khelne ke liye\n"
            "`&trivia` - Quiz game khelne ke liye\n"
            "`&rps` - Rock Paper Scissors khelne ke liye\n"
            "`&connect4` - Connect 4 game khelne ke liye\n"
            "`&hangman` - Hangman word game khelne ke liye\n"
            "`&ship` - Do logo ki compatibility check karne ke liye\n"
            "`&meme` - Funny meme dekhne ke liye\n"
            "`&joke` - Joke sunane ke liye\n"
            "`&fact` - Interesting fact janne ke liye\n"
            "`&roll` / `&roll dice` - Dice roll karne ke liye\n"
            "`&8ball` / `&coinflip` - Random decisions ke liye"
        )

    elif category == "profile" or category == "image":
        embed.title = "🎨 Profile & Image Editing Commands"
        embed.description = (
            "`&marry` / `&divorce` / `&profile` / `&bio` / `&badge` / `&title` / `&background` / `&levelbackground` - User profile customization\n"
            "`&hug` / `&slap` / `&pat` - Interactive actions ke liye\n"
            "`&colorpicker` / `&imagefilter` / `&blur` / `&pixelate` / `&invert` / `&grayscale` / `&deepfry` - Image editing commands"
        )

    elif category == "animals":
        embed.title = "🐾 Animals & Nature Commands"
        embed.description = (
            "`&cat`, `&dog`, `&fox`, `&panda`, `&duck`, `&koala`, `&bird`, `&lizard`, `&raccoon`, `&kangaroo`, `&dhole` - Alag-alag janwaron ki random pictures aur info ke liye."
        )

    elif category == "economy":
        embed.title = "💰 Economy & Fun Commands"
        embed.description = (
            "`&balance` / `&daily` / `&work` - Virtual money manage karne ke liye\n"
            "`&confession` - Anonymous message bhejne ke liye\n"
            "`&birthday` - Birthday register karne ke liye\n"
            "`&suggest` - Server ke liye suggestion dene ke liye\n"
            "`&pay` - Economy mein kisi ko paise transfer karne ke liye\n"
            "`&rob` - Kisi se paise churane ke liye\n"
            "`&deposit` - Bank mein paise jama karne ke liye\n"
            "`&withdraw` - Bank se paise nikalne ke liye\n"
            "`&shop` - Virtual shop dekhne ke liye\n"
            "`&buy` - Item kharidne ke liye\n"
            "`&inventory` - Apne items dekhne ke liye\n"
            "`&leaderboard economy` - Rich users ki list dekhne ke liye\n"
            "`&coinflip bet` - Coinflip par bet lagane ke liye"
        )

    elif category == "leveling" or category == "social":
        embed.title = "📊 Leveling & Social Commands"
        embed.description = (
            "`&welcome` - Welcome message setup karne ke liye\n"
            "`&goodbye` - Leave message setup karne ke liye\n"
            "`&autorole` - Naye user ko auto role dene ke liye\n"
            "`&autorole remove` - Auto-role feature disable karne ke liye\n"
            "`&rank` - Apna current XP aur level dekhne ke liye\n"
            "`&leaderboard` - Server ke top active users ki list dekhne ke liye\n"
            "`&reactionrole` - Self-assignable roles system ke liye\n"
            "`&reactionrole remove` - Reaction role hatane ke liye\n"
            "`&givexp` - User ko extra XP dene ke liye\n"
            "`&removexp` - User ka XP kam karne ke liye\n"
            "`&levelroles` - Level ke hisab se roles set karne ke liye\n"
            "`&rankcard` - Level card design ya view karne ke liye\n"
            "`&resetlevel` - Server ke levels reset karne ke liye\n"
            "`&voiceexp` - Voice channel mein rehne par XP earn karne ke liye\n"
            "`&boosters` - Server boosters ki list dekhne ke liye\n"
            "`&rep` - Kisi user ko reputation/points dene ke liye"
        )

    elif category == "ticket" or category == "support":
        embed.title = "🎟️ Tickets & Support Commands"
        embed.description = (
            "`&ticket` - Support ticket create karne ke liye\n"
            "`&ticket close` - Support ticket band karne ke liye\n"
            "`&ticket add` - Ticket mein user add karne ke liye\n"
            "`&ticket remove` - Ticket se user hatane ke liye\n"
            "`&ticket claim` - Staff dwara ticket handle karne ke liye\n"
            "`&ticket transcript` - Ticket ki chat save karne ke liye\n"
            "`&ticket rename` - Ticket channel ka naam badalne ke liye"
        )

    elif category == "giveaway":
        embed.title = "🎉 Giveaway & Events Commands"
        embed.description = (
            "`&giveaway start` - Giveaway shuru karne ke liye\n"
            "`&giveaway reroll` - Naya winner chunne ke liye\n"
            "`&giveaway end` - Giveaway khatam karne ke liye\n"
            "`&event start` - Server event shuru karne ke liye\n"
            "`&poll edit` - Poll modify karne ke liye\n"
            "`&poll end` - Poll band karne ke liye"
        )

    elif category == "management" or category == "automod":
        embed.title = "⚙️ Management & AutoMod Commands"
        embed.description = (
            "`&automod` - Auto moderation rules setup karne ke liye\n"
            "`&setlog` - Logs channel set karne ke liye\n"
            "`&modlogs` - User ka moderation record check karne ke liye\n"
            "`&prefix` / `&setprefix` - Bot ka custom prefix set/badalne ke liye\n"
            "`&setchannel` - Important channels (rules, welcome) configure karne ke liye\n"
            "`&setlanguage` - Bot ki language change karne ke liye\n"
            "`&embededit` - Embed message edit karne ke liye\n"
            "`&announcement` - Important announcement bhejne ke liye\n"
            "`&thread` - Channel ke andar thread create karne ke liye\n"
            "`&forum` - Forum channel manage karne ke liye"
        )
    else:
        embed.title = "❌ Invalid Category"
        embed.description = "Sahi category ka naam dalein ya saari categories dekhne ke liye `&help` use karein."

    await ctx.send(embed=embed)
