import random
import discord
from discord.ext import commands

class eightball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def eightball(self, ctx):
        answer = random.randint(1, 20)
        text = "Nothing"
        if answer==1:
            text = "It is certain."
        elif answer==2:
            text = "It is decidedly so."
        elif answer==3:
            text = "Without a doubt."
        elif answer==4:
            text = "Yes definitely."
        elif answer==5:
            text = "You may rely on it."
        elif answer==6:
            text = "As I see it, yes."
        elif answer==7:
            text = "Most likely."
        elif answer==8:
            text = "Outlook good."
        elif answer==9:
            text = "Yes."
        elif answer==10:
            text = "Signs point to yes."
        elif answer==11:
            text = "Reply hazy, try again."
        elif answer==12:
            text = "Ask again later."
        elif answer==13:
            text = "Better not tell you now."
        elif answer==14:
            text = "Cannot predict now."
        elif answer==15:
            text = "Concentrate and ask again."
        elif answer==16:
            text = "Don't count on it."
        elif answer==17:
            text = "My reply is no."
        elif answer==18:
            text = "My sources say no."
        elif answer==19:
            text = "Outlook not so good."
        elif answer==20:
            text = "Very doubtful."

        await ctx.send(text)

async def setup(bot):
    await bot.add_cog(eightball(bot))
