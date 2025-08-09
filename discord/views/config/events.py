import discord
from discord.ext import commands

from models.config import ConfigModel
from models.config.events import EventSettingsModel

EVENT_DESCRIPTIONS = {
    "Nation Leaves": "leave",
    "WA Nation Leaves": "waLeave",
    "Nation Joins": "join",
    "WA Nation Joins": "waJoin",
    "Nation Ceases to Exist": "cte",
    "WA Nation Ceases to Exist": "waCte",
    "Nation is Founded": "founded",
    "Nation is Refounded": "refounded",
    "Nation Applies to WA": "apply",
    "Nation Joins WA": "admit",
    "Nation Resigns from WA": "resign",
    "Nation Endorses Delegate": "delEndo",
    "Nation Endorses Other": "endo",
    "Nation Unendorses Delegate": "delUnendo",
    "Nation Unendorses Other": "unendo",
}

class EventConfigView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

        self.eventSelect = discord.ui.Select(
            placeholder="Select an event to edit",
            options=[
                discord.SelectOption(label=key, value=value) for key,value in EVENT_DESCRIPTIONS.items()
            ],
            row=0
        )
        self.eventSelect.callback = self.onSelect

        self.channelSelect = discord.ui.ChannelSelect(
            placeholder="Select a channel to assign to this event",
            channel_types=[
                discord.ChannelType.text
            ],
            row=1
        )
        self.channelSelect.callback = self.onSelect

        self.roleSelect = discord.ui.RoleSelect(
            placeholder="Select a role to ping (leave empty to not ping any)",
            row=2
        )
        self.roleSelect.callback = self.onSelect

        self.add_item(self.eventSelect)
        self.add_item(self.channelSelect)
        self.add_item(self.roleSelect)

    def queryChannel(self, config: ConfigModel, event: str) -> tuple[discord.TextChannel | None, str | None]:
        eventConfig = config.events.get(event)

        if not eventConfig:
            return "**Disabled**"
        
        channel = self.bot.get_channel(eventConfig.channel)

        if eventConfig.role:
            mention = channel.guild.get_role(eventConfig.role).mention
            return f"{channel.mention} (pings {mention})"

        return channel.mention

    def getEmbed(self):
        config = ConfigModel.load()

        return discord.Embed(
            color=15844367,
            title="Event Settings",
            description="\n".join([f"{label}: {self.queryChannel(config, event)}" for label, event in EVENT_DESCRIPTIONS.items()]),
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
    
    @discord.ui.button(label="Edit Event", style=discord.ButtonStyle.green, row=3)
    async def editEvent(self, interaction: discord.Interaction, button: discord.Button):
        if not self.eventSelect.values:
            await interaction.response.send_message(
                "Please select an event!",
                ephemeral=True
            )
            return
        
        if not self.channelSelect.values:
            await interaction.response.send_message(
                "Please select a channel! If you want to disable the event, click 'Disable Event' instead.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        eventConfig = EventSettingsModel(
            channel=self.channelSelect.values[0].id
        )
        if self.roleSelect.values:
            eventConfig.role = self.roleSelect.values[0].id
        
        event = self.eventSelect.values[0]

        config = ConfigModel.load()
        config.events[event] = eventConfig
        config.save()

        self.eventSelect.values.clear()

        await self.editMessage()

    @discord.ui.button(label="Disable Event", style=discord.ButtonStyle.red, row=3)
    async def disableEvent(self, interaction: discord.Interaction, button: discord.Button):
        if not self.eventSelect.values:
            await interaction.response.send_message(
                "Please select an event!",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        event = self.eventSelect.values[0]

        config = ConfigModel.load()
        config.events.pop(event, None)
        config.save()

        self.eventSelect.values.clear()

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