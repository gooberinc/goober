from discord.ext import commands
import discord
from collections import defaultdict, Counter
import datetime
from modules.globalvars import ownerid
class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.utcnow()
        self.active_users = set()
        self.total_messages = 0
        self.command_usage = Counter()
        self.user_message_counts = Counter()
        self.messages_per_hour = defaultdict(int)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        self.active_users.add(message.author.id)
        self.total_messages += 1
        self.user_message_counts[message.author.id] += 1

        now = datetime.datetime.utcnow()
        hour_key = now.strftime("%Y-%m-%d %H")
        self.messages_per_hour[hour_key] += 1

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.command_usage[ctx.command.qualified_name] += 1

    @commands.command()
    async def spyware(self, ctx):
        if ctx.author.id != ownerid:
            return
        uptime = datetime.datetime.utcnow() - self.start_time
        hours_elapsed = max((uptime.total_seconds() / 3600), 1)
        avg_per_hour = self.total_messages / hours_elapsed
        if self.messages_per_hour:
            peak_hour, peak_count = max(self.messages_per_hour.items(), key=lambda x: x[1])
        else:
            peak_hour, peak_count = "N/A", 0

        top_users = self.user_message_counts.most_common(5)

        embed = discord.Embed(title="Community Stats", color=discord.Color.blue())
        embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=False)
        embed.add_field(name="Total Messages", value=str(self.total_messages), inline=True)
        embed.add_field(name="Active Users", value=str(len(self.active_users)), inline=True)
        embed.add_field(name="Avg Messages/Hour", value=f"{avg_per_hour:.2f}", inline=True)
        embed.add_field(name="Peak Hour (UTC)", value=f"{peak_hour}: {peak_count} messages", inline=True)

        top_str = "\n".join(
            f"<@{user_id}>: {count} messages" for user_id, count in top_users
        ) or "No data"
        embed.add_field(name="Top Chatters", value=top_str, inline=False)

        cmd_str = "\n".join(
            f"{cmd}: {count}" for cmd, count in self.command_usage.most_common(5)
        ) or "No commands used yet"
        embed.add_field(name="Top Commands", value=cmd_str, inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StatsCog(bot))
