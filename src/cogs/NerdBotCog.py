# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ, import-not-found
"""A Cog for interactions focused around NerdBot: https://github.com/Xomboodle/NerdBot-v2"""
import json
import random
import re
from typing import Final, Any
import os
from discord.ext import commands

from src.BotUtils import BotUtils, Emotes
from src.cogs.CogTemplate import CustomCog
from src.logger import Logger

class NerdBotCog(CustomCog):
    """A Cog for interactions focused around NerdBot: https://github.com/Xomboodle/NerdBot-v2"""

    def __init__(self, bot: commands.Bot, logger: Logger, botUtils: BotUtils, gifs: dict[str, list[str]]):

        self.LOGGER: Final[Logger] = logger

        super().__init__('NerdBotCog', logger, [
        ])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_UTILS: Final[BotUtils] = botUtils

        self.GIFS: Final[dict[str, list[str]]] = gifs

        with open(os.path.join(self.BOT_UTILS.STATIC_DATA_PATH, 'nerdbot.json'), 'r', encoding='utf-8') as file:
            self.NERDBOT_DATA = json.load(file)

        if (self.NERDBOT_DATA is not None):
            # Convert insults to regex patterns
            if (self.NERDBOT_DATA.get('insults') is not None):
                self.INSULTS = [
                    insult.replace("{arg}", r".*").replace("{arg2}", r".*").lower()
                        for insult in self.NERDBOT_DATA['insults']
                ]

    @commands.Cog.listener()
    async def on_message(self, context: Any):
        """Reacts to messages sent to the bot."""

        message: str = context.content.lower()  # removes case sensitivity
        if (context.author == self.BOT.user):
            return

        if (self.isInsultFromBot(message)):
            # extract mentions
            userMentions = self.BOT_UTILS.extractMentionsFromMessage(message).get('users')

            for userID in userMentions:
                if (userID != self.NERDBOT_DATA['nerdbotID']):
                    await self.BOT_UTILS.reactWithEmote(context, Emotes.BONK.value)
                    await self.BOT_UTILS.sendGIF(
                        context.channel,
                        self.GIFS['bonks'] + self.GIFS['shames'] + ['Vengeance', 'KeepYourForkedTongue']
                    )

                    return
                else:
                    # NerdBot insulted itself
                    await self.BOT_UTILS.reactWithEmoteStr(context, '👍🏿')
                    await self.BOT_UTILS.sendGIF(context.channel, 'WeHaveVictory')
                return # only avenge a single user

    def isInsultFromBot(self, message: str) -> bool:
        """Determine if the message is a NerdBot insult."""
        if (self.INSULTS is not None):
            for pattern in self.INSULTS:
                if (re.match(pattern, message)):
                    return True
        return False
