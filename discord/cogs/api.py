import sans, logging, httpx, asyncio, time
from discord.ext import commands
from lib import normalize
from classes import *

logger = logging.getLogger("api")

class APIClient(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = sans.AsyncClient()

    async def fetchWaNations(self) -> set[str]:
        while True:
            try:
                response = await self.client.get(sans.WA(1, "members"))
                return set(response.xml.find("./MEMBERS").text.split(","))
            except httpx.ReadTimeout:
                logger.warning("response for fetchWa() timed out, retrying in 10 seconds")
                await asyncio.sleep(10)

    async def fetchRegionsByTag(self, tags: list[str]) -> set[str]:
        while True:
            try:
                response = await self.client.get(sans.World("regionsbytag", tags=normalize('+'.join(tags))))
                regions = response.xml.find("./REGIONS")
                if regions.text is None:
                    # No regions with said tag combination/tags do not exist
                    return set()
                
                return set([normalize(r) for r in regions.text.split(",")])
            except httpx.ReadTimeout:
                logger.warning(f"response for fetchRegionsByTag({tags}) timed out, retrying in 10 seconds")
                await asyncio.sleep(10)

    async def fetchNation(self, id: str) -> Nation | None:
        while True:
            try:
                response = await self.client.get(
                    sans.Nation(id, 
                                "name", "flag", "wa", 
                                "region", "endorsements", "lastlogin", 
                                "census", "population", "tgcanrecruit",
                                "foundedtime", 
                                scale="80", mode="score"))
                
                if response.status_code == 404:
                    # Nation not found
                    return None
                
                name = response.xml.find("./NAME").text
                flagUrl = response.xml.find("./FLAG").text
                region = normalize(response.xml.find("./REGION").text)
                lastLogin = int(response.xml.find("./LASTLOGIN").text)
                residency = float(response.xml.find("./CENSUS/SCALE/SCORE").text)
                population = int(response.xml.find("./POPULATION").text)
                canRecruit = response.xml.find("./TGCANRECRUIT").text == "1"
                foundedAt = int(response.xml.find("./FOUNDEDTIME").text)

                waStatus = NON_WA
                waStatusText = response.xml.find("./UNSTATUS").text
                if waStatusText == "WA Member":
                    waStatus = WA_MEMBER
                elif waStatusText == "WA Delegate":
                    waStatus = WA_DELEGATE

                endorsements = set()
                if waStatus != NON_WA:
                    endoList = response.xml.find("./ENDORSEMENTS").text
                    if endoList:
                        endorsements = set(endoList.split(","))

                updateTime = time.time()
                
                return Nation(id, name, flagUrl, waStatus, region, 
                                endorsements, residency, population, 
                                canRecruit, lastLogin, foundedAt, lastApiUpdateTime=updateTime, 
                                lastResidencyUpdateTime=updateTime)
            except httpx.ReadTimeout:
                logger.warning(f"response for fetchNation({id}) timed out, retrying in 10 seconds")
                await asyncio.sleep(10)

    async def fetchRegion(self, id: str) -> None:
        while True:
            try:
                response = await self.client.get(
                    sans.Region(id, "name", "nations", "delegate", "officers", "recruiters"))

                if response.status_code == 404:
                    # Region not found
                    return None
                
                name = response.xml.find("./NAME").text
                delegate = response.xml.find("./DELEGATE").text
                if delegate == "0":
                    delegate = None

                nations = set(response.xml.find("./NATIONS").text.split(":"))
                recruiters = set(response.xml.find("./RECRUITERS").text.split(","))

                officers = {}

                for officerNode in response.xml.findall("./OFFICERS/OFFICER"):
                    nation = officerNode.find("./NATION").text
                    office = officerNode.find("./OFFICE").text
                    authority = Authority.parse(officerNode.find("./AUTHORITY").text)
                    officers[nation] = RegionalOfficer(nation, office, authority)

                updateTime = time.time()

                return Region(id, name, nations, delegate, 
                            officers, recruiters, lastApiUpdateTime=updateTime)
            except httpx.ReadTimeout:
                logger.warning(f"response for fetchRegion({id}) timed out, retrying in 10 seconds")
                await asyncio.sleep(10)

    async def sendAPITelegram(self, 
                              client_key: str,
                              telegram: APITelegram, 
                              limiter: sans.TelegramLimiter,
                              retry: bool = False) -> str | None:
        try:
            logger.debug(f"preparing API telegram with ID {telegram.tgid} for target '{telegram.targetId}'")

            response = await self.client.get(
                sans.Telegram(
                    client=client_key, 
                    tgid=telegram.tgid, 
                    key=telegram.key, 
                    to=telegram.targetId), 
                auth=limiter)
            
            return response.content.rstrip().decode('utf-8')
        except httpx.ReadTimeout:
            logger.warning(f"response for sendAPITelegram({telegram.tgid}) timed out")

    async def fetchRMBPosts(self, regionId: str, fromid: int, limit: int) -> list[Message]:
        while True:
            try:
                response = await self.client.get(sans.Region(regionId, 
                                                            "messages", 
                                                            limit=str(limit), 
                                                            fromid=str(fromid)))

                messages = []
                        
                for post in response.xml.findall("./MESSAGES/POST"):
                    id = int(post.attrib["id"])
                    timestamp = int(post.find("./TIMESTAMP").text)
                    nation = post.find("./NATION").text
                    status = int(post.find("./STATUS").text)

                    message = Message(id, timestamp, nation, status, None, None)

                    if status != RMB_MOD_SUPPRESSED and status != RMB_SELF_DELETED:
                        message.content = post.find("./MESSAGE").text

                    if status == RMB_SUPPRESSED:
                        message.suppressor = post.find("./SUPPRESSOR").text

                    messages.append(message)

                return messages
            except httpx.ReadTimeout:
                logger.warning(f"response for fetchRMBPosts({regionId}) timed out, retrying in 10 seconds")
                await asyncio.sleep(10)

    def serverSentEvents(self, *args):
        return sans.serversent_events(self.client, *args)