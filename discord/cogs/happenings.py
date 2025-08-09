import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from cogs.cache import CacheManager

import views.happenings as views
from views.error import getManageGuildRequiredEmbed
from views.config.events import EventConfigView

from models.config import ConfigModel

class HappeningsFeed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache: CacheManager = self.bot.get_cog('CacheManager')

    def queryChannel(self, event: str) -> tuple[discord.TextChannel | None, str | None]:
        config = ConfigModel.load()

        eventConfig = config.events.get(event)

        if not eventConfig:
            return (None, None)
        
        channel = self.bot.get_channel(eventConfig.channel)
        mention = None

        if eventConfig.role:
            mention = channel.guild.get_role(eventConfig.role).mention

        return (channel, mention)

    @commands.Cog.listener()
    async def on_localLeave(self, nationId: str, sourceId: str, targetId: str):
        channel, message = self.queryChannel("leave")

        if channel:
            await views.NationLeaveView(
                self.cache.lookupNationName(nationId), 
                self.cache.lookupRegionName(sourceId),
                self.cache.lookupRegionName(targetId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localJoin(self, nationId: str, sourceId: str, targetId: str):
        channel, message = self.queryChannel("join")

        if channel:
            await views.NationJoinView(
                self.cache.lookupNationName(nationId), 
                self.cache.lookupRegionName(sourceId),
                self.cache.lookupRegionName(targetId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localWaLeave(self, nationId: str, sourceId: str, targetId: str):
        channel, message = self.queryChannel("waLeave")

        if channel:
            await views.WaNationLeaveView(
                self.cache.lookupNationName(nationId), 
                self.cache.lookupRegionName(sourceId),
                self.cache.lookupRegionName(targetId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localWaJoin(self, nationId: str, sourceId: str, targetId: str):
        channel, message = self.queryChannel("waJoin")

        if channel:
            await views.WaNationJoinView(
                self.cache.lookupNationName(nationId), 
                self.cache.lookupRegionName(sourceId),
                self.cache.lookupRegionName(targetId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localCte(self, nationId: str, regionId: str):
        channel, message = self.queryChannel("cte")

        if channel:
            await views.NationCteView(
                self.cache.lookupNationName(nationId), 
                self.cache.lookupRegionName(regionId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localWaCte(self, nationId: str, regionId: str):
        channel, message = self.queryChannel("waCte")

        if channel:
            await views.WaNationCteView(
                self.cache.lookupNationName(nationId), 
                self.cache.lookupRegionName(regionId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localFounding(self, nationId: str, event: str, regionId: str):
        channel, message = self.queryChannel(event)

        if channel:
            if event == "founded":
                await views.NationFoundView(
                    self.cache.lookupNationName(nationId), 
                    self.cache.lookupRegionName(regionId),
                    datetime.now(timezone.utc)
                ).send(channel, message)
            elif event == "refounded":
                await views.NationRefoundView(
                    self.cache.lookupNationName(nationId), 
                    self.cache.lookupRegionName(regionId),
                    datetime.now(timezone.utc)
                ).send(channel, message)

    @commands.Cog.listener()
    async def on_localWaApply(self, nationId: str, regionId: str):
        channel, message = self.queryChannel("apply")

        if channel:
            await views.WAApplyView(
                self.cache.lookupNationName(nationId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localWaAdmit(self, nationId: str, regionId: str):
        channel, message = self.queryChannel("admit")

        if channel:
            await views.WAAdmitView(
                self.cache.lookupNationName(nationId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localWaResign(self, nationId: str, regionId: str):
        channel, message = self.queryChannel("resign")

        if channel:
            await views.WAResignView(
                self.cache.lookupNationName(nationId), 
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localDelEndo(self, sourceId: str, targetId: str, regionId: str):
        channel, message = self.queryChannel("delEndo")

        if channel:
            await views.DelegateEndorsementView(
                self.cache.lookupNationName(sourceId),
                self.cache.lookupNationName(targetId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localWaEndo(self, sourceId: str, targetId: str, regionId: str):
        channel, message = self.queryChannel("endo")

        if channel:
            await views.EndorsementView(
                self.cache.lookupNationName(sourceId),
                self.cache.lookupNationName(targetId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localDelUnendo(self, sourceId: str, targetId: str, regionId: str):
        channel, message = self.queryChannel("delUnendo")

        if channel:
            await views.DelegateUnEndorsementView(
                self.cache.lookupNationName(sourceId),
                self.cache.lookupNationName(targetId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @commands.Cog.listener()
    async def on_localWaUnendo(self, sourceId: str, targetId: str, regionId: str):
        channel, message = self.queryChannel("unendo")

        if channel:
            await views.UnEndorsementView(
                self.cache.lookupNationName(sourceId),
                self.cache.lookupNationName(targetId),
                datetime.now(timezone.utc)
            ).send(channel, message)

    @app_commands.command(description="Edit event settings.")
    async def events(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=getManageGuildRequiredEmbed())
            return
        
        await EventConfigView(self.bot).send(interaction)