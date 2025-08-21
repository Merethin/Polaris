import discord
from datetime import datetime
from classes import RMBMessage, RMB_NORMAL_POST, RMB_MOD_SUPPRESSED, RMB_SELF_DELETED, RMB_SUPPRESSED
from cogs.cache import CacheManager
from nscode import parseNsCode
from lib import normalize

class RMBView(discord.ui.View):
    def __init__(self, cache: CacheManager, post: RMBMessage, region: str):
        super().__init__()
        self.cache = cache
        self.region = region
        self.post = post

        self.content = self.parseContent(post)
        url = self.generateRMBLink(post)
        button = discord.ui.Button(label='View RMB Post', style=discord.ButtonStyle.url, url=url)
        self.add_item(button)

    def generateRMBLink(self, post: RMBMessage) -> str:
        return f'https://www.nationstates.net/page=display_region_rmb/region={normalize(self.region)}?postid={post.id}#p{post.id}'
    
    def parseContent(self, post: RMBMessage) -> str | None:
        if post.status == RMB_NORMAL_POST:
            try:
                return parseNsCode(post.content).render().replace("%%regionid%%", normalize(self.region))
            except Exception:
                return None
        elif post.status == RMB_SELF_DELETED:
            return f"**Original message deleted by author**"
        elif post.status == RMB_MOD_SUPPRESSED:
            return f"**Original message suppressed by moderators**"
        else:
            return f"**Original message suppressed by [{self.cache.lookupNationName(post.suppressor)}](https://www.nationstates.net/nation={post.suppressor})**"
        
    async def generateEmbed(self):
        embed = discord.Embed(
            color=5814783,
            title="New RMB Post",
            description=self.content,
            timestamp=datetime.fromtimestamp(self.post.timestamp),
        ).set_footer(
            text=f"Posted by {self.cache.lookupNationName(self.post.nation)}",
        )

        nation = self.cache.nation(self.post.nation)
        if nation:
            if nation.flagDirty: # fetch it again
                await self.cache.fetchNation(nation.id)
                nation = self.cache.nation(nation.id)

            embed.set_thumbnail(nation.flagUrl)
        
        return embed

    async def send(self, channel: discord.TextChannel):
        if not self.content:
            return
        
        embed = await self.generateEmbed()

        view = None
        if self.post.status == RMB_NORMAL_POST:
            view = self

        self.message = await channel.send(
            embed=embed,
            view=view,
        )

    async def update(self, newPost: RMBMessage):
        if newPost.content == self.post.content and newPost.status == self.post.status:
            # No changes, do nothing
            return
        
        self.content = self.parseContent(newPost)
        self.post = newPost

        if not self.content:
            return

        embed = await self.generateEmbed()

        view = None
        if self.post.status == RMB_NORMAL_POST:
            view = self

        await self.message.edit(
            embed=embed,
            view=view,
        )