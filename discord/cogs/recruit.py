import typing, time, discord, random, asyncio, logging, re
from discord.ext import commands
from discord import app_commands
from collections import deque
from Levenshtein import ratio
from cogs.cache import CacheManager
from datetime import datetime
from classes import *
from lib import normalize

from views.recruit import RecruiterView
from views.cache import getCacheIncompleteEmbed
from views.error import getNonResidentEmbed, getManageGuildRequiredEmbed, getNoRecruitmentEmbed
from views.config.bucket import BucketSelectorView, CreateBucketView
from views.config.template import TemplateSelectorView, CreateTemplateView
from views.tgsetup import TemplateSetupView

from models.recruit import UserTemplateModel, BucketModel, TemplateModel
from models.tgstats import TelegramStats, Recipient
from models.config import ConfigModel

logger = logging.getLogger("recruit")

MAX_NATIONS_PER_TG = 8

class RecruitmentManager(commands.Cog):
    def __init__(self, bot: commands.Bot, userAgent: str):
        self.bot = bot
        self.recruiters: dict[int, typing.Awaitable[None]] = {}
        self.buckets: list[BucketQueue] = []
        self.filteringQueue = deque(maxlen=40)
        self.userAgent = userAgent
        self.cache: CacheManager = self.bot.get_cog('CacheManager')

        self.reloadBuckets()

    def reloadBuckets(self) -> None:
        self.buckets = []

        all_keys = BucketModel.all_pks()
        buckets = [BucketModel.get(key) for key in all_keys]

        for bucketModel in buckets:
            self.buckets.append(BucketQueue.create(
                bucketModel.id,
                bucketModel.filter,
                bucketModel.size,
                bucketModel.priority,
                bucketModel.mode,
                bucketModel.templates,
            ))

    # Sort the guild's buckets by last update in descending order,
    # and return the corresponding ordered indexes
    def sortBuckets(self) -> list[int]:
        buckets = list(enumerate([bucket.lastUpdate() for bucket in self.buckets]))

        buckets.sort(reverse=True, key=lambda v: v[1])

        return [v[0] for v in buckets]

    PUPPET_FILTER_REGEXES = [
        re.compile(r"[a-z0-9_-]+[0-9]+"), # Nations ending with a number
        re.compile(r"[a-z0-9_-]+_m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})") # Nations ending with a space and a roman numeral
    ]
    
    def checkPuppetFilter(self, nation: str) -> bool:
        for regex in self.PUPPET_FILTER_REGEXES:
            if regex.fullmatch(nation) is not None:
                logger.info(f"skipping likely puppet {nation}, which matches a puppet regex")
                return True
            
        puppet_likeliness = 0
        for other_nation in self.filteringQueue:
            likeness = ratio(nation, other_nation)
            if likeness > puppet_likeliness:
                puppet_likeliness = likeness

        if puppet_likeliness < 0.7:
            self.filteringQueue.append(nation)
            return False
        else:
            logger.info(f"skipping likely puppet {nation}, who is {puppet_likeliness} similar to existing nation")
            return True
        
    def popNations(self, bucket: BucketQueue, max: int) -> list[str]:
        result = []

        for i in range(max):
            if bucket.nations:
                (nation, time) = bucket.nations.pop()
                result.append((nation, time - bucket.priority))
            else:
                break

        return result
    
    def addNation(self, nation: str, region: str, event: str) -> None:
        for bucket in reversed(self.buckets):
            if bucket.filter.matches(event, region):
                logger.info(f"added {nation} to bucket '{bucket.name}'")
                bucket.nations.append([nation, time.time()])
                self.bot.dispatch('new_recruit')
                break

    @commands.Cog.listener()
    async def on_worldFounding(self, nationId: str, event: str, regionId: str):
        if self.checkPuppetFilter(nationId):
            return
        
        # don't bother wasting API calls on checking this for newfounds
        if event == "refounded":
            await self.cache.fetchNation(nationId)

            nation = self.cache.nation(nationId)
            if not nation.canRecruit:
                logger.warning(f"skipping new refounded nation {nationId} as it has recruitment telegrams turned off")
                return
        
        self.addNation(nationId, regionId, event)

    @commands.Cog.listener()
    async def on_worldJoin(self, nationId: str, sourceId: str, targetId: str):
        self.addNation(nationId, targetId, "move")

    @commands.Cog.listener()
    async def on_worldWaAdmit(self, nationId: str):
        if self.checkPuppetFilter(nationId):
            return
        
        if not self.cache.isNationCached(nationId):
            await self.cache.fetchNation(nationId)

        nation = self.cache.nation(nationId)
        if not nation.canRecruit:
            logger.warning(f"skipping new WA nation {nationId} as it has recruitment telegrams turned off")
            return
        if nation.population > 500:
            logger.warning(f"skipping new WA nation {nationId} as it has over 500 million population")
            return
        
        if self.cache.isJPOrPuppetStorage(nation.region):
            logger.warning(f"skipping new WA nation {nationId} as it is in a puppet storage or jump point")
            return
        
        self.addNation(nationId, nation.region, "wa")

    def cooldown(self, nation: Nation) -> float:
        daysSinceFounding = (time.time() - nation.foundedAt) / 86400

        # min cooldown (5 seconds per nation) at 18 months
        if daysSinceFounding >= (18 * 30):
            return 5.0
        
        # max cooldown (14 seconds per nation), 1 second less per 2 months of existence
        return 14.0 - (daysSinceFounding / 60.0)

    def findTelegramDetails(self, userId: int, templateId: str) -> str | None:
        query = (UserTemplateModel.id == templateId) & (UserTemplateModel.user == userId)
        result = UserTemplateModel.find(query).all()
        if len(result) > 0:
            return result[0].tgid
        return None

    async def recruitmentTask(self, 
                              interaction: discord.Interaction, 
                              nation: Nation, 
                              timer: int | None, 
                              confirm: bool = False) -> None:
        
        if timer is None:
            await interaction.response.send_message(
                f"{interaction.user.mention} has started recruiting with the dynamic timer")
        else:
            await interaction.response.send_message(
                f"{interaction.user.mention} has started recruiting every {timer} seconds")

        cooldownTimer = None

        # outer loop: loops indefinitely
        while True:
            # inner loop: loops until there are nations to telegram, 
            # then breaks so that the timer can handle the rate limiting
            while True:
                logger.info(f"querying nations to telegram for {interaction.user.name}")
                
                order = self.sortBuckets()

                for i in order:
                    bucket = self.buckets[i]
                    if bucket.supportsManual():
                        targets = self.popNations(bucket, MAX_NATIONS_PER_TG)

                        if len(targets) == 0:
                            continue

                        template = random.choice(bucket.templates)

                        tgid = self.findTelegramDetails(interaction.user.id, template)

                        if not tgid:
                            await interaction.channel.send(f"{interaction.user.mention} does not have the '{template}' template in the {bucket.name} bucket set up!\n"
                                                           "Please re-run /setup before recruiting.")
                            self.recruiters[interaction.user.id] = None
                            return
                        
                        message = await RecruiterView(
                            interaction.user, 
                            self.userAgent, tgid, 
                            [t[0] for t in targets], nation.id).send(interaction.channel)

                        TelegramStats(
                            timestamp=time.time(),
                            sender=interaction.user.id,
                            senderDisplayName=interaction.user.name,
                            bucket=bucket.name,
                            template=template,
                            recipients=[Recipient(name, time) for name, time in targets]
                        ).save()

                        if confirm:
                            def check(reaction, user):
                                return reaction.message.id == message.id and user.id == interaction.user.id
                            
                            try:
                                await self.bot.wait_for('reaction_add', check=check, timeout=300)
                            except asyncio.TimeoutError:
                                await interaction.channel.send(
                                    f"{interaction.user.mention} has not reacted to a recruitment message in the last 5 minutes! Stopping.")
                                self.recruiters[interaction.user.id] = None
                                return

                        cooldownTimer = self.cooldown(nation) * len(targets)
                        if not confirm:
                            cooldownTimer += 5 # extra 5 seconds of buffer time

                        break
                else:
                    logger.info(f"no new nations, waiting for something to happen")
                    _ = await self.bot.wait_for('new_recruit')
                    continue

                break
            
            if timer is None:
                logger.info(f"next recruitment message for {interaction.user.name} in {cooldownTimer} seconds")
                await asyncio.sleep(cooldownTimer)
            else:
                logger.info(f"next recruitment message for {interaction.user.name} in {timer} seconds")
                await asyncio.sleep(timer)

    def canRecruit(self, interaction: discord.Interaction) -> bool:
        config = ConfigModel.load()

        if not config.recruitRole:
            return False
        
        return interaction.user.get_role(config.recruitRole) is not None
    
    @app_commands.command(description="Start a recruitment session.")
    async def recruit(self, interaction: discord.Interaction, 
                      nation: str, 
                      timer: int | None, 
                      confirm: bool = False):
        nationId = normalize(nation)

        if not self.cache.firstCacheComplete():
            await interaction.response.send_message(embed=getCacheIncompleteEmbed())
            return
        
        if not self.canRecruit(interaction):
            await interaction.response.send_message(embed=getNoRecruitmentEmbed())
            return
        
        if interaction.user.id in self.recruiters:
            await interaction.response.send_message(f"You already have a recruitment session active!", ephemeral=True)
            return
        
        if nationId not in self.cache.mainRegion.nations:
            await interaction.response.send_message(embed=getNonResidentEmbed(nation, self.cache.mainRegion.name))
            return
        
        if not self.cache.isNationCached(nationId): # non-WA probably
            await self.cache.fetchNation(nation)

        minimumTimer = self.cooldown(self.cache.nation(nationId)) * 8
        if timer and timer < minimumTimer:
            await interaction.response.send_message(f"Timer too fast! Your nation can only recruit once every {minimumTimer} seconds.\n" 
                                                    "It is recommended to set the timer slightly above that.", ephemeral=True)
            return
        
        task = asyncio.create_task(self.recruitmentTask(interaction, 
                                                        self.cache.nation(nationId),
                                                        timer,
                                                        confirm))
        self.recruiters[interaction.user.id] = task

        await task

    @app_commands.command(description="Stop a recruitment session.")
    async def stop(self, interaction: discord.Interaction):
        if interaction.user.id not in self.recruiters:
            await interaction.response.send_message(f"You do not have a recruitment session active!", ephemeral=True)
            return
        
        task = self.recruiters[interaction.user.id]
        task.cancel()

        del self.recruiters[interaction.user.id]

        await interaction.response.send_message(f"Recruitment session stopped.")

    @app_commands.command(description="View the amount of queued nations per bucket.")
    async def queue(self, interaction: discord.Interaction):
        if not self.canRecruit(interaction):
            await interaction.response.send_message(embed=getNoRecruitmentEmbed())
            return

        description = "\n".join([f"{len(bucket.nations)} nations queued for bucket {bucket.name} (max {bucket.nations.maxlen})" for bucket in self.buckets])

        embed = discord.Embed(title=f"Nations Queued for {self.cache.mainRegion.name}",
                      description=description,
                      colour=0x1c71d8,
                      timestamp=datetime.now())
        
        await interaction.response.send_message(
            embed=embed,
        )

    @app_commands.command(description="Reload recruitment settings.")
    async def reload(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=getManageGuildRequiredEmbed())
            return

        self.reloadBuckets()

        await interaction.response.send_message("Recruitment settings reloaded and buckets cleared.")

    @app_commands.command(description="Set the role that is allowed to recruit.")
    async def setrecruitrole(self, interaction: discord.Interaction, role: discord.Role):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=getManageGuildRequiredEmbed())
            return

        config = ConfigModel.load()
        config.recruitRole = role.id
        config.save()

        await interaction.response.send_message("Recruiter role updated.")

    @app_commands.command(description="Create a new bucket.")
    async def create_bucket(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=getManageGuildRequiredEmbed())
            return

        await CreateBucketView().send(interaction)

    @app_commands.command(description="View, edit and delete existing buckets.")
    async def buckets(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=getManageGuildRequiredEmbed())
            return

        await BucketSelectorView().send(interaction)

    @app_commands.command(description="Create a new template.")
    async def create_template(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=getManageGuildRequiredEmbed())
            return

        await CreateTemplateView().send(interaction)

    @app_commands.command(description="View, edit and delete existing templates.")
    async def templates(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=getManageGuildRequiredEmbed())
            return

        await TemplateSelectorView().send(interaction)

    @app_commands.command(description="Setup telegram templates to recruit with.")
    async def setup(self, interaction: discord.Interaction, nation: str):
        if not self.canRecruit(interaction):
            await interaction.response.send_message(embed=getNoRecruitmentEmbed())
            return
        
        nationId = normalize(nation)

        if not self.cache.firstCacheComplete():
            await interaction.response.send_message(embed=getCacheIncompleteEmbed())
            return
        
        if nationId not in self.cache.mainRegion.nations:
            await interaction.response.send_message(embed=getNonResidentEmbed(nation, self.cache.mainRegion.name))
            return
        
        templates = TemplateModel.find(
            TemplateModel.mode != MODE_API
        ).all()
        
        await TemplateSetupView(self.userAgent, 
                                self.cache.mainRegion.name,
                                nationId,
                                templates).send(interaction)