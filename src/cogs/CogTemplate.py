"""TODO ..."""
from typing import Final, Sequence
from discord.ext import commands

from src.logger import Logger

class CustomCog(commands.Cog):
    """TODO"""

    def __init__(self, name: str, logger: Logger, helpList: list[dict[str, str | Sequence[str]]] | None = None):
        self.COG_NAME: Final[str] = name
        self.HELP_LIST: list[dict[str, str | Sequence[str]]] = helpList if (helpList) else []

        self.setupDatabase()

        logger.info(f'COG {self.COG_NAME} loaded')

    def getHelpList(self):
        """TODO"""

        return self.HELP_LIST

    def setupDatabase(self):
        """TODO"""

        return
