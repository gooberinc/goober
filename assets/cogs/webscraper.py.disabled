import discord
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup
import json
import asyncio
from urllib.parse import urljoin
from modules.globalvars import ownerid 
class WebScraper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.visited_urls = set()

    async def fetch(self, session, url):
        """Fetch the HTML content of a URL."""
        try:
            async with session.get(url, timeout=10) as response:
                return await response.text()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def extract_sentences(self, text):
        """Extract sentences from text."""
        sentences = text.split('.')
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def save_to_json(self, sentences):
        """Save sentences to memory.json."""
        try:
            try:
                with open("memory.json", "r") as file:
                    data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                data = []
            data.extend(sentences)
            with open("memory.json", "w") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print(f"Failed to save to JSON: {e}")

    def undo_last_scrape(self):
        """Undo the last scrape by removing the most recent sentences."""
        try:
            with open("memory.json", "r") as file:
                data = json.load(file)

            if not data:
                print("No data to undo.")
                return False

            
            data = data[:-1]

            with open("memory.json", "w") as file:
                json.dump(data, file, indent=4)

            return True
        except (FileNotFoundError, json.JSONDecodeError):
            print("No data to undo or failed to load JSON.")
            return False
        except Exception as e:
            print(f"Failed to undo last scrape: {e}")
            return False

    async def scrape_links(self, session, url, depth=2):
        print(f"Scraping: {url}")
        self.visited_urls.add(url)

        html = await self.fetch(session, url)
        if not html:
            return

        soup = BeautifulSoup(html, "html.parser")

        for paragraph in soup.find_all('p'):
            sentences = self.extract_sentences(paragraph.get_text())
            self.save_to_json(sentences)


    @commands.command()
    async def start_scrape(self, ctx, start_url: str):
        """Command to start the scraping process."""
        if ctx.author.id != ownerid:
            await ctx.send("You do not have permission to use this command.")
            return

        if not start_url.startswith("http"):
            await ctx.send("Please provide a valid URL.")
            return

        await ctx.send(f"Starting scrape from {start_url}... This may take a while!")

        async with aiohttp.ClientSession() as session:
            await self.scrape_links(session, start_url)

        await ctx.send("Scraping complete! Sentences saved to memory.json.")

    @commands.command()
    async def undo_scrape(self, ctx):
        """Command to undo the last scrape."""
        if ctx.author.id != ownerid:
            await ctx.send("You do not have permission to use this command.")
            return

        success = self.undo_last_scrape()
        if success:
            await ctx.send("Last scrape undone successfully.")
        else:
            await ctx.send("No data to undo or an error occurred.")

async def setup(bot):
    await bot.add_cog(WebScraper(bot))
