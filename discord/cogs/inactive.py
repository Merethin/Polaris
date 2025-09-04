import discord, time, dateparser, io
from discord.ext import commands
from discord import app_commands
from datetime import timezone, date

from cogs.cache import CacheManager

from views.cache import getCacheIncompleteEmbed
from views.pagination import Pagination

SECONDS_IN_A_DAY = 86400

class InactiveNationsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache: CacheManager = self.bot.get_cog('CacheManager')

    @app_commands.command(description="Display WA nations that haven't logged in after some time.")
    async def inactive(self, interaction: discord.Interaction, days: int):
        if not self.cache.firstCacheComplete():
            await interaction.response.send_message(embed=getCacheIncompleteEmbed())
            return
        
        inactiveNations = []
        for nationId in self.cache.regionWaNations():
            if not self.cache.isNationCached(nationId): # should not happen, in theory
                await self.cache.fetchNation(nationId)

            nation = self.cache.nation(nationId)
            daysSinceLastLogin = (time.time() - nation.lastLogin) // SECONDS_IN_A_DAY

            if daysSinceLastLogin >= days:
                inactiveNations.append((nation.id, daysSinceLastLogin, nation.lastLogin, nation.lastApiUpdateTime))
        
        inactiveNations.sort(key=lambda a: a[1], reverse=True)

        ELEMENTS_PER_PAGE = 10

        async def get_page(page: int):
            emb = discord.Embed(title="Inactive World Assembly Nations", description="")
            offset = (page-1) * ELEMENTS_PER_PAGE
            for nation in inactiveNations[offset:offset+ELEMENTS_PER_PAGE]:
                emb.description += f"[{self.cache.lookupNationName(nation[0])}](https://www.nationstates.net/nation={nation[0]}) - last logged in <t:{nation[2]}:R> (last updated <t:{int(nation[3])}:R>)\n"
            n = Pagination.compute_total_pages(len(inactiveNations), ELEMENTS_PER_PAGE)
            emb.set_footer(text=f"Page {page} of {n}")
            return emb, n
        
        await Pagination(interaction, get_page).navigate()