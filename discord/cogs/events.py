import re, logging
from discord.ext import commands

from cogs.api import APIClient

logger = logging.getLogger("events")

EVENTS: list[tuple[str, re.Pattern]] = [
    ("RegionUpdate", re.compile(r"%%([a-z0-9_\-]+)%% updated\.")),
    ("Endo", re.compile(r"@@([a-z0-9_\-]+)@@ endorsed @@([a-z0-9_\-]+)@@")),
    ("Unendo", re.compile(r"@@([a-z0-9_\-]+)@@ withdrew its endorsement from @@([a-z0-9_\-]+)@@")),
    ("WaApply", re.compile(r"@@([a-z0-9_\-]+)@@ applied to join the World Assembly")),
    ("WaAdmit", re.compile(r"@@([a-z0-9_\-]+)@@ was admitted to the World Assembly")),
    ("WaResign", re.compile(r"@@([a-z0-9_\-]+)@@ resigned from the World Assembly")),
    ("NewDelegate", re.compile(r"@@([a-z0-9_\-]+)@@ became WA Delegate of %%([a-z0-9_\-]+)%%")),
    ("ReplaceDelegate", re.compile(r"@@([a-z0-9_\-]+)@@ seized the position of %%([a-z0-9_\-]+)%% WA Delegate from @@([a-z0-9_\-]+)@@")),
    ("LoseDelegate", re.compile(r"@@([a-z0-9_\-]+)@@ lost WA Delegate status in %%([a-z0-9_\-]+)%%")),
    ("Founding", re.compile(r"@@([a-z0-9_\-]+)@@ was (founded|refounded) in %%([a-z0-9_\-]+)%%")),
    ("Cte", re.compile(r"@@([a-z0-9_\-]+)@@ ceased to exist in %%([a-z0-9_\-]+)%%")),
    ("Move", re.compile(r"@@([a-z0-9_\-]+)@@ relocated from %%([a-z0-9_\-]+)%% to %%([a-z0-9_\-]+)%%")),
    ("Rmb", re.compile(r"@@([a-z0-9_\-]+)@@ lodged <a href=\"/region=(?:[a-z0-9_\-]+)/page=display_region_rmb\?postid=([0-9]+)#p(?:[0-9]+)\">a message</a> on the %%([a-z0-9_\-]+)%% Regional Message Board")),
    ("Flag", re.compile(r"@@([a-z0-9_\-]+)@@ altered its national flag"))
]

class EventListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def listen(self):
        api: APIClient = self.bot.get_cog('APIClient')

        async for event in api.serverSentEvents("admin", 
                                                "endo", 
                                                "founding",
                                                "member", 
                                                "move",
                                                "change",
                                                "rmb"):
            for (event_type, event_regex) in EVENTS:
                match = event_regex.match(event["str"])
                if match is not None:
                    logger.debug(f"new {event_type}: {event["str"]}")
                    self.bot.dispatch(f"event{event_type}", *match.groups())
                    break

    @commands.Cog.listener()
    async def on_startJobs(self):
        await self.listen()