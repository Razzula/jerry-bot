# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""TODO ..."""
from typing import Final, Any
import json
from discord.ext import commands
from discord import Embed, Color

from apis.steamAPI import SteamAPI, SteamTags

from BotUtils import BotUtils, Emotes, Emote
from DatabaseManager import DatabaseManager
from cogs.CogTemplate import CustomCog

RETRY_EMOJI: Final[str] = '🔁'

class SteamCog(CustomCog):
    """TODO"""

    def __init__(self, bot: commands.Bot, botUtils: BotUtils, dbManager: DatabaseManager, steamAPIKey: str):

        self.DB_MANAGER: Final[DatabaseManager] = dbManager

        super().__init__('SteamCog', [
            { 'aliases': ['game'], 'short': 'game', 'icon': Emotes.STEAM.value.emote, 'description': 'Select a game to play from your Steam library. If you are in a voice channel, it will select a shared game among all active users.' },
            { 'aliases': ['steam'], 'short': 'steam `id`', 'icon': Emotes.STEAM_BLACK.value.emote, 'description': 'Set your Steam ID for API access. Use with no arguments to see your current profile.' },
        ])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_UTILS: Final[BotUtils] = botUtils

        self.STEAM_API: Final[SteamAPI] = SteamAPI(steamAPIKey)

    def setupDatabase(self):
        """TODO"""

        cursor = self.DB_MANAGER.getCursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS steam_ids (
                discord_id VARCHAR(18) PRIMARY KEY,
                steam_id VARCHAR(17),
                username VARCHAR(32)
            )
        ''')
        self.DB_MANAGER.commit()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if (user.id == self.BOT.user.id): # ignore self
            return
        
        if (reaction.emoji == RETRY_EMOJI):
            # get embed data
            embedData = self.DB_MANAGER.getFromCache(self.COG_NAME, 'activeEmbeds', str(reaction.message.id))
            if (embedData is not None):
                # get new game
                embedData = embedData[0]

                votePercentage = (reaction.count - 1) / len(embedData['players'])
                if (votePercentage >= 0.5):

                    gameEmbed = self.getGameEmbed(embedData['library'], multiplayer=(len(embedData['players']) > 1))

                    await reaction.message.clear_reactions()
                    await reaction.message.edit(embed=gameEmbed)
                    await reaction.message.add_reaction(RETRY_EMOJI)

    @commands.command(name='game', pass_context=True)
    async def decideGame(self, context: Any, _message: str | None = None):
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
        discordIDList = self.DB_MANAGER.arrayToSqlInArgument(activeUsers)

        # attempt to use cache
        cachedRes = self.DB_MANAGER.getFromCache(self.COG_NAME, 'idlist', discordIDList)
        if (cachedRes is not None):
            # use cached data
            sharedGameLibrary = cachedRes
        else:
            # fetch data from db
            res = self.DB_MANAGER.executeOneshot(f'SELECT discord_id, steam_id FROM steam_ids WHERE discord_id IN {discordIDList}')

            if (len(res) < len(activeUsers)):
                # not all users have a steam id
                await context.channel.send(f"Sorry, I couldn't find a valid Steam ID for <@???>.\nPlease use `!steam <your_steam_id>` to resolve this.")
                return

            # get shared game library
            sharedGameLibrary, invalidUsers = self.STEAM_API.getSharedLibrary(res) # TODO: handle invalidUsers

            # cache result
            # TODO: handle errors first (do not cache if error)
            self.DB_MANAGER.storeInCache(self.COG_NAME, 'idlist', discordIDList, sharedGameLibrary)

        # select game
        if (sharedGameLibrary == [None]): # TODO: handle this properly
            await context.channel.send("No valid Steam users found. Use `!steam <your_steam_id>` to resolve this.")

        elif (not sharedGameLibrary): # TODO: handle this properly
            await context.channel.send("No shared games found.")

        else:
            gameEmbed = self.getGameEmbed(
                sharedGameLibrary, multiplayer=(len(activeUsers) > 1) # game must be multi-player if multiple users
            )
            res = await context.channel.send(embed=gameEmbed)
            
            # handle voting
            if (res is not None):
                await res.add_reaction(RETRY_EMOJI)
            self.DB_MANAGER.storeInCache(self.COG_NAME, 'activeEmbeds', str(res.id), {
                'library': sharedGameLibrary,
                'players': activeUsers,
            }, timeUntilExpire=600) # 10 minutes

    def getGameEmbed(self, gamesList: list[Any], multiplayer: bool) -> Embed:
        """TODO"""
        # select game
        selectedGame = self.STEAM_API.selectGame(gamesList, requireMultiplayer=multiplayer)

        # generate embed
        embed = Embed(
            title=selectedGame.get('name'),
            color=Color.dark_blue(),
            description=selectedGame.get('description'),
        )
        embed.url = f'https://store.steampowered.com/app/{selectedGame["id"]}'
        embed.set_thumbnail(url=selectedGame['thumbnail'])

        categories = selectedGame['categories']

        # Multiplayer
        if (multiplayer):
            embed.add_field(name='Multiplayer', value='✅')

            # Co-Op
            coopIcon = ''

            if (SteamTags.COOP.value.id in categories):
                for tag in [SteamTags.COOP_ONLINE, SteamTags.COOP_LAN, SteamTags.SHARED_SCREEN]:
                    if (categories.get(tag.value.id)):
                        coopIcon += tag.value.icon
            else:
                coopIcon = '❌'
            embed.add_field(name='Cooperative', value=coopIcon if (coopIcon != '') else '✅')

        # Controller Support
        controllerIcon = None
        for tag in [SteamTags.FULL_CONTROLLER, SteamTags.PARTIAL_CONTROLLER]:
            if (categories.get(tag.value.id)):
                controllerIcon = tag.value.icon
                break
        embed.add_field(name='Controller Support', value=controllerIcon if (controllerIcon is not None) else '❌')

        return embed

    def getUserEmbed(self, steamID: str) -> Embed:
        """TODO"""
        userData = self.STEAM_API.getSteamProfile(steamID)

        embed = Embed(
            title=userData.get('personaname'),
            color=Color.dark_blue(),
            # description=userData.get('realname'),
        )
        embed.url = userData.get('profileurl')
        embed.set_thumbnail(url=userData.get('avatarfull'))

        # CURRENT STATUS
        if (userData.get('personastate') == 1):
            embed.add_field(name='Online', value='🟢')
        else:
            embed.add_field(name='Offline', value='🔴')
        # VISIBILITY
        if (userData.get('communityvisibilitystate') == 3):
            embed.add_field(name='Public', value='👁')
        else:
            embed.add_field(name='Private', value='🔒')


        return embed

    @commands.command(name='steam', pass_context=True)
    async def setSteamID(self, context: Any, arg: str | None = None):
        """TODO"""

        if (arg is None):  # no ID passed

            res = self.DB_MANAGER.executeOneshot(f"SELECT steam_id FROM steam_ids WHERE discord_id = '{context.author.id}'")
            if (res):
                embed = self.getUserEmbed(res[0][0])
                await context.channel.send(embed=embed)
            else:
                await context.channel.send(f'You have not set a Steam ID yet. Use `!steam <your_steam_id>` to resolve this.')

        elif (steamID := self.STEAM_API.isValidUser(arg)):
            self.DB_MANAGER.executeOneshot(f'''
                INSERT INTO steam_ids (discord_id, steam_id, username) VALUES ('{context.author.id}', '{steamID}', '{context.author.name}')
                ON CONFLICT (discord_id) DO UPDATE SET steam_id = '{steamID}'
            ''')

            await context.channel.send(f"Steam ID set to `{steamID}`.")

        else:
            await self.BOT_UTILS.reactWithEmote(context, Emotes.EKKY_DISAPPROVES.value)
            await context.channel.send(f"`{arg}` is not a valid Steam ID.")
