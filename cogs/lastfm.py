import os
import discord
from discord.ext import commands, tasks
import aiohttp
from dotenv import load_dotenv

load_dotenv()

#stole most of this code from my old expect bot so dont be suprised if its poorly made

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")

class LastFmCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_track = None
        self.update_presence_task = None
        self.ready = False
        bot.loop.create_task(self.wait_until_ready())

    async def wait_until_ready(self):
        await self.bot.wait_until_ready()
        self.ready = True
        self.update_presence.start()

    @tasks.loop(seconds=60)
    async def update_presence(self):
        print("Looped!")
        if not self.ready:
            return
        track = await self.fetch_current_track()
        if track and track != self.current_track:
            self.current_track = track
            artist, song = track
            activity_name = f"{artist} - {song}"
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=activity_name))
            print(f"Updated song to {artist} - {song}")
        else:
            print("LastFM gave me the same track! not updating...")

    @update_presence.before_loop
    async def before_update_presence(self):
        await self.bot.wait_until_ready()

    @commands.command(name="lastfm")
    async def lastfm_command(self, ctx):
        track = await self.fetch_current_track()
        if not track:
            await ctx.send("No track currently playing or could not fetch data")
            return
        self.current_track = track
        artist, song = track
        activity_name = f"{artist} - {song}"
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=activity_name))
        await ctx.send(f"Updated presence to: Listening to {activity_name}")

    async def fetch_current_track(self):
        url = (
            f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks"
            f"&user={LASTFM_USERNAME}&api_key={LASTFM_API_KEY}&format=json&limit=1"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        recenttracks = data.get("recenttracks", {}).get("track", [])
        if not recenttracks:
            return None

        track = recenttracks[0]
        if '@attr' in track and track['@attr'].get('nowplaying') == 'true':
            artist = track.get('artist', {}).get('#text', 'Unknown Artist')
            song = track.get('name', 'Unknown Song')
            return artist, song
        return None

async def setup(bot):
    await bot.add_cog(LastFmCog(bot))
