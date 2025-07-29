import discord
from discord.ext import commands
from discord import app_commands
from lib import normalize
from collections import deque

from cogs.cache import CacheManager

from views.tart import TartView
from views.error import getNonResidentEmbed, getNonWaEmbed
from views.cache import getCacheIncompleteEmbed

class TartCog(commands.Cog):
    def __init__(self, bot: commands.Bot, userAgent: str):
        self.bot = bot
        self.userAgent = userAgent
        self.cache: CacheManager = self.bot.get_cog('CacheManager')
        self.tartViews: dict[str, list[TartView]] = {}

    @app_commands.command(description="Endorse other World Assembly members in the region.")
    async def tart(self, interaction: discord.Interaction, nation: str):
        if not self.cache.firstCacheComplete():
            await interaction.response.send_message(embed=getCacheIncompleteEmbed())
            return
        
        nationId = normalize(nation)

        if nationId not in self.cache.mainRegion.nations:
            await interaction.response.send_message(embed=getNonResidentEmbed(nation, self.cache.mainRegion.name))
            return
        
        if not self.cache.inWa(nationId):
            await interaction.response.send_message(embed=getNonWaEmbed(nation, self.cache.mainRegion.name))
            return
        
        endorsed = self.cache.endorsementsGiven(nationId)
        totalToEndorse = self.cache.regionWaNations()

        nationsToEndorse = list(totalToEndorse-endorsed)
        nationsToEndorse.remove(nationId)

        nationQueue = deque()
        if self.cache.mainRegion.delegate in nationsToEndorse:
            nationsToEndorse.remove(self.cache.mainRegion.delegate)
            nationQueue.appendleft(("Delegate", self.cache.mainRegion.delegate))

        for targetId in nationsToEndorse:
            nationQueue.appendleft((None, targetId))

        view = TartView(
            self,
            self.cache,
            nationId,
            nationQueue,
            self.userAgent
        )

        if nationId not in self.tartViews.keys():
            self.tartViews[nationId] = []

        self.tartViews[nationId].append(view)
        await view.send(interaction)

    def removeView(self, view: TartView, nationId: str):
        try:
            if nationId in self.tartViews.keys():
                self.tartViews[nationId].remove(view)
        except ValueError:
            pass

    async def addNewNation(self, nationId: str):
        for endorserId, views in self.tartViews.items():
            if self.cache.isNationCached(nationId):
                if endorserId in self.cache.nation(nationId).endorsements:
                    continue

            for view in views:
                view.nations.appendleft((None, nationId))
                await view.editMessage()

    async def removeNation(self, nationId: str):
        for endorserId, views in self.tartViews.items():
            if self.cache.isNationCached(nationId):
                if endorserId in self.cache.nation(nationId).endorsements:
                    continue

            for view in views:
                view.nations.remove((None, nationId))
                await view.editMessage()

    async def handleEndo(self, endorserId: str, nationId: str):
        if endorserId in self.tartViews.keys():
            for view in self.tartViews[endorserId]:
                if nationId == view.currentNation:
                    view.queryNewNation()
                    await view.editMessage()
                else:
                    view.nations.remove((None, nationId))
                    await view.editMessage()

    async def handleUnendo(self, endorserId: str, nationId: str):
        if endorserId in self.tartViews.keys():
            for view in self.tartViews[endorserId]:
                view.nations.appendleft((None, nationId))
                await view.editMessage()

    @commands.Cog.listener()
    async def on_localWaLeave(self, nationId: str, sourceId: str, targetId: str):
        await self.removeNation(nationId)

    @commands.Cog.listener()
    async def on_localWaJoin(self, nationId: str, sourceId: str, targetId: str):
        await self.addNewNation(nationId)

    @commands.Cog.listener()
    async def on_localWaCte(self, nationId: str, regionId: str):
        await self.removeNation(nationId)

    @commands.Cog.listener()
    async def on_localWaAdmit(self, nationId: str, regionId: str):
        await self.addNewNation(nationId)

    @commands.Cog.listener()
    async def on_localDelEndo(self, sourceId: str, targetId: str, regionId: str):
        await self.handleEndo(sourceId, targetId)

    @commands.Cog.listener()
    async def on_localWaEndo(self, sourceId: str, targetId: str, regionId: str):
        await self.handleEndo(sourceId, targetId)
        
    @commands.Cog.listener()
    async def on_localDelUnendo(self, sourceId: str, targetId: str, regionId: str):
        await self.handleUnendo(sourceId, targetId)

    @commands.Cog.listener()
    async def on_localWaUnendo(self, sourceId: str, targetId: str, regionId: str):
        await self.handleUnendo(sourceId, targetId)