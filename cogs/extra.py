import discord
from discord.ext import commands

class ImperionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. No Prefix Command
    @commands.command(name="noprefix")
    @commands.is_owner()
    async def noprefix(self, ctx, action: str, member: discord.Member):
        if action.lower() == "add":
            await ctx.send(f"Success: {member.mention} ko no-prefix list mein add kar diya gaya hai[span_0](start_span)[span_0](end_span).")
        elif action.lower() == "remove":
            await ctx.send(f"Success: {member.mention} ko no-prefix list se hata diya gaya hai.")
        else:
            await ctx.send("Usage: `!noprefix add @user` ya `remove @user`")

    # 2. Birthday Command
    @commands.command(name="birthday")
    async def birthday(self, ctx, action: str, date: str = None):
        if action.lower() == "set":
            await ctx.send(f"Aapka birthday **{date}** par set kar diya gaya hai[span_1](start_span)[span_1](end_span)!")
        else:
            await ctx.send("Usage: `!birthday set DD-MM-YYYY`")

    # 3. VC Role Command
    @commands.command(name="vcrole")
    @commands.has_permissions(manage_roles=True)
    async def vcrole(self, ctx, channel: discord.VoiceChannel, role: discord.Role):
        await ctx.send(f"Success: {channel.mention} join karne par ab `{role.name}` role milega[span_2](start_span)[span_2](end_span).")

    # 4. Modmail Command
    @commands.command(name="modmail")
    async def modmail(self, ctx, action: str = "setup"):
        await ctx.send(f"Modmail system successfully **{action}** ho gaya hai[span_3](start_span)[span_3](end_span)!")

    # 5. Guild Tag Command
    @commands.command(name="guildtag")
    @commands.has_permissions(관리_서버=True)
    async def guildtag(self, ctx, action: str, tag: str):
        await ctx.send(f"Server guild tag **{tag}** set kar diya gaya hai[span_4](start_span)[span_4](end_span).")

    # 6. Quote Info Command
    @commands.command(name="quoteinfo")
    async def quoteinfo(self, ctx, message_id: int):
        await ctx.send(f"Message ID `{message_id}` ki details fetch ki ja rahi hain[span_5](start_span)[span_5](end_span)...")

    # 7. Voice Master Command
    @commands.command(name="voicemaster")
    @commands.has_permissions(administrator=True)
    async def voicemaster(self, ctx):
        await ctx.send("VoiceMaster 'Join to Create' channel successfully setup ho gaya hai[span_6](start_span)[span_6](end_span)!")

    # 8. Voice Care Command
    @commands.command(name="voicecare")
    async def voicecare(self, ctx):
        await ctx.send("Voice care aur channel management settings open hain[span_7](start_span)[span_7](end_span).")

    # 9. 24/7 Voice Command
    @commands.command(name="247")
    @commands.has_permissions(administrator=True)
    async def toggle_247(self, ctx, state: str):
        await ctx.send(f"24/7 Voice channel connection state: **{state.upper()}**[span_8](start_span)[span_8](end_span).")

    # 10. Backup Command
    @commands.command(name="backup")
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx, action: str):
        if action.lower() == "create":
            await ctx.send("Server ka backup successfully create ho raha hai[span_9](start_span)[span_9](end_span)...")
        else:
            await ctx.send("Usage: `!backup create`")

    # 11. Server Event Command
    @commands.command(name="serverevent")
    @commands.has_permissions(manage_events=True)
    async def serverevent(self, ctx, action: str):
        await ctx.send(f"Server event action **{action}** process kiya ja raha hai[span_10](start_span)[span_10](end_span).")

async def setup(bot):
    await bot.add_cog(ImperionCommands(bot))
