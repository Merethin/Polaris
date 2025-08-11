import discord
from classes import *
from filters import FilterError

from models.recruit import BucketModel, TemplateModel

class EditFilterForm(discord.ui.Modal):
    filter = discord.ui.TextInput(label="Bucket Filter", placeholder="Matches new nations", required=True)

    def __init__(self, parentView: discord.ui.View, pk: str):
        self.parentView = parentView
        self.pk = pk
        super().__init__(title="Edit Filter")

    async def on_submit(self, interaction: discord.Interaction):
        filter = self.filter.value

        try:
            RecruitFilter().parse(filter)
        except FilterError as e:
            await interaction.response.send_message(f"Error while parsing filter: {e.message}", ephemeral=True)
            return
        
        model = BucketModel.get(self.pk)
        model.filter = filter
        model.save()

        await self.parentView.update()
        await interaction.response.defer()

class EditSizeForm(discord.ui.Modal):
    size = discord.ui.TextInput(label="Bucket Size", placeholder="Max number of nations to hold", required=True)

    def __init__(self, parentView: discord.ui.View, pk: str):
        self.parentView = parentView
        self.pk = pk
        super().__init__(title="Edit Filter")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            size = int(self.size.value)
            if size < 0 or size > 2000:
                await interaction.response.send_message("Bucket Size must be a valid number between 0 and 2000", ephemeral=True)
                return

            model = BucketModel.get(self.pk)
            model.size = size
            model.save()

            await self.parentView.update()
            await interaction.response.defer()
        except ValueError:
            await interaction.response.send_message("Bucket Size must be a valid number between 0 and 2000", ephemeral=True)

MODE_DISPLAY_NAME = {
    MODE_API: "API Only",
    MODE_MANUAL: "Manual Only",
    MODE_BOTH: "API & Manual",
}

PRIORITY_DISPLAY_NAME = {
    0.0: "Normal Priority",
    1.0: "Medium Priority",
    2.0: "High Priority",
    4.0: "Maximum Priority",
}

class EditBucketView(discord.ui.View):
    def __init__(self, pk: str):
        super().__init__()
        self.pk = pk

    def getDeleteEmbed(self):
        return discord.Embed(
            color=15277667,
            title="Bucket Deleted",
            description="Bucket has been deleted.",
        )
    
    def getEmbed(self):
        model = BucketModel.get(self.pk)

        priority = PRIORITY_DISPLAY_NAME.get(model.priority)
        if not priority:
            priority = f"Custom: {model.priority:.2}"

        filter = RecruitFilter().parse(model.filter)

        templateText = "No templates yet."
        if len(model.templates) > 0:
            templateText = ", ".join(model.templates)

        embed = discord.Embed(
            color=5814783,
            title=f"Edit Bucket: {model.id}",
        ).add_field(
            name="Filter",
            value=f"`{model.filter}`\n{filter.explain()}",
            inline=False,
        ).add_field(
            name="Size",
            value=f"Holds up to {model.size} nations",
            inline=False,
        ).add_field(
            name="Mode",
            value=f"{MODE_DISPLAY_NAME[model.mode]}",
            inline=True,
        ).add_field(
            name="Priority",
            value=priority,
            inline=True,
        ).add_field(
            name=f"Templates: {len(model.templates)}",
            value=templateText,
            inline=False,
        )

        return embed

    async def send(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=self.getEmbed(), view=self)
        self.message = await interaction.original_response()
        self.user = interaction.user

    async def update(self) -> None:
        await self.message.edit(embed=self.getEmbed(), view=self)

    @discord.ui.select(placeholder="Select a new mode...",
    options=[
        discord.SelectOption(label="API & Manual", value=str(MODE_BOTH)),
        discord.SelectOption(label="Manual Only", value=str(MODE_MANUAL)),
        discord.SelectOption(label="API Only", value=str(MODE_API)),
    ])
    async def selectMode(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values:
            model = BucketModel.get(self.pk)
            model.mode = int(select.values[0])
            model.save()
            await self.update()

        await interaction.response.defer()

    @discord.ui.select(placeholder="Select a new priority...",
    options=[
        discord.SelectOption(label="Normal Priority", value="0"),
        discord.SelectOption(label="Medium Priority", value="1"),
        discord.SelectOption(label="High Priority", value="2"),
        discord.SelectOption(label="Maximum Priority", value="4"),
    ])
    async def selectPriority(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values:
            model = BucketModel.get(self.pk)
            model.priority = float(select.values[0])
            model.save()
            await self.update()

        await interaction.response.defer()

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
    
    @discord.ui.button(label="Edit Filter", style=discord.ButtonStyle.green)
    async def editFilter(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(EditFilterForm(self, self.pk))

    @discord.ui.button(label="Edit Size", style=discord.ButtonStyle.green)
    async def editSize(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(EditSizeForm(self, self.pk))

    @discord.ui.button(label="Delete Bucket", style=discord.ButtonStyle.red)
    async def deleteBucket(self, interaction: discord.Interaction, button: discord.Button):
        model = BucketModel.get(self.pk)

        templates = TemplateModel.find(TemplateModel.bucket == model.id).all()
        TemplateModel.delete_many(templates)

        BucketModel.delete(self.pk)
        await interaction.response.defer()
        await self.message.edit(embed=self.getDeleteEmbed(), view=None)

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

class CreateBucketForm(discord.ui.Modal):
    name = discord.ui.TextInput(label="Bucket Name", placeholder="Must be unique", required=True)
    filter = discord.ui.TextInput(label="Bucket Filter", placeholder="Matches new nations", required=True)
    size = discord.ui.TextInput(label="Bucket Size", placeholder="Max number of nations to hold", required=True)

    def __init__(self, parentView: discord.ui.View, mode: int, priority: float):
        self.parentView = parentView
        self.mode = mode
        self.priority = priority
        super().__init__(title="Create New Bucket")

    async def on_submit(self, interaction: discord.Interaction):
        id = self.name.value
        filter = self.filter.value

        try:
            RecruitFilter().parse(filter)
        except FilterError as e:
            await interaction.response.send_message(f"Error while parsing filter: {e.message}", ephemeral=True)
            return
        
        try:
            size = int(self.size.value)
            if size < 0 or size > 2000:
                await interaction.response.send_message("Bucket Size must be a valid number between 0 and 2000", ephemeral=True)
                return
            
            if BucketModel.find(BucketModel.id == id).count() > 0:
                await interaction.response.send_message("A bucket with the specified name already exists!", ephemeral=True)
                return

            model = BucketModel(
                id=id,
                filter=filter,
                size=size,
                priority=self.priority,
                mode=self.mode,
                templates=[]
            ).save()

            await self.parentView.disable()
            await EditBucketView(model.pk).send(interaction)
        except ValueError:
            await interaction.response.send_message("Bucket Size must be a valid number between 0 and 2000", ephemeral=True)

class CreateBucketView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.mode = MODE_BOTH
        self.priority = 0

    def getEmbed(self):
        return discord.Embed(
            color=5814783,
            title="Create Bucket",
            description="Select a mode and priority and press 'Create New Bucket' to create a bucket.",
        )

    async def send(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=self.getEmbed(), view=self)
        self.message = await interaction.original_response()
        self.user = interaction.user

    @discord.ui.select(options=[
        discord.SelectOption(label="API & Manual", value=str(MODE_BOTH), default=True),
        discord.SelectOption(label="Manual Only", value=str(MODE_MANUAL)),
        discord.SelectOption(label="API Only", value=str(MODE_API)),
    ])
    async def selectMode(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values:
            self.mode = int(select.values[0])

        await interaction.response.defer()

    @discord.ui.select(options=[
        discord.SelectOption(label="Normal Priority", value="0", default=True),
        discord.SelectOption(label="Medium Priority", value="1"),
        discord.SelectOption(label="High Priority", value="2"),
        discord.SelectOption(label="Maximum Priority", value="4"),
    ])
    async def selectPriority(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values:
            self.priority = float(select.values[0])

        await interaction.response.defer()

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
    
    @discord.ui.button(label="Create New Bucket", style=discord.ButtonStyle.green)
    async def createBucket(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(CreateBucketForm(self, self.mode, self.priority))

    async def disable(self):
        await self.message.edit(view=None)

    async def on_timeout(self) -> None:
        await self.disable()

class BucketSelectorView(discord.ui.View):
    def __init__(self):
        super().__init__()

        all_pks = BucketModel.all_pks()
        
        self.bucketSelect = discord.ui.Select(
            placeholder="Select a bucket to edit...",
            options=[
                discord.SelectOption(
                    label=BucketModel.get(pk).id,
                    value=pk
                ) for pk in all_pks
            ])
        
        self.bucketSelect.callback = self.selectBucket
        self.add_item(self.bucketSelect)

    def getEmbed(self):
        return discord.Embed(
            color=5814783,
            title="Edit Bucket",
            description="Select a bucket to edit or delete.",
        )
    
    def getNoBucketsEmbed(self):
        return discord.Embed(
            color=15277667,
            title="No Buckets",
            description="There are no buckets to edit! Please create a bucket first.",
        )

    async def send(self, interaction: discord.Interaction) -> None:
        if len(self.bucketSelect.options) == 0:
            await interaction.response.send_message(embed=self.getNoBucketsEmbed(), view=None)
        else:
            await interaction.response.send_message(embed=self.getEmbed(), view=self)
        self.message = await interaction.original_response()
        self.user = interaction.user

    async def selectBucket(self, interaction: discord.Interaction):
        if self.bucketSelect.values:
            pk = self.bucketSelect.values[0]
            await self.disable()
            await EditBucketView(pk).send(interaction)
        else:
            await interaction.response.defer()

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

    async def disable(self):
        await self.message.edit(view=None)

    async def on_timeout(self) -> None:
        await self.disable()