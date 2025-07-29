import discord

def getCacheIncompleteEmbed() -> discord.Embed:
    return discord.Embed(
        color=5814783,
        title="Startup Incomplete",
        description="Sorry, the bot is starting up and gathering data! Please try again in a few minutes.",
    )