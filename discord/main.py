import discord, asyncio, sans, os, logging, sys
from discord.ext import commands
from redis_om import Migrator

from cogs.api import APIClient
from cogs.cache import CacheManager
from cogs.events import EventListener
from cogs.recruit import RecruitmentManager
from cogs.happenings import HappeningsFeed
from cogs.rmb import RMBFeed
from cogs.wastats import WAStatsCog
from cogs.tart import TartCog
from cogs.inactive import InactiveNationsCog
from cogs.version import VersionCog

logger = logging.getLogger("main")

VERSION = "0.0.1"

class PolarisBot(commands.Bot):
    def __init__(self, userAgent: str, region: str):
        intents: discord.Intents = discord.Intents.default()
        intents.members = True

        super().__init__(command_prefix="?", intents=intents)

        self.userAgent = userAgent
        self.region = region

    async def setup_hook(self):
        loop = asyncio.get_event_loop()
        loop.set_task_factory(asyncio.eager_task_factory)

        await self.add_cog(APIClient(self))
        await self.add_cog(EventListener(self))
        await self.add_cog(CacheManager(self, self.region))
        await self.add_cog(RecruitmentManager(self, self.userAgent))
        await self.add_cog(HappeningsFeed(self))
        await self.add_cog(RMBFeed(self))
        await self.add_cog(WAStatsCog(self))
        await self.add_cog(TartCog(self, self.userAgent))
        await self.add_cog(InactiveNationsCog(self))
        await self.add_cog(VersionCog(self, VERSION))

        self.dispatch('startJobs')

    async def on_ready(self):
        global nation_name
        logger.info(f'Polaris: logged in as {self.user}')

        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.warning(f"Error syncing commands: {e}")

def main() -> None:
    nation = os.getenv("POLARIS_NATION")
    token = os.getenv("POLARIS_TOKEN")
    region = os.getenv("POLARIS_REGION")

    logging.basicConfig(level=logging.INFO)

    if not nation or not token or not region:
        print("Please provide a user agent, region and/or token in the environment!\n"
              "docker-compose should do this automatically if you have a proper .env file.",
              file=sys.stderr)

    userAgent = sans.set_agent(f"Polaris/{VERSION} by Merethin, used by {nation}")
    logger.info(f"User agent set to {userAgent}")

    Migrator().run()

    bot = PolarisBot(userAgent=nation, region=region)
    bot.run(token=token)

if __name__ == "__main__":
    main()