import discord, time, asyncio
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from cogs.cache import CacheManager
from cogs.api import APIClient

from views.rmb import RMBView
from views.error import getManageGuildRequiredEmbed
from views.config.rmb import RMBConfigView

from models.config import ConfigModel

class RMBFeed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache: CacheManager = self.bot.get_cog('CacheManager')
        self.api: APIClient = self.bot.get_cog('APIClient')
        self.lastUpdate: float = 0
        self.views: dict[int, RMBView] = {}
        self.updating: bool = False

    def queryChannel(self) -> tuple[discord.TextChannel | None]:
        config = ConfigModel.load()

        if not config.rmbChannel:
            return None

        return self.bot.get_channel(config.rmbChannel)
    
    MAX_RMB_UPDATE_FREQUENCY = 15 # maximum query the RMB once every 15 seconds
    
    async def updateRmb(self):
        if self.updating:
            return # already another coroutine updating the RMB
        
        channel = self.queryChannel()
        if not channel:
            return # rmb feed disabled
        
        self.updating = True

        timeSinceLastUpdate = (time.time() - self.lastUpdate)
        
        if timeSinceLastUpdate < self.MAX_RMB_UPDATE_FREQUENCY:
            await asyncio.sleep(self.MAX_RMB_UPDATE_FREQUENCY - timeSinceLastUpdate)

        messages = await self.api.fetchRMBPosts(
            self.cache.mainRegionId,
            0,
            10
        )

        config = ConfigModel.load()

        for message in messages:
            if message.id in self.views:
                await self.views[message.id].update(message)
            else:
                if message.id <= config.rmbLastPost:
                    continue

                self.views[message.id] = RMBView(
                    self.cache, message, self.cache.mainRegionId)
                await self.views[message.id].send(channel)
                config.rmbLastPost = message.id

        config.save()
        self.lastUpdate = time.time()
        self.updating = False

    @commands.Cog.listener()
    async def on_localRmb(self, nationId: str, postId: str, regionId: str):
        await self.updateRmb()

    @commands.Cog.listener()
    async def on_localSuppress(self, nationId: str, regionId: str):
        await self.updateRmb()

    @commands.Cog.listener()
    async def on_localUnsuppress(self, nationId: str, regionId: str):
        await self.updateRmb()

    @app_commands.command(description="Edit RMB feed settings.")
    async def rmbfeed(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=getManageGuildRequiredEmbed())
            return
        
        await RMBConfigView(self.bot).send(interaction)