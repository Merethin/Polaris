import discord, os
from discord.ext import commands
from discord import app_commands

from views.version import getVersionEmbed
from views.error import getManageGuildRequiredEmbed

class VersionCog(commands.Cog):
    def __init__(self, bot: commands.Bot, version: str):
        self.bot = bot
        self.versionNumber = version

    @app_commands.command(description="Check bot version information.")
    async def version(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=getManageGuildRequiredEmbed())
            return
        
        branch = os.getenv("GIT_BRANCH")
        commit = os.getenv("GIT_COMMIT")
        
        await interaction.response.send_message(embed=getVersionEmbed(self.versionNumber, branch, commit))