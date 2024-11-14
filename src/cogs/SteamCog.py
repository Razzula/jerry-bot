# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""TODO ..."""
import datetime
import random
from typing import Final, Any
from discord.ext import commands
from discord import Embed, Color, ButtonStyle
from discord.ui import Button, View

from src.apis.steamAPI import SteamAPI, SteamTags

from src.BotUtils import BotUtils, Emotes
from src.DatabaseManager import DatabaseManager
from src.cogs.CogTemplate import CustomCog

from src.logger import Logger

RETRY_EMOJI: Final[str] = '🔁'

class SteamCog(CustomCog):
    """TODO"""

    def __init__(self, bot: commands.Bot, logger: Logger, botUtils: BotUtils, dbManager: DatabaseManager, steamAPIKey: str | None):

        self.DB_MANAGER: Final[DatabaseManager] = dbManager
        self.LOGGER = logger

        super().__init__('SteamCog', logger, [
            { 'aliases': ['game'], 'short': 'game', 'icon': Emotes.STEAM.value.emote, 'description': 'Select a game to play from your Steam library. If you are in a voice channel, it will select a shared game among all active users.' },
            { 'aliases': ['hunt'], 'short': 'hunt', 'icon': '🏹', 'description': 'View the Steam achievements of your currently played game. Request a quarry for honour and valour.' },
            { 'aliases': ['quarry'], 'short': 'quarry', 'icon': '🏆', 'description': 'View your active quarry, and be rewarded if you have achieved it.' },
            { 'aliases': ['steam'], 'short': 'steam `id`', 'icon': Emotes.STEAM_BLACK.value.emote, 'description': 'Set your Steam ID for API access. Use with no arguments to see your current profile.' },
        ])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_UTILS: Final[BotUtils] = botUtils

        if (steamAPIKey is not None):
            self.STEAM_API: Final[SteamAPI] = SteamAPI(steamAPIKey)
        else:
            self.LOGGER.warn('Steam API key not provided. SteamCog will not work.')

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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS steam_quarries (
                discord_id VARCHAR(18) PRIMARY KEY,
                steam_appid VARCHAR(32),
                achievement_id VARCHAR(32),
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

                    gameEmbed = self.getGameEmbed(embedData['library'], reaction.message, multiplayer=(len(embedData['players']) > 1))

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
            await context.channel.send('No valid Steam users found. Use `!steam <your_steam_id>` to resolve this.')

        elif (not sharedGameLibrary): # TODO: handle this properly
            await context.channel.send('No shared games found.')

        else:
            gameEmbed = self.getGameEmbed(
                sharedGameLibrary, context, multiplayer=(len(activeUsers) > 1) # game must be multi-player if multiple users
            )

            res = await context.channel.send(embed=gameEmbed)

            # handle voting
            if (res is not None):
                await res.add_reaction(RETRY_EMOJI)
            self.DB_MANAGER.storeInCache(self.COG_NAME, 'activeEmbeds', str(res.id), {
                'library': sharedGameLibrary,
                'players': activeUsers,
            }, timeUntilExpire=600) # 10 minutes

    def getGameEmbed(self, gamesList: list[Any], context: Any, multiplayer: bool) -> Embed:
        """TODO"""
        # select game
        selectedGame = self.STEAM_API.selectGame(gamesList, requireMultiplayer=multiplayer)

        # generate embed
        embed = Embed(
            title=f'{Emotes.STEAM.value.emote} {selectedGame.get("name")}',
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

            embed.set_footer(text=f'Vote to select a new game with {RETRY_EMOJI}')

        else:
            embed.set_author(name=context.author.display_name, icon_url=context.author.avatar)
            embed.set_footer(text='Go in a voice channel with friends to select a game together.')

        # Controller Support
        controllerIcon = None
        for tag in [SteamTags.FULL_CONTROLLER, SteamTags.PARTIAL_CONTROLLER]:
            if (categories.get(tag.value.id)):
                controllerIcon = tag.value.icon
                break
        embed.add_field(name='Controller Support', value=controllerIcon if (controllerIcon is not None) else '❌')

        return embed

    def getUserEmbed(self, steamID: str, author: any) -> Embed:
        """TODO"""
        userData = self.STEAM_API.getSteamProfile(steamID)

        embed = Embed(
            title=f'{Emotes.STEAM.value.emote} {userData.get("personaname")}',
            color=Color.dark_blue(),
            # description=userData.get('realname'),
        )
        embed.url = userData.get('profileurl')
        embed.set_thumbnail(url=userData.get('avatarfull'))
        embed.set_author(name=author.display_name, icon_url=author.avatar)

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
                embed = self.getUserEmbed(res[0][0], context.author)
                await context.channel.send(embed=embed)
            else:
                await context.channel.send(f'You have not set a Steam ID yet. Use `!steam <your_steam_id>` to resolve this.')

        elif (steamID := self.STEAM_API.isValidUser(arg)):
            self.DB_MANAGER.executeOneshot(f'''
                INSERT INTO steam_ids (discord_id, steam_id, username) VALUES ('{context.author.id}', '{steamID}', '{context.author.name}')
                ON CONFLICT (discord_id) DO UPDATE SET steam_id = '{steamID}'
            ''')

            await context.channel.send(f'Steam ID set to `{steamID}`.')

        else:
            await self.BOT_UTILS.reactWithEmote(context, Emotes.EKKY_DISAPPROVES.value)
            await context.channel.send(f'`{arg}` is not a valid Steam ID.')

    @commands.command(name='hunt', pass_context=True, aliases=['achievement'])
    async def decideAchievement(self, context: Any):
        """TODO"""

        # STEAM API
        # get steam id
        res = self.DB_MANAGER.executeOneshot(f"SELECT steam_id FROM steam_ids WHERE discord_id = '{context.author.id}'")
        if (res is None or len(res) == 0):
            await context.channel.send('You have not set a Steam ID yet. Use `!steam <your_steam_id>` to resolve this.')
            return

        # get current game
        userData = self.STEAM_API.getSteamProfile(res[0][0])
        activity = userData.get('gameid')
        if (activity is None):
            await context.channel.send("You don't seem to be currently playing a game.")
            return

        embed, gameData, missingAchievements = self.getHuntEmbed(res[0][0], activity)
        view = AchievementView(self, gameData, missingAchievements)

        await context.channel.send(embed=embed, view=view)

    def getHuntEmbed(self, steamID: str, activity: str):
        """TODO"""

        # get data
        currentGame = self.STEAM_API.getGame(activity)
        currentGameAchievements = self.STEAM_API.getAchievementStatsOfGame(activity)
        missingAchievements = self.STEAM_API.getMissingAchievements(steamID, activity)

        missingAchievementsSorted = []

        for achievement in currentGameAchievements: # these are sorted in descnding order of commonality
            # sort missing achievements to match the order of the current game's achievements
            for missingAchievement in missingAchievements:
                if (missingAchievement.get('apiname') == achievement.get('name')):
                    missingAchievementsSorted.append({
                        'name': missingAchievement.get('name'),
                        'apiname': achievement.get('name'),
                        'description': missingAchievement.get('description'),
                        'percentage': int(achievement.get('percent')),
                    })
                    break

        numberOfAchievements = currentGame.get('achievements').get('total')
        progressBar = self.BOT_UTILS.getProgressBar(
            numberOfAchievements - len(missingAchievements),
            numberOfAchievements,
            length=10
        )

        # EMBED
        embed = Embed(
            title=f'{Emotes.STEAM.value.emote} {currentGame.get("name")} {progressBar}',
            color=Color.dark_blue(),
            description=f'There are {len(currentGameAchievements)} achievements in this game. You are missing {len(missingAchievements)}. \nHere are some of the most common achievements you are missing: ',
        )
        embed.url = f'https://steamcommunity.com/stats/{currentGame["steam_appid"]}/achievements'
        embed.set_thumbnail(url=currentGame['header_image'])
        # embed.timestamp = context.message.created_at
        # embed.set_author(name=userData.get('personaname'), icon_url=userData.get('avatarfull'), url=userData.get('profileurl'))

        count = 0
        i = 0
        desiredCount = min(3, len(missingAchievementsSorted))

        while (count < desiredCount and i < len(missingAchievementsSorted)):
            achievement = missingAchievementsSorted[i]
            if (achievement['description'] != ''): # ignore secret achievements
                embed.add_field(
                    name=f'🏆 {achievement["name"]} ({achievement["percentage"]}%)',
                    value=achievement['description'],
                    inline=False
                )
                count += 1
            i += 1

        if (count < desiredCount):
            pass # TODO: display secret achievements if needed

        return embed, currentGame, missingAchievementsSorted

    @commands.command(name='quarry', pass_context=True)
    async def quarry(self, context: Any):
        """TODO"""

        res = self.DB_MANAGER.executeOneshot(f'''
            SELECT i.steam_id, q.steam_appid, q.achievement_id, q.date FROM steam_quarries q
            JOIN steam_ids i ON i.discord_id = q.discord_id
            WHERE q.discord_id = '{context.author.id}'
        ''')

        if (len(res) == 0):
            await context.channel.send("You don't currently have a quarry. Use `!hunt` to find one.")

        else:
            gameData = self.STEAM_API.getGame(res[0][1])
            achievements = self.STEAM_API.getPlayerAchievementsForGame(res[0][0], res[0][1])

            quarry = None
            for achievement in achievements:
                if (achievement['apiname'] == res[0][2]):
                    quarry = {
                        'name': achievement['name'],
                        'description': achievement['description'],
                        'steam_appid': gameData['steam_appid'],
                        'header_image': gameData['header_image'],
                        'achieved': achievement['achieved'],
                    }
                    break

            if (quarry is not None):
                embed = self.getQuarryEmbed(quarry, author=context.author, date=res[0][3])

                if (quarry['achieved'] == 1):

                    self.DB_MANAGER.executeOneshot(f'''
                        DELETE FROM steam_quarries WHERE discord_id = '{context.author.id}'
                    ''')

                    await context.channel.send(
                        f'Congratulations, {context.author.mention}! You have achieved your quarry! 🥳',
                        embed=embed
                    )

                else:
                    await context.channel.send(embed=embed)

    def getQuarryEmbed(self, quarry: Any, colour: Color = Color.dark_blue(), author: Any = None, date: Any = None) -> Embed:
        """TODO"""

        embed = Embed(
            title=f'🏆 {quarry["name"]}',
            color=colour,
            description=quarry['description'],
        )
        embed.url = f'https://steamcommunity.com/stats/{quarry["steam_appid"]}/achievements'
        embed.set_thumbnail(url=quarry['header_image'])

        if (author is not None):
            embed.set_author(name=author.display_name, icon_url=author.avatar)

        if (date is not None):
            embed.timestamp = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

        return embed

def createButton(view: View, label: str, style: ButtonStyle, custom_id: str, callback: Any):
    """TODO"""
    button = Button(label=label, style=style, custom_id=custom_id)
    button.callback = callback
    view.add_item(button)

class AchievementView(View):
    """TODO"""

    def __init__(self, parent: SteamCog, gameData: Any, missingAchievements: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.PARENT: Final[SteamCog] = parent

        self.gameData: Final[Any] = gameData
        self.missingAchievements: Final[Any] = missingAchievements

        createButton(self, 'Challenge Me!', ButtonStyle.danger, 'quarry', self.triggerQuarry)
        #createButton('Show More', ButtonStyle.secondary, 'more', self.button_callback)


    async def triggerQuarry(self, interaction):
        """TODO"""

        # check if quarry exists
        res = self.PARENT.DB_MANAGER.executeOneshot(f'''
            SELECT steam_appid, achievement_id FROM steam_quarries WHERE discord_id = '{interaction.user.id}'                                 
        ''')

        if (len(res) != 0):
            await interaction.response.send_message('You already have an active quarry. Use `!quarry` to view it.', ephemeral=True)

        else:
            # TODO ensure user owns the game

            view = View()
            createButton(view, 'An easy road', ButtonStyle.success, 'common', self.selectEasyQuarry)
            createButton(view, 'Blood, glory, and honour 🏆', ButtonStyle.danger, 'rare', self.selectHardQuarry)
            createButton(view, 'Whatever you need of me, sire 🎲', ButtonStyle.primary, 'random', self.selectRandomQuarry)

            await interaction.response.send_message('What is is that you seek, brave adventurer?', view=view, ephemeral=True)

    async def selectEasyQuarry(self, interaction):
        """TODO"""
        quarry = None
        for achievement in self.missingAchievements:
            if (achievement['description'] != ''): # ignore secret achievements
                quarry = achievement
                break

        await self.selectQuarry(interaction, quarry, Color.green())

    async def selectHardQuarry(self, interaction):
        """TODO"""
        quarry = None
        for achievement in reversed(self.missingAchievements):
            if (achievement['description'] != ''): # ignore secret achievements
                quarry = achievement
                break

        await self.selectQuarry(interaction, quarry, Color.red())

    async def selectRandomQuarry(self, interaction):
        """TODO"""
        await self.selectQuarry(interaction, random.choice(self.missingAchievements), Color.blurple())

    async def selectQuarry(self, interaction, quarry: Any, colour: Color = Color.dark_blue()):
        """TODO"""

        quarry['steam_appid'] = self.gameData['steam_appid']
        quarry['header_image'] = self.gameData['header_image']

        await interaction.response.edit_message(view=None)
        await interaction.followup.send(
            f'I, {self.PARENT.BOT.user.name}, have heard your plea, and I, therefore, with the powers vested in me herby present upon you, {interaction.user.mention}, this challenge. Will you accept and pursue it in valour?',
            embed=self.PARENT.getQuarryEmbed(quarry, colour, interaction.user),
            view=QuarryView(self.PARENT, quarry, interaction),
        )

class QuarryView(View):

    def __init__(self, parent: SteamCog, quarry: Any, proposalMessage: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.PARENT: Final[SteamCog] = parent

        self.quarry: Final[Any] = quarry
        self.proposalMessage: Final[Any] = proposalMessage

        createButton(self, 'I accept', ButtonStyle.success, 'accept', self.acceptQuarry)
        createButton(self, 'I am a coward', ButtonStyle.danger, 'decline', self.declineQuarry)

    async def acceptQuarry(self, interaction):
        """TODO"""

        # ensure user is the one who requested the quarry
        if (interaction.user.id != self.proposalMessage.user.id):
            await interaction.response.send_message('I admire your selflessness to aid your companion in this quest. But only they can accept the quarry.', ephemeral=True)
            return

        # check if quarry exists
        res = self.PARENT.DB_MANAGER.executeOneshot(f'''
            SELECT steam_appid, achievement_id FROM steam_quarries WHERE discord_id = '{interaction.user.id}'
        ''')

        if (len(res) != 0):
            await interaction.response.send_message('You already have an active quarry. Use `!quarry` to view it.', ephemeral=True)
            return

        # add quarry to db
        self.PARENT.DB_MANAGER.executeOneshot(f'''
            INSERT INTO steam_quarries (discord_id, steam_appid, achievement_id)
            VALUES ('{interaction.user.id}', '{self.quarry["steam_appid"]}', '{self.quarry["apiname"]}')
        ''')

        await interaction.response.edit_message(view=None)
        await interaction.followup.send('Your quarry has been set. May the odds be ever in your favour.')

    async def declineQuarry(self, interaction):
        """TODO"""

        # ensure user is the one who requested the quarry
        if (interaction.user.id != self.proposalMessage.user.id):
            await interaction.response.send_message('Hmm. Well, it is interesting to know that you are a coward. But fear not, friend, for this quarry has not been assigned to you.', ephemeral=True)
        else:
            # await self.proposalMessage.message.edit(
            #     embed=self.PARENT.getQuarryEmbed(self.quarry, Color.dark_grey())
            # )
            await interaction.response.edit_message(view=None)
            await interaction.followup.send('A shame...')
