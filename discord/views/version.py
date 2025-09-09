import discord

def getVersionEmbed(version: str, branch: str, commit: str):
    return discord.Embed(
        color=5814783,
        title="Version Information",
    ).add_field(
        name="Version",
        value=f"Polaris/{version} by Merethin",
        inline=False,
    ).add_field(
        name="Git Branch",
        value=branch,
        inline=True,
    ).add_field(
        name="Git Commit",
        value=commit,
        inline=True,
    )