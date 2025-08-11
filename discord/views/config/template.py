import discord

from models.recruit import BucketModel, TemplateModel

class CreateTemplateForm(discord.ui.Modal):
    name = discord.ui.TextInput(label="Template Name", placeholder="Must be unique", required=True)
    content = discord.ui.TextInput(label="Template Content", placeholder="Template text that will be given to recruiters", style=discord.TextStyle.long, required=True)

    def __init__(self, parentView: discord.ui.View, bucketKey: str):
        self.parentView = parentView
        self.bucketKey = bucketKey
        super().__init__(title="Create New Template")

    async def on_submit(self, interaction: discord.Interaction):
        id = self.name.value

        bucket = BucketModel.get(self.bucketKey)
            
        if TemplateModel.find(TemplateModel.id == id).count() > 0:
            await interaction.response.send_message("A template with the specified name already exists!", ephemeral=True)
            return

        TemplateModel(
            id=id,
            bucket=bucket.id,
            mode=bucket.mode,
            content=self.content.value
        ).save()

        bucket.templates.append(id)
        bucket.save()

        await self.parentView.disable()
        await interaction.response.send_message("Template added.")

class CreateTemplateView(discord.ui.View):
    def __init__(self):
        super().__init__()

        all_pks = BucketModel.all_pks()
        
        self.bucketSelect = discord.ui.Select(
            placeholder="Select a bucket to add a template to...",
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
            title="Create Template",
            description="To create a template, select the bucket you want to create it for.",
        )
    
    def getNoBucketsEmbed(self):
        return discord.Embed(
            color=15277667,
            title="No Buckets",
            description="You need a bucket to add a template to! Please create a bucket first.",
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
            await interaction.response.send_modal(CreateTemplateForm(self, pk))
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

class EditTemplateForm(discord.ui.Modal):
    content = discord.ui.TextInput(label="Template Content", placeholder="Template text that will be given to recruiters", style=discord.TextStyle.long, required=True)

    def __init__(self, parentView: discord.ui.View, pk: str):
        self.parentView = parentView
        self.pk = pk
        super().__init__(title="Edit Template Content")

    async def on_submit(self, interaction: discord.Interaction):
        template = TemplateModel.get(self.pk)

        template.content = self.content.value
        template.save()

        await self.parentView.update()
        await interaction.response.defer()

class EditTemplateView(discord.ui.View):
    def __init__(self, pk: str):
        super().__init__()
        self.pk = pk

    def getDeleteEmbed(self):
        return discord.Embed(
            color=15277667,
            title="Template Deleted",
            description="Template has been deleted.",
        )
    
    def getEmbed(self):
        model = TemplateModel.get(self.pk)
        if not model:
            return self.getDeleteEmbed()

        embed = discord.Embed(
            color=5814783,
            title=f"Edit Template: {model.id}",
        ).add_field(
            name="Bucket",
            value=model.bucket,
            inline=False,
        ).add_field(
            name="Content",
            value=f"```\n{model.content}\n```",
            inline=False,
        )

        return embed

    async def send(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=self.getEmbed(), view=self)

        self.message = await interaction.original_response()
        self.user = interaction.user

    async def update(self) -> None:
        await self.message.edit(embed=self.getEmbed(), view=self)

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
    
    @discord.ui.button(label="Edit Content", style=discord.ButtonStyle.green)
    async def editContent(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(EditTemplateForm(self, self.pk))

    @discord.ui.button(label="Delete Template", style=discord.ButtonStyle.red)
    async def deleteTemplate(self, interaction: discord.Interaction, button: discord.Button):
        model = TemplateModel.get(self.pk)

        bucket = BucketModel.find(BucketModel.id == model.bucket).first()
        bucket.templates.remove(model.id)
        bucket.save()

        TemplateModel.delete(self.pk)
        await interaction.response.defer()
        await self.message.edit(embed=self.getDeleteEmbed(), view=None)

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

class TemplateSelectorView(discord.ui.View):
    def __init__(self):
        super().__init__()

        all_pks = TemplateModel.all_pks()
        
        self.templateSelect = discord.ui.Select(
            placeholder="Select a template to view/edit...",
            options=[
                discord.SelectOption(
                    label=TemplateModel.get(pk).id,
                    value=pk
                ) for pk in all_pks
            ])
        
        self.templateSelect.callback = self.selectTemplate
        self.add_item(self.templateSelect)

    def getEmbed(self):
        return discord.Embed(
            color=5814783,
            title="Edit Template",
            description="Select a template to view, edit or delete.",
        )
    
    def getNoTemplatesEmbed(self):
        return discord.Embed(
            color=15277667,
            title="No Templates",
            description="There are no templates to edit! Please create a template first.",
        )

    async def send(self, interaction: discord.Interaction) -> None:
        if len(self.templateSelect.options) == 0:
            await interaction.response.send_message(embed=self.getNoTemplatesEmbed(), view=None)
        else:
            await interaction.response.send_message(embed=self.getEmbed(), view=self)

        self.message = await interaction.original_response()
        self.user = interaction.user

    async def selectTemplate(self, interaction: discord.Interaction):
        if self.templateSelect.values:
            pk = self.templateSelect.values[0]

            await self.disable()
            await EditTemplateView(pk).send(interaction)
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