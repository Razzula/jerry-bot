# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""TODO ..."""
from typing import Final, Any
from discord.ext import commands
from discord import Embed, Color

from apis.steamAPI import SteamAPI

from BotUtils import BotUtils, Emotes, Emote
from DatabaseHandler import DatabaseHandler
from cogs.CogTemplate import CustomCog

class SteamCog(CustomCog):
    """TODO"""

    def __init__(self, bot: commands.Bot, botUtils: BotUtils, dbHandler: DatabaseHandler, steamAPIKey: str):
        super().__init__('SteamCog', [
            ['game',      Emotes.STEAM.value.emote],
            ['steam `id`',  Emotes.STEAM_BLACK.value.emote],
        ])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_UTILS: Final[BotUtils] = botUtils

        self.STEAM_API: Final[SteamAPI] = SteamAPI(steamAPIKey)

        self.DB_HANDLER: Final[DatabaseHandler] = dbHandler
        self.setupDatabase()

    def setupDatabase(self):
        """TODO"""

        cursor = self.DB_HANDLER.getCursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS steam_ids (
                discord_id VARCHAR(18) PRIMARY KEY,
                steam_id VARCHAR(17)
            )
        ''')
        self.DB_HANDLER.commit()

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
        temp = self.DB_HANDLER.arrayToSqlInArgument(activeUsers)
        res = self.DB_HANDLER.executeOneshot(f'SELECT discord_id, steam_id FROM steam_ids WHERE discord_id IN {temp}')

        if (len(res) < len(activeUsers)):
            # not all users have a steam id
            await context.channel.send(f"Sorry, I couldn't find a valid Steam ID for <@???>.\nPlease use `!steam <your_steam_id>` to resolve this.")
            return

        # get shared game library
        # TODO caching
        sharedGameLibrary, invalidUsers = self.STEAM_API.getSharedLibrary(res) # TODO: handle invalidUsers

        # select game
        if (sharedGameLibrary == [None]): # TODO: handle this properly
            await context.channel.send("No valid Steam users found. Use `!steam <your_steam_id>` to resolve this.")

        elif (not sharedGameLibrary): # TODO: handle this properly
            await context.channel.send("No shared games found.")

        else:
            gameEmbed = self.getGameEmbed(
                sharedGameLibrary, multiplayer=(len(res) > 1) # game must be multi-player if multiple users
            )
            await context.channel.send(embed=gameEmbed)
            # TODO: handle voting

    def getGameEmbed(self, gamesList: list[Any], multiplayer: bool) -> Embed:
        """TODO"""
        # select game
        selectedGame = self.STEAM_API.selectGame(gamesList, requireMultiplayer=multiplayer)

        # generate embed
        embed = Embed(
            title=selectedGame.get('name'),
            color=Color.dark_blue(),
            description=selectedGame.get('short_description'),
        )
        embed.url = f'https://store.steampowered.com/app/{selectedGame["steam_appid"]}'
        embed.set_thumbnail(url=selectedGame['header_image'])

        if (multiplayer):
            embed.add_field(name='Multiplayer ✅', value='')
            embed.add_field(name='Cooperative ❓', value='') # TODO
        embed.add_field(name='Controller Support ❓', value='') # TODO

        return embed
