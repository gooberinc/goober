import discord
from discord.ext import commands
from modules.globalvars import ownerid
class FileSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mode = None
        self.peer_id = None
        self.awaiting_file = False

    @commands.command()
    async def syncfile(self, ctx, mode: str, peer: discord.User):
        self.mode = mode.lower()
        self.peer_id = peer.id
        if ctx.author.id != ownerid:
            await ctx.send("You don't have permission to execute this command.")
            return
        if self.mode == "s":
            await ctx.send(f"<@{self.peer_id}> FILE_TRANSFER_REQUEST")
            await ctx.send(file=discord.File("memory.json"))
            await ctx.send("File sent in this channel.")
        elif self.mode == "r":
            await ctx.send("Waiting for incoming file...")
            self.awaiting_file = True
        else:
            await ctx.send("Invalid mode, use 's' or 'r'.")


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or not self.awaiting_file:
            return
        if message.author.id != self.peer_id:
            return

        if message.content == "FILE_TRANSFER_REQUEST":
            print("Ping received. Awaiting file...")
        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith(".json"):
                    filename = "received_memory.json"
                    await attachment.save(filename)
                    print(f"File saved as {filename}")
                    await message.channel.send("File received and saved.")
                    self.awaiting_file = False

async def setup(bot):
    await bot.add_cog(FileSync(bot))
