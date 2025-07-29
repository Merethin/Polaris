import discord
from lib import normalize
from collections import deque
from discord.ext import commands

from cogs.cache import CacheManager

class TartView(discord.ui.View):
    def __init__(self,
                 parentCog: commands.Cog,
                 cache: CacheManager, 
                 endorserId: str, 
                 nations: deque[tuple[str | None, str]],
                 userAgent: str):
        
        super().__init__()

        self.parentCog = parentCog
        self.cache = cache
        self.endorserId = endorserId
        self.nations = nations
        self.currentNation = None
        self.userAgent = userAgent

        self.button = discord.ui.Button(label='Endorse Nation', style=discord.ButtonStyle.url, url='https://www.nationstates.net')
        self.add_item(self.button)
        self.queryNewNation()

    def queryNewNation(self):
        if not self.nations:
            self.currentNation = None
            return
        
        title, self.currentNation = self.nations.pop()
        url = self.generateUrl(self.currentNation)

        if title:
            self.button.label=f'Endorse {title} {self.cache.lookupNationName(self.currentNation)}'
        else:
            self.button.label=f'Endorse {self.cache.lookupNationName(self.currentNation)}'
            
        self.button.url=url

    def generateUrl(self, nation: str) -> str:
        generatedBy = f"generated_by=Polaris__by_Merethin__ran_by_{self.userAgent}"
        return f"https://www.nationstates.net/nation={normalize(nation)}#composebutton?{generatedBy}"
    
    def getFinishedEmbed(self) -> discord.Embed:
        nationsToEndorse = len(self.cache.regionWaNations()) - 1

        embed = discord.Embed(
            color=1752220,
            title="All Nations Endorsed",
            description=f"Congratulations! **{self.cache.lookupNationName(self.endorserId)}** has endorsed all {nationsToEndorse} World Assembly members to endorse in **{self.cache.mainRegion.name}**. This is cause for celebration!",
        )

        return embed
    
    def getProgressEmbed(self) -> discord.Embed:
        nationsEndorsed = len(self.cache.endorsementsGiven(self.endorserId))
        nationsToEndorse = len(self.cache.regionWaNations()) - 1

        embed = discord.Embed(
            color=10181046,
            title="Endotarting Helper",
            description=f"**{self.cache.lookupNationName(self.endorserId)}** is endorsing **{nationsEndorsed}** of **{nationsToEndorse}** World Assembly nations in **{self.cache.mainRegion.name}**.\n\nClick the link below to bring you to a nation page to endorse. When you endorse that nation, this embed will be updated with a new nation to endorse.",
        )

        return embed
    
    async def editMessage(self) -> None:
        if self.currentNation:
            await self.message.edit(embed=self.getProgressEmbed(), view=self)
        else:
            self.parentCog.removeView(self, self.endorserId)
            await self.message.edit(embed=self.getFinishedEmbed(), view=None)

    async def send(self, interaction: discord.Interaction) -> None:
        if self.currentNation:
            await interaction.response.send_message(embed=self.getProgressEmbed(), view=self)
        else:
            self.parentCog.removeView(self, self.endorserId)
            await interaction.response.send_message(embed=self.getFinishedEmbed())

        self.message = await interaction.original_response()

    async def on_timeout(self) -> None:
        self.parentCog.removeView(self, self.endorserId)
        await self.message.edit(view=None)