import discord, time, dateparser, io
from discord.ext import commands
from discord import app_commands
from datetime import timezone, date
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from redis_om import Migrator

from cogs.cache import CacheManager

from views.cache import getCacheIncompleteEmbed
from views.wastats import getWaStatsEmbed

from models.wastats import WaStats

def savePlotToDiscordFile(filename: str, plot: Figure) -> discord.File:
    data_stream = io.BytesIO()
    plot.savefig(data_stream, format='png', bbox_inches="tight", dpi = 80)

    data_stream.seek(0)
    return discord.File(data_stream, filename=filename)

class WAStatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache: CacheManager = self.bot.get_cog('CacheManager')

    def calculateStats(self) -> WaStats:
        waNations = self.cache.regionWaNations()
        waCount = len(waNations)

        delEndos = 0
        delegateId = self.cache.region().delegate
        if delegateId:
            delEndos = len(self.cache.nation(delegateId).endorsements)

        potentialEndos = waCount * (waCount - 1)
        endosGiven = 0
        for nationId in waNations:
            endosGiven += len(self.cache.verifiedEndorsements(nationId))
        
        return WaStats(timestamp=time.time(), waCount=waCount, 
                       delEndos=delEndos, potentialEndos=potentialEndos, 
                       endosGiven=endosGiven)

    @commands.Cog.listener()
    async def on_cacheRebuildComplete(self):
        stats = self.calculateStats()
        stats.save()

    @app_commands.command(description="Display WA engagement rates for the region.")
    async def wastats(self, interaction: discord.Interaction):
        if not self.cache.firstCacheComplete():
            await interaction.response.send_message(embed=getCacheIncompleteEmbed())
            return
        
        stats = self.calculateStats()

        await interaction.response.send_message(embed=getWaStatsEmbed(self.cache.mainRegion.name, stats))

    @app_commands.command(description="Display historical WA engagement rates for the region.")
    async def wahistory(self, interaction: discord.Interaction, start: str, end: str):
        SETTINGS = {'DATE_ORDER': 'DMY', 'TIMEZONE': 'UTC', 'TO_TIMEZONE': 'UTC', 'PREFER_DAY_OF_MONTH': 'first'}

        startTime = dateparser.parse(start, settings=SETTINGS)
        endTime = dateparser.parse(end, settings=SETTINGS)

        if not startTime:
            await interaction.response.send_message(f"Error: '{start}' is not a valid date or time!")
            return
        
        if not endTime:
            await interaction.response.send_message(f"Error: '{end}' is not a valid date or time!")
            return

        startTimestamp = startTime.replace(tzinfo=timezone.utc).timestamp()
        endTimestamp = endTime.replace(tzinfo=timezone.utc).timestamp()

        await interaction.response.send_message(f"Generating history graph from <t:{int(startTimestamp)}> to <t:{int(endTimestamp)}>")

        query = (WaStats.timestamp >= startTimestamp) & (WaStats.timestamp <= endTimestamp)
        stats = WaStats.find(query).all()

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot([date.fromtimestamp(s.timestamp) for s in stats], [s.waCount for s in stats])
        ax.plot([date.fromtimestamp(s.timestamp) for s in stats], [s.delEndos for s in stats])
        ax.set_title("WA Nation and Delegate Endorsement Graph")
        await interaction.channel.send(file=savePlotToDiscordFile("delendos.png", fig))

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        plt.plot([date.fromtimestamp(s.timestamp) for s in stats], [s.delegateRatio() for s in stats])
        plt.plot([date.fromtimestamp(s.timestamp) for s in stats], [s.regionRatio() for s in stats])
        ax.set_title("Endorsement Rates Graph")
        await interaction.channel.send(file=savePlotToDiscordFile("endorates.png", fig))