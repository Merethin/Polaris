import discord

def getNonResidentEmbed(nation: str, region: str):
    return discord.Embed(
        color=15277667,
        description=f"**{nation}** is not a resident nation in **{region}**.",
    )

def getNonWaEmbed(nation: str, region: str):
    return discord.Embed(
        color=15277667,
        description=f"**{nation}** is a resident of **{region}**, but isn't in the World Assembly!\n\nHead over to the [World Assembly page](https://www.nationstates.net/page=un) to join first. **Remember that you can only have one nation in the World Assembly at a time.**",
    )

def getNoBotOwnerEmbed():
    return discord.Embed(
        color=15277667,
        title="Not Enough Permissions",
        description="Sorry, this command can only be used by the bot owner.",
    )

def getManageGuildRequiredEmbed():
    return discord.Embed(
        color=15277667,
        title="Not Enough Permissions",
        description="Sorry, this command can only be used by members with the **Manage Server** permission.",
    )

def getNoRecruitmentEmbed():
    return discord.Embed(
        color=15277667,
        title="Not Enough Permissions",
        description="Sorry, this command can only be used by members with a role that allows recruiting.",
    )