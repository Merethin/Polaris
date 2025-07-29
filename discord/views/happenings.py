import discord, datetime
from lib import normalize

# Nation movement views

class NationJoinView(discord.ui.View):
    def __init__(self, nation: str, source: str, target: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.source = source
        self.target = target
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0x484C70,
            title="Nation Joined",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) joined [{self.target}](https://www.nationstates.net/region={normalize(self.target)}) from [{self.source}](https://www.nationstates.net/region={normalize(self.source)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: move",
        )

        await channel.send(message, embed=embed, view=self)

class WaNationJoinView(discord.ui.View):
    def __init__(self, nation: str, source: str, target: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.source = source
        self.target = target
        self.timestamp = timestamp

        url = f"https://www.nationstates.net/nation={normalize(nation)}#composebutton"
        button = discord.ui.Button(label='Click to Endorse Nation', style=discord.ButtonStyle.url, url=url)
        self.add_item(button)

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0x484C70,
            title="WA Nation Joined",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) joined [{self.target}](https://www.nationstates.net/region={normalize(self.target)}) from [{self.source}](https://www.nationstates.net/region={normalize(self.source)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: move",
        )

        sentMessage = await channel.send(message, embed=embed, view=self)
        await sentMessage.add_reaction("✅")

class NationLeaveView(discord.ui.View):
    def __init__(self, nation: str, source: str, target: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.source = source
        self.target = target
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0x484C70,
            title="Nation Left",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) left [{self.source}](https://www.nationstates.net/region={normalize(self.source)}) for [{self.target}](https://www.nationstates.net/region={normalize(self.target)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: move",
        )

        await channel.send(message, embed=embed, view=self)

class WaNationLeaveView(discord.ui.View):
    def __init__(self, nation: str, source: str, target: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.source = source
        self.target = target
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0x484C70,
            title="WA Nation Left",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) left [{self.source}](https://www.nationstates.net/region={normalize(self.source)}) for [{self.target}](https://www.nationstates.net/region={normalize(self.target)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: move",
        )

        await channel.send(message, embed=embed, view=self)

# Nation creation and destruction views

class WaNationCteView(discord.ui.View):
    def __init__(self, nation: str, region: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.region = region
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0xE0A458,
            title="WA Nation Ceased to Exist",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) vanished from reality in [{self.region}](https://www.nationstates.net/region={normalize(self.region)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: cte",
        )

        await channel.send(message, embed=embed, view=self)

class NationCteView(discord.ui.View):
    def __init__(self, nation: str, region: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.region = region
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0xE0A458,
            title="Nation Ceased to Exist",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) vanished from reality in [{self.region}](https://www.nationstates.net/region={normalize(self.region)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: cte",
        )

        await channel.send(message, embed=embed, view=self)

class NationFoundView(discord.ui.View):
    def __init__(self, nation: str, region: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.region = region
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0x419D78,
            title="Nation Founded",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) was created in [{self.region}](https://www.nationstates.net/region={normalize(self.region)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: founding",
        )

        await channel.send(message, embed=embed, view=self)

class NationRefoundView(discord.ui.View):
    def __init__(self, nation: str, region: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.region = region
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0x419D78,
            title="Nation Refounded",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) was brought back to life in [{self.region}](https://www.nationstates.net/region={normalize(self.region)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: founding",
        )

        await channel.send(message, embed=embed, view=self)

# WA membership views

class WAApplyView(discord.ui.View):
    def __init__(self, nation: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0xCA68C7,
            title="New WA Application",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) applied to join the World Assembly",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: wa",
        )

        await channel.send(message, embed=embed, view=self)

class WAAdmitView(discord.ui.View):
    def __init__(self, nation: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.timestamp = timestamp

        url = f"https://www.nationstates.net/nation={normalize(nation)}#composebutton"
        button = discord.ui.Button(label='Click to Endorse Nation', style=discord.ButtonStyle.url, url=url)
        self.add_item(button)

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0xCA68C7,
            title="New WA Member",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) joined the World Assembly",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: wa",
        )

        sentMessage = await channel.send(message, embed=embed, view=self)
        await sentMessage.add_reaction("✅")

class WAResignView(discord.ui.View):
    def __init__(self, nation: str, timestamp: datetime.datetime):
        super().__init__()
        self.nation = nation
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0xCA68C7,
            title="WA Resignation",
            description=f"[{self.nation}](https://www.nationstates.net/nation={normalize(self.nation)}) left the World Assembly",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: wa",
        )

        await channel.send(message, embed=embed, view=self)

# Endorsement views

class EndorsementView(discord.ui.View):
    def __init__(self, source: str, target: str, timestamp: datetime.datetime):
        super().__init__()
        self.source = source
        self.target = target
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0xCA68C7,
            title="Endorsement Given",
            description=f"[{self.source}](https://www.nationstates.net/nation={normalize(self.source)}) endorsed [{self.target}](https://www.nationstates.net/nation={normalize(self.target)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: endo",
        )

        await channel.send(message, embed=embed, view=self)

class DelegateEndorsementView(discord.ui.View):
    def __init__(self, source: str, target: str, timestamp: datetime.datetime):
        super().__init__()
        self.source = source
        self.target = target
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0xCA68C7,
            title="Delegate Endorsement Given",
            description=f"[{self.source}](https://www.nationstates.net/nation={normalize(self.source)}) endorsed the Delegate [{self.target}](https://www.nationstates.net/nation={normalize(self.target)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: endo",
        )

        await channel.send(message, embed=embed, view=self)

class UnEndorsementView(discord.ui.View):
    def __init__(self, source: str, target: str, timestamp: datetime.datetime):
        super().__init__()
        self.source = source
        self.target = target
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0xCA68C7,
            title="Endorsement Removed",
            description=f"[{self.source}](https://www.nationstates.net/nation={normalize(self.source)}) withdrew its endorsement from [{self.target}](https://www.nationstates.net/nation={normalize(self.target)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: endo",
        )

        await channel.send(message, embed=embed, view=self)

class DelegateUnEndorsementView(discord.ui.View):
    def __init__(self, source: str, target: str, timestamp: datetime.datetime):
        super().__init__()
        self.source = source
        self.target = target
        self.timestamp = timestamp

    async def send(self, channel: discord.TextChannel, message: str | None):
        embed = discord.Embed(
            color=0xCA68C7,
            title="Delegate Endorsement Removed",
            description=f"[{self.source}](https://www.nationstates.net/nation={normalize(self.source)}) withdrew its endorsement from the Delegate [{self.target}](https://www.nationstates.net/nation={normalize(self.target)})",
            timestamp=self.timestamp,
        ).set_footer(
            text="Event Type: endo",
        )

        await channel.send(message, embed=embed, view=self)