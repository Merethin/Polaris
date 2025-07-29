import discord
from models.wastats import WaStats

class WaStatsView(discord.ui.View):
    def __init__(self, region: str, stats: WaStats):
        super().__init__()
        self.region = region
        self.stats = stats

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
                color=5814783,
                title=f"WA Statistics for {self.region}",
            ).add_field(
                name="WA Nations",
                value=f"`{self.stats.waCount}`",
                inline=True,
            ).add_field(
                name="Delegate Endorsements",
                value=f"`{self.stats.delEndos}`",
                inline=True,
            ).add_field(
                name="Delegate Endorsement Ratio",
                value=f"{self.stats.delegateRatio():.0%}",
                inline=False,
            ).add_field(
                name="Total Endorsements",
                value=f"`{self.stats.potentialEndos}`",
                inline=True,
            ).add_field(
                name="Endorsements Given",
                value=f"`{self.stats.endosGiven}`",
                inline=True,
            ).add_field(
                name="Regional Endorsement Ratio",
                value=f"{self.stats.regionRatio():.0%}",
                inline=False,
            )

        await channel.send(message, embed=embed, view=self)