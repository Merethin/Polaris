import discord
from models.wastats import WaStats

def getWaStatsEmbed(region: str, stats: WaStats):
    return discord.Embed(
        color=5814783,
        title=f"WA Statistics for {region}",
    ).add_field(
        name="WA Nations",
        value=f"`{stats.waCount}`",
        inline=True,
    ).add_field(
        name="Delegate Endorsements",
        value=f"`{stats.delEndos}`",
        inline=True,
    ).add_field(
        name="Delegate Endorsement Ratio",
        value=f"{stats.delegateRatio():.0%}",
        inline=False,
    ).add_field(
        name="Total Endorsements",
        value=f"`{stats.potentialEndos}`",
        inline=True,
    ).add_field(
        name="Endorsements Given",
        value=f"`{stats.endosGiven}`",
        inline=True,
    ).add_field(
        name="Regional Endorsement Ratio",
        value=f"{stats.regionRatio():.0%}",
        inline=False,
    )