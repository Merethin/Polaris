import discord
from datetime import datetime

class RecruiterView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, userAgent: str, template: str, nations: list[str], senderId: str):
        super().__init__()
        self.user = user
        self.nations = nations
        self.userAgent = userAgent

        url = self.generateTelegramLink(template, nations, senderId)
        button = discord.ui.Button(label='Click to Send TG', style=discord.ButtonStyle.url, url=url)
        self.add_item(button)

    def generateTelegramLink(self, template: str, nations: list[str], senderId: str) -> str:
        containerLink = f"container={senderId}/nation={senderId}"
        searchParams = f"tgto={",".join(nations)}&message=%TEMPLATE-{template}%"
        generatedBy = f"generated_by=Polaris__by_Merethin__ran_by_{self.userAgent}"
        return f'https://www.nationstates.net/{containerLink}/page=compose_telegram?{searchParams}&{generatedBy}'

    async def send(self, channel: discord.TextChannel) -> discord.Message:
        embed = discord.Embed(title="New Nations to Recruit",
                      description=f"{len(self.nations)} nations are ready to telegram!",
                      colour=0xf8e45c,
                      timestamp=datetime.now())

        message = await channel.send(
            f"{self.user.mention}",
            embed=embed,
            view=self,
        )

        await message.add_reaction("✅")

        return message