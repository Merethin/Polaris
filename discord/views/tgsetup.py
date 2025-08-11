import discord, re, logging

from models.recruit import TemplateModel, UserTemplateModel, APITemplateModel

logger = logging.getLogger("tgsetup")

class TemplateSetupForm(discord.ui.Modal):
    code = discord.ui.TextInput(label="Template Code", placeholder="%TEMPLATE-XXXXXX%", required=True)

    def __init__(self, view):
        self.view = view
        super().__init__(title="Set Template Code")

    async def on_submit(self, interaction: discord.Interaction):
        match = re.match(r"%TEMPLATE\-([0-9]+)%", self.code.value)
        if match is not None:
            tgid = int(match.groups()[0])
            await interaction.response.defer()
            await self.view.updateTemplate(tgid)
        else:
            await interaction.response.send_message("Template code is invalid! Try again.", ephemeral=True)

class TemplateSetupView(discord.ui.View):
    def __init__(self,
                 userAgent: str,
                 region: str,
                 nationId: str,
                 templates: list[TemplateModel]):
        self.userAgent = userAgent
        self.region = region
        self.nationId = nationId
        self.templates = templates
        self.index = 0
        super().__init__(timeout=300)

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

    def getManualEmbed(self):
        template = self.templates[self.index]

        embed = discord.Embed(title=f"Create Template: {template.id}",
        description=f"Log in to the nation you will be using to send recruitment telegrams. Make sure it is in the region **{self.region}**!\n\n"
        f"Open [the Compose Telegram page](https://www.nationstates.net/container={self.nationId}/nation={self.nationId}/page=compose_telegram?tgto=tag:template&generated_by=Polaris__by_Merethin__usedBy_{self.userAgent})"
        ", and paste the following template into the telegram box:\n"
        f"```\n{template.content}\n```\n"
        f"In the dropdown, **make sure to check the \"This is a recruitment telegram for `{self.region}`\" box!**\n\n"
        "Once that's done, press \"Send\".\n"
        "NationStates will give you a code that looks like this: `%TEMPLATE-XXXXXX%`.\n"
        "Copy that code, click the \"Set Template Code\" button below, and paste it in.",
        colour=0x00b0f4)

        embed.set_author(name=f"Template Setup - {self.index+1}/{len(self.templates)}")

        return embed

    def getFinishedEmbed(self):
        embed = discord.Embed(description="Congratulations, you have set up all templates!\n\nNow all that's left is to start recruiting!",
                      colour=0x57e389)

        embed.set_author(name="Template Setup Finished")

        return embed
    
    def getNoTemplatesEmbed(self):
        embed = discord.Embed(description="This server's admins have not created any templates yet!\n\nCome back when that's done.",
                      colour=0xe01b24)

        embed.set_author(name="No Templates to Set Up")

        return embed

    async def updateTemplate(self, tgid: int):
        template = self.templates[self.index]

        print(f"Template {self.index} ({template.id}) set to %TEMPLATE-{tgid}%")

        query = (UserTemplateModel.id == template.id) & (UserTemplateModel.user == self.user.id)
        userTemplates = UserTemplateModel.find(query).all()

        if len(userTemplates) == 0:
            UserTemplateModel(
                id=template.id,
                user=self.user.id,
                tgid=str(tgid)
            ).save()
        else:
            userTemplates[0].tgid = str(tgid)
            userTemplates[0].save()

        self.index += 1

        if self.index >= len(self.templates):
            await self.message.edit(embed=self.getFinishedEmbed(), view=None)
        else:
            await self.message.edit(embed=self.getManualEmbed(), view=self)

    @discord.ui.button(label="Set Template Code", style=discord.ButtonStyle.blurple)
    async def setCode(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await interaction.response.send_modal(TemplateSetupForm(self))

    async def send(self, interaction: discord.Interaction):
        if self.index >= len(self.templates):
            await interaction.response.send_message(embed=self.getNoTemplatesEmbed())
        else:
            await interaction.response.send_message(embed=self.getManualEmbed(), view=self)

        self.message = await interaction.original_response()
        self.user = interaction.user

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)