import discord
from discord.ext import commands

from models.config import ConfigModel

class RMBConfigView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

        self.channelSelect = discord.ui.ChannelSelect(
            placeholder="Select a channel for the RMB feed",
            channel_types=[
                discord.ChannelType.text
            ],
            row=0
        )
        self.channelSelect.callback = self.onSelect
        self.add_item(self.channelSelect)

    def queryChannel(self, config: ConfigModel) -> discord.TextChannel | None:
        if not config.rmbChannel:
            return "**Disabled**"
        
        channel = self.bot.get_channel(config.rmbChannel)

        return channel.mention

    def getEmbed(self):
        config = ConfigModel.load()

        return discord.Embed(
            color=15844367,
            title="RMB Settings",
            description=f"Currently posting RMB messages in: {self.queryChannel(config)}",
        )
    
    async def editMessage(self) -> None:
        await self.message.edit(embed=self.getEmbed(), view=self)

    async def send(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=self.getEmbed(), view=self)
        self.message = await interaction.original_response()
        self.user = interaction.user

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

    async def onSelect(self, interaction: discord.Interaction):
        await interaction.response.defer()
    
    @discord.ui.button(label="Update Channel", style=discord.ButtonStyle.green, row=1)
    async def update(self, interaction: discord.Interaction, button: discord.Button):
        if not self.channelSelect.values:
            await interaction.response.send_message(
                "Please select a channel! If you want to disable the RMB feed, click 'Disable RMB Feed' instead.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()

        config = ConfigModel.load()
        config.rmbChannel = self.channelSelect.values[0].id
        config.save()

        await self.editMessage()

    @discord.ui.button(label="Disable RMB Feed", style=discord.ButtonStyle.red, row=1)
    async def disable(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()

        config = ConfigModel.load()
        config.rmbChannel = None
        config.save()

        await self.editMessage()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.user:
            return True
        else:
            emb = discord.Embed(
                description=f"Only the author of the command can perform this action.",
                color=16711680
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False