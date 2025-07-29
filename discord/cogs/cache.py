from discord.ext import commands, tasks
import time, asyncio, logging
from classes import *
from lib import displayName

from cogs.api import APIClient

logger = logging.getLogger("cache")

class CacheManager(commands.Cog):
    waNations: set[str]
    puppetRegions: set[str]
    jumpPointRegions: set[str]
    nations: dict[str, Nation]
    mainRegion: Region
    regionalNations: dict[str, set[str]]

    def __init__(self, bot: commands.Bot, mainRegionId: str):
        self.bot = bot
        self.mainRegionId = mainRegionId
        self.api: APIClient = self.bot.get_cog('APIClient')

        self.waNations = set()
        self.puppetRegions = set()
        self.jumpPointRegions = set()
        self.nations = {}
        self.mainRegion = None
        self.regionalNations = {}

        self.needsRebuild = False
        self.lastRebuildStart = 0
        self.lastRebuildEnd = 0

    async def fetchWa(self) -> None:
        self.waNations = await self.api.fetchWaNations()

    async def fetchPuppetRegions(self) -> None:
        self.puppetRegions = await self.api.fetchRegionsByTag(['Puppet Storage'])

    async def fetchJumpPointRegions(self) -> None:
        self.jumpPointRegions = await self.api.fetchRegionsByTag(['Jump Point'])

    async def fetchNation(self, id: str) -> None:
        nation = await self.api.fetchNation(id)
        if nation:
            self.nations[id] = nation

    async def fetchRegion(self, id: str) -> None:
        region = await self.api.fetchRegion(id)
        if region:
            self.mainRegion = region

    def nation(self, id: str) -> Nation | None:
        return self.nations.get(id)
    
    def region(self) -> Region:
        return self.mainRegion
    
    def isNationCached(self, id: str) -> bool:
        return id in self.nations.keys()
    
    def inWa(self, nationId: str) -> bool:
        return nationId in self.waNations
    
    def worldWaNations(self) -> set[str]:
        return self.waNations

    def firstCacheComplete(self) -> bool:
        return self.lastRebuildEnd > 0
    
    def lookupNationName(self, nationId: str) -> str:
        nation = self.nation(nationId)
        if nation:
            return nation.name
        return displayName(nationId)
    
    def lookupRegionName(self, regionId: str) -> str:
        if regionId == self.mainRegionId:
            return self.mainRegion.name
        return displayName(regionId)
    
    def regionWaNations(self) -> set[str]:
        return self.waNations & self.mainRegion.nations

    def isJPOrPuppetStorage(self, regionId: str) -> bool:
        return regionId in self.puppetRegions or regionId in self.jumpPointRegions
    
    def inRegion(self, nationId: str, regionId: str) -> bool:
        if regionId not in self.regionalNations.keys():
            return False
        
        return nationId in self.regionalNations[regionId]
    
    def verifyEndo(self, nationId: str, endorserId: str) -> bool:
        if not self.inWa(nationId) or not self.inWa(endorserId):
            return False
        
        # In theory verifyEndorsement should only be called for cached nations, but just check
        if not self.isNationCached(nationId):
            return False
        
        if not self.inRegion(endorserId, self.nation(nationId).region):
            return False
        
        return True
    
    def verifiedEndorsements(self, nationId: str) -> set[str]:
        if not self.isNationCached(nationId):
            return set()
        
        endorsements = set()
        for endo in self.nation(nationId).endorsements:
            if self.verifyEndo(nationId, endorserId=endo):
                endorsements.add(endo)

        return endorsements
    
    def endorsementsGiven(self, nationId: str) -> set[str]:
        if not self.isNationCached(nationId):
            return set()

        regionId = self.nation(nationId).region
        if regionId != self.mainRegionId:
            return set()
        
        endorsements = set()
        for endorsee in self.regionWaNations():
            if endorsee == nationId:
                continue

            if nationId in self.nation(endorsee).endorsements and self.verifyEndo(endorsee, nationId):
                endorsements.add(endorsee)

        return endorsements
    
    @tasks.loop(minutes=30)
    async def checkForRebuild(self):
        if self.lastRebuildStart > self.lastRebuildEnd:
            # Cache is already rebuilding
            return
        
        timeSinceLastRebuild = time.time() - self.lastRebuildEnd

        if timeSinceLastRebuild < (3600 * 2):
            # Less than 2h since last rebuild
            return
        
        if not self.needsRebuild and timeSinceLastRebuild < (3600 * 24):
            # Skip if we don't need a rebuild, but do force a rebuild every 24h
            return

        await self.rebuildCache()
    
    async def rebuildCache(self):
        self.lastRebuildStart = time.time()

        logger.info(f"cache: Building regional cache for {self.mainRegionId}")
        
        await self.fetchWa()
        logger.info(f"cache: Queried list of WA members ({len(self.waNations)})")

        await asyncio.sleep(1)

        await self.fetchJumpPointRegions()
        logger.info(f"cache: Queried list of jump points ({len(self.jumpPointRegions)})")

        await asyncio.sleep(1)

        await self.fetchPuppetRegions()
        logger.info(f"cache: Queried list of puppet storages ({len(self.puppetRegions)})")

        await asyncio.sleep(1)

        self.regionalNations = {}

        await self.fetchRegion(self.mainRegionId)

        self.regionalNations[self.mainRegionId] = self.mainRegion.nations
        logger.info(f"Queried list of residents for {self.mainRegion.name} ({len(self.mainRegion.nations)})")

        await asyncio.sleep(1)

        for nationId in self.regionWaNations():
            await self.fetchNation(nationId)

            nation = self.nation(nationId)
            logger.info(f"Queried WA nation {nation.name} in {self.mainRegion.name} with {len(self.verifiedEndorsements(nationId))} verified endorsements")

            await asyncio.sleep(1.2)
    
        logger.debug(f"Region: {self.mainRegion}")
        logger.debug(f"Nations: {list[self.nations.values()]}")

        self.lastRebuildEnd = time.time()
        self.needsRebuild = False

        self.bot.dispatch('cacheRebuildComplete')
        logger.info(f"Cache rebuild completed after {self.lastRebuildEnd-self.lastRebuildStart} seconds.")

    def markCacheOutdated(self) -> None:
        self.needsRebuild = True
    
    @commands.Cog.listener()
    async def on_eventCte(self, nationId: str, regionId: str) -> None:
        if regionId in self.regionalNations.keys():
            self.regionalNations[regionId].discard(nationId)

        if self.isNationCached(nationId):
            del self.nations[nationId]

        if regionId == self.mainRegionId:
            try:
                self.mainRegion.nations.remove(nationId)

                if self.inWa(nationId):
                    self.waNations.remove(nationId)
                    self.bot.dispatch('localWaCte', nationId, regionId)
                    logger.warning(f"WA nation {nationId} ceased to exist in {regionId}")
                else:
                    self.bot.dispatch('localCte', nationId, regionId)
                    logger.info(f"Non-WA nation {nationId} ceased to exist in {regionId}")
            except KeyError:
                self.markCacheOutdated()
        else:
            self.waNations.discard(nationId)

    @commands.Cog.listener()
    async def on_eventFounding(self, nationId: str, event: str, regionId: str) -> None:
        if regionId not in self.regionalNations.keys():
            self.regionalNations[regionId] = set()

        self.regionalNations[regionId].add(nationId)

        if regionId == self.mainRegionId:
            self.mainRegion.nations.add(nationId)
            self.bot.dispatch('localFounding', nationId, event, regionId)
        else:
            self.bot.dispatch('worldFounding', nationId, event, regionId)

        logger.info(f"Nation {nationId} was {event} in {regionId}")

    @commands.Cog.listener()
    async def on_eventMove(self, nationId: str, sourceId: str, targetId: str) -> None:
        if sourceId in self.regionalNations.keys():
            self.regionalNations[sourceId].discard(nationId)

        if targetId not in self.regionalNations.keys():
            self.regionalNations[targetId] = set()

        self.regionalNations[targetId].add(nationId)

        if self.isNationCached(nationId):
            self.nation(nationId).region = targetId
            self.nation(nationId).resetResidency()
            self.nation(nationId).resetLogin()

        if sourceId == self.mainRegionId:
            try:
                self.mainRegion.nations.remove(nationId)
            except KeyError:
                self.markCacheOutdated()
            
            if self.inWa(nationId):
                self.bot.dispatch('localWaLeave', nationId, sourceId, targetId)
                logger.warning(f"WA nation {nationId} left {targetId}")
            else:
                self.bot.dispatch('localLeave', nationId, sourceId, targetId)
                logger.info(f"Nation {nationId} left {sourceId}")
        elif targetId == self.mainRegionId:
            self.mainRegion.nations.add(nationId)

            if self.inWa(nationId):
                if not self.isNationCached(nationId):
                    await self.fetchNation(nationId)
                    self.bot.dispatch('localWaJoin', nationId, sourceId, targetId)
                    logger.warning(f"WA nation {nationId} joined {targetId}")
            else:
                self.bot.dispatch('localJoin', nationId, sourceId, targetId)
                logger.info(f"Nation {nationId} joined {targetId}")
        else:
            self.bot.dispatch('worldJoin', nationId, sourceId, targetId)
    
    @commands.Cog.listener()
    async def on_eventWaAdmit(self, nationId: str) -> None:
        self.waNations.add(nationId)

        if self.isNationCached(nationId):
            self.nation(nationId).waStatus = WA_MEMBER
            self.nation(nationId).resetLogin()

        if nationId in self.mainRegion.nations:
            if not self.isNationCached(nationId):
                await self.fetchNation(nationId)

            self.bot.dispatch('localWaAdmit', nationId, self.mainRegionId)
            logger.warning(f"Nation {nationId} joined the WA in {self.mainRegionId}")
        else:
            self.bot.dispatch('worldWaAdmit', nationId)
            logger.info(f"Nation {nationId} joined the WA")

    @commands.Cog.listener()
    async def on_eventWaApply(self, nationId: str) -> None:
        if nationId in self.mainRegion.nations:
            self.bot.dispatch('localWaApply', nationId, self.mainRegionId)
            logger.info(f"Nation {nationId} applied to join the WA in {self.mainRegionId}")
        else:
            self.bot.dispatch('worldWaApply', nationId)
            logger.info(f"Nation {nationId} applied to join the WA")

    @commands.Cog.listener()
    async def on_eventWaResign(self, nationId: str) -> None:
        try:
            self.waNations.remove(nationId)
        except KeyError:
            self.markCacheOutdated()

        if self.isNationCached(nationId):
            self.nation(nationId).waStatus = NON_WA
            self.nation(nationId).endorsements = set()
            self.nation(nationId).resetLogin()

            if nationId in self.mainRegion.nations:
                self.bot.dispatch('localWaResign', nationId, self.mainRegionId)
                logger.info(f"Nation {nationId} left the WA in {self.mainRegionId}")

    @commands.Cog.listener()
    async def on_eventEndo(self, sourceId: str, targetId: str) -> None:
        if self.isNationCached(targetId):
            self.nation(targetId).endorsements.add(sourceId)

            if targetId in self.mainRegion.nations:
                if targetId == self.mainRegion.delegate:
                    self.bot.dispatch('localDelEndo', sourceId, targetId, self.mainRegionId)
                    logger.info(f"Nation {sourceId} endorsed the delegate {targetId} in {self.mainRegionId}")
                else:
                    self.bot.dispatch('localWaEndo', sourceId, targetId, self.mainRegionId)
                    logger.info(f"Nation {sourceId} endorsed {targetId} in {self.mainRegionId}")

        if self.isNationCached(sourceId):
            self.nation(sourceId).resetLogin()

    @commands.Cog.listener()
    async def on_eventUnendo(self, sourceId: str, targetId: str) -> None:
        try:
            if self.isNationCached(targetId):
                self.nation(targetId).endorsements.remove(sourceId)

                if targetId in self.mainRegion.nations:
                    if targetId == self.mainRegion.delegate:
                        self.bot.dispatch('localDelUnendo', sourceId, targetId, self.mainRegionId)
                        logger.warning(f"Nation {sourceId} unendorsed the delegate {targetId} in {self.mainRegionId}")
                    else:
                        self.bot.dispatch('localWaUnendo', sourceId, targetId, self.mainRegionId)
                        logger.info(f"Nation {sourceId} unendorsed {targetId} in {self.mainRegionId}")
        except KeyError:
            self.markCacheOutdated()

        if self.isNationCached(sourceId):
            self.nation(sourceId).resetLogin()

    @commands.Cog.listener()
    async def on_eventRegionUpdate(self, regionId: str) -> None:
        if regionId in self.regionalNations.keys():
            for nation in self.regionalNations[regionId]:
                if self.isNationCached(nation):
                    self.nation(nation).endorsements = self.verifiedEndorsements(nationId=nation)

        if regionId == self.mainRegionId:
            self.bot.dispatch('localUpdate', regionId)
            logger.info(f"Region {regionId} updated")

    @commands.Cog.listener()
    async def on_eventFlag(self, nationId: str) -> None:
        if self.isNationCached(nationId):
            # we mark this so we don't query the new flag until it's needed
            self.nation(nationId).flagDirty = True
            self.nation(nationId).resetLogin()

            if nationId in self.mainRegion.nations:
                self.bot.dispatch('localFlagChange', nationId, self.mainRegionId)
                logger.info(f"Nation {nationId} altered its national flag in {self.mainRegionId}")

    @commands.Cog.listener()
    async def on_eventNewDelegate(self, newDelegateId: str, regionId: str) -> None:
        if self.isNationCached(newDelegateId):
            self.nation(newDelegateId).waStatus = WA_DELEGATE

        if regionId == self.mainRegionId:
            self.mainRegion.delegate = newDelegateId
            self.bot.dispatch('localNewDelegate', newDelegateId, regionId)
            logger.warning(f"Nation {newDelegateId} became the delegate in {regionId}")

    @commands.Cog.listener()
    async def on_eventReplaceDelegate(self, newDelegateId: str, regionId: str, oldDelegateId: str) -> None:
        if self.isNationCached(newDelegateId):
            self.nation(newDelegateId).waStatus = WA_DELEGATE

        if self.isNationCached(oldDelegateId):
            self.nation(oldDelegateId).waStatus = WA_MEMBER

        if regionId == self.mainRegionId:
            self.mainRegion.delegate = newDelegateId
            self.bot.dispatch('localReplaceDelegate', newDelegateId, regionId)
            logger.warning(f"Nation {newDelegateId} replaced {oldDelegateId} as delegate in {regionId}")

    @commands.Cog.listener()
    async def on_eventLoseDelegate(self, oldDelegateId: str, regionId: str) -> None:
        if self.isNationCached(oldDelegateId):
            # If the delegacy loss was because of a resignation, this should have been changed to NON_WA.
            if self.nation(oldDelegateId).waStatus == WA_DELEGATE:
                self.nation(oldDelegateId).waStatus = WA_MEMBER

        if regionId == self.mainRegionId:
            self.mainRegion.delegate = None
            self.bot.dispatch('localLoseDelegate', oldDelegateId, regionId)
            logger.warning(f"Nation {oldDelegateId} lost the delegacy in {regionId}")

    @commands.Cog.listener()
    async def on_startJobs(self):
        self.checkForRebuild.start()