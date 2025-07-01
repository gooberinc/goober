import discord
from discord.ext import commands
from discord import app_commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="slashcommand", description="slashcommandexample")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer()
        exampleembed = discord.Embed(
            title="Pong!!",
            description="The Beretta fires fast and won't make you feel any better!",
            color=discord.Color.blue()
        )
        exampleembed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)

        await interaction.followup.send(embed=exampleembed)

async def setup(bot):
    await bot.add_cog(Ping(bot))
