"""TODO ..."""
from typing import Final
from discord.ext import commands

class CustomCog(commands.Cog):
    """TODO"""

    def __init__(self, name: str, helpList: list[list[str]] | None = None):
        self.COG_NAME: Final[str] = name
        self.HELP_LIST: list[list[str]] = helpList if (helpList) else []

        self.setupDatabase()

        print(f'COG: {self.COG_NAME} loaded')

    def getHelpList(self):
        """TODO"""

        return self.HELP_LIST

    def setupDatabase(self):
        """TODO"""

        return
