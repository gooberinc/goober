import discord
from discord.ext import commands

class whoami(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def whoami(self, ctx):
        user_id = ctx.author.id
        username = ctx.author.name

        embed = discord.Embed(
            title="User Information",
            description=f"Your User ID is: {user_id}\n"
                        f"Your username is: {username}\n"
                        f"Your nickname in this server is: <@{user_id}>",
            color=discord.Color.blue() 
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(whoami(bot))
