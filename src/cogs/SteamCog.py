# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""TODO ..."""
from typing import Final, Any
from discord.ext import commands
import apis.steamAPI

from BotUtils import BotUtils, Emotes, Emote
from cogs.CogTemplate import CustomCog

class SteamCog(CustomCog):
    """TODO"""

    def __init__(self, bot: commands.Bot, botUtils: BotUtils):
        super().__init__('SteamCog', [
            ['decide',      Emotes.STEAM.value.emote],
            ['steam `id`',  Emotes.STEAM_BLACK.value.emote],
        ])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_UTILS: Final[BotUtils] = botUtils

    @commands.command(name='game', pass_context=True)
    async def decideGame(self, context: Any):
        """TODO"""

        # get users in vc
        activeUsers: list[str] = []
        if (context.author.voice is None):
            # user is not in a voice channel
            activeUsers = [str(context.author.id)]
        else:
            vc = context.author.voice.channel
            for user in vc.members:
                activeUsers.append(str(user.id))

        # get steam ids of users
        steamIds: list[str] = []
        for user in activeUsers:
            # if no steam ID found (TODO)
            await context.channel.send(f"Sorry, I couldn't find a valid Steam ID for <@{user}>.\nPlease use `!steam <your_steam_id>` to resolve this.")
            return
