import discord
from discord.ext import commands
from modules.globalvars import RED, GREEN, RESET, LOCAL_VERSION_FILE
import os

class songchange(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_local_version():
        if os.path.exists(LOCAL_VERSION_FILE):
            with open(LOCAL_VERSION_FILE, "r") as f:
                return f.read().strip()
        return "0.0.0"

    global local_version
    local_version = get_local_version()

    @commands.command()
    async def changesong(self, ctx):
        if LOCAL_VERSION_FILE > "0.11.8":
            await ctx.send(f"Goober is too old! you must have version 0.11.8 you have {local_version}")
            return
        await ctx.send("Check the terminal! (this does not persist across restarts)")
        song = input("\nEnter a song:\n")
        try:
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{song}"))
            print(f"{GREEN}Changed song to {song}{RESET}")
        except Exception as e:
            print(f"{RED}An error occurred while changing songs..: {str(e)}{RESET}")

async def setup(bot):
    await bot.add_cog(songchange(bot))
