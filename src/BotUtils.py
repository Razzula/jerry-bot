# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""TODO"""
from enum import Enum
import os
import random
from datetime import datetime
from dateutil.easter import easter
import re
from typing import Final, Any
import discord
from discord.ext import commands

from src.DatabaseManager import DatabaseManager
from src.logger import Logger

class Emote:
    """TODO ..."""

    def __init__(self, name: str, emote: str, triggers: list[str] | None = None, fallback: str | None = None):
        self.name = name
        self.emote = emote
        self.triggers = triggers if (triggers is not None) else []
        self.fallback = fallback if (fallback is not None) else None

class Emotes(Enum):
    """Enum of custom emotes"""

    JERRY = Emote('jerry', '❤️', ['jerry', 'jezza', 'good bot', 'attab'])

    # Flags
    AR = Emote('ar-flag', '🇦🇷', ['argent'])
    CA = Emote('ca-flag', '🇨🇦', ['canada', 'canhead'])
    AU = Emote('au-flag', '🇦🇺', ['australia', 'aussie', 'didgeri'])
    NZ = Emote('nz-flag', '🇳🇿', ['zealand', 'kiwi'])
    MT = Emote('mt-flag', '🇲🇹', ['malta', 'malteaser'])

    # Timezones
    GB = Emote('gb-flag', '🇬🇧', ['gmt', 'bst', 'utc'])
    CH = Emote('ch-flag', '🇨🇭', ['cet', 'cest'])

    # Custom Emotes
    ALLIANCE = Emote('theAlliance', '<:theAlliance:899087916251353118>', ['alliance'], '�')
    DOUBT = Emote('doubt', '<:doubt:1084980452537937940>', ['doubt'], '🇽')
    BEANS = Emote('beans', '<:beans:796047923711836210>', ['beans'], '🫘')
    BONK = Emote('bonk', '<:bonk:798539206901235773>', [], '👎🏿')
    EKKY_DISAPPROVES = Emote('ekky_disapproves', '<:ekkydisapproves:876951860144144454>', [], '👎🏿')
    CARDBOARD = Emote('cardboard', '<:cardboard:1203077387345207448>', ['cardboard'], '📦')

    # Steam
    STEAM = Emote('steam', '<:steam:1042900928048681030>', ['steam'], '�')
    STEAM_BLACK = Emote('steam_black', '<:steam:1044305789554266162>', [], '�')

    # Other
    WINDOWS = Emote('windows', '🪟', [])
    CHEESE = Emote('cheese', '🧀', ['cheese'])

class BotUtils:
    """TODO"""

    def __init__(self, logger, staticDataPath, dynamicDataPath):
        self.STATIC_DATA_PATH: Final[str] = staticDataPath
        self.DYNAMIC_DATA_PATH: Final[str] = dynamicDataPath

        self.LOGGER : Final[Logger] = logger

    def getActivity(self):
        """Determine the bot's activity and profile picture based on the current date."""

        defaultActivity = 'Baba Yetu'
        defaultActivityType = discord.ActivityType.listening

        activity = None

        today = datetime.now()
        if (today.month == 12):  # DECEMBER (CHRISTMAS)
            with open(os.path.join(self.STATIC_DATA_PATH ,'pfp/jerry-festag.png'), 'rb') as image:
                avatar = image.read()

            if (today.day <= 14):  # JINGLE JAM
                activityType = discord.ActivityType.watching
                activity = 'Jingle Jam'
            else:
                activity = random.choice([
                    'Fairytale of New York',
                    'Jingle Bells',
                    'Last Christmas',
                    'Feliz Navidad',
                    'The Little Drummer Boy',
                    'White Christmas',
                    'Mariah Carey',
                ])

        else:
            with open(os.path.join(self.STATIC_DATA_PATH ,'pfp/jerry.png'), 'rb') as image:
                avatar = image.read()

            if (today.month == 2 and today.day == 14):  # VALENTIE'S DAY
                activity = 'Careless Whisper'

            elif (today.month == 3 or today.month == 4):  # (possibly) EASTER
                easterDate = easter(today.year)

                if (today.month == easterDate.month  - 3 and today.day == easterDate.day - 3): # Maundy Thursday
                    activityType = discord.ActivityType.competing
                    activity = "The Last Supper"
                elif (today.month == easterDate.month - 2 and today.day == easterDate.day - 2): # Good Friday
                    activity = 'Too Small a Price'
                elif (today.month == easterDate.month and today.day == easterDate.day): # Easter Sunday
                    activity = "He's Alive"

            if (today.month == 5): # MAY
                if (today.day == 1):  # GLADIATOR RELEASE DATE
                    activityType = discord.ActivityType.competing
                    activity = 'gladitorial combat'
                elif (today.day == 4):  # MAY THE 4TH BE WITH YOU
                    activity = 'Duel of the Fates'

            elif (today.month == 9 and today.day == 5):  # JERRY'S B(OT)IRTHDAY
                activity = 'Happy Birthday'

        if (activity is None):

            if (today.weekday() == 4): # FRIDAY
                activityType = discord.ActivityType.watching
                activity = 'cardboard'
            if (today.weekday() == 6): # SUNDAY
                activity = random.choice([
                    'Amazing Grace',
                    'Blessed Assurance',
                    'Great Is Thy Faithfulness',
                    'How Great Thou Art',
                    'In Christ Alone',
                    'It Is Well With My Soul',
                    'When I Survey the Wondrous Cross',
                    'Your Grace Is Enough',
                    'Your Love Never Fails',
                ])

            else:
                return defaultActivity, defaultActivityType, avatar

        return activity, activityType, avatar

    def extractMentionsFromMessage(self, message: str) -> dict[str, list[str] | bool]:
        """Extracts mentions from a message."""

        return {
            'global': re.search(r'@everyone|@here', message) is not None,
            'users': re.findall(r'<@!?(\d+)>', message),
            'roles': re.findall(r'<@&(\d+)>', message),
        }

    def extractSmallestMentionSubset(self, message: str) -> str | bool:
        """Extracts the smallest subset of mentions from a message."""

        mentions = self.extractMentionsFromMessage(message)
        if (mentions['global']):
            return '@everyone'

        output = []
        for mention in mentions['users']:
            output.append(f'<@{mention}>')
        for mention in mentions['roles']:
            output.append(f'<@&{mention}>')

        if (len(output) > 0):
            return ', '.join(output)
        return False

    def getGIF(self, gifName: str | list[str]):
        """Gets a GIF from the static data folder."""

        if (isinstance(gifName, list)):
            gifName = random.choice(gifName)
        return f'https://raw.githubusercontent.com/Razzula/jerry-bot/main/data/static/gifs/{gifName}.gif'

    async def sendGIF(self, channel: Any, gifName: str | list[str]):
        """Sends a GIF to the current channel."""

        await channel.send(self.getGIF(gifName))

    async def reactWithEmote(self, context: commands.context.Context | discord.message.Message, emote: Emote):
        """Sends an Emote object to the current channel, using the fallback, if needed."""

        try:
            await self.reactWithEmoteStr(context, emote.emote)
        except discord.errors.HTTPException:
            self.LOGGER.error(f'Error: Unknown Emoji: {emote.name} ({emote.emote})')
            if (emote.fallback is not None):
                await self.reactWithEmoteStr(context, emote.fallback)

    async def reactWithEmoteStr(self, context: commands.context.Context | discord.message.Message, emoteString: str):
        """Sends an string emote to the current channel."""

        if (isinstance(context, commands.context.Context)):
            await context.message.add_reaction(emoteString)
        elif (isinstance(context, discord.message.Message)):
            await context.add_reaction(emoteString)

    async def reactWithCustomEmote(self, context: Any, emote: Emote):
        """Reacts to a message with a custom emote."""

        try:
            await context.add_reaction(emote.emote)
        except discord.errors.HTTPException:
            await context.add_reaction(emote.fallback)

    def isUserAdmin(self, user: Any) -> bool:
        """Checks if a user has admin permissions."""

        return user.guild_permissions.administrator

    def getUsersFromMentions(self, mentions: dict[str, list[str] | bool]) -> list[Any]:
        """Gets user objects from a list of mentions."""

        users = []
        for user in mentions['users']:
            users.append(user)

        for role in mentions['roles']:
            # TODO: get users from role
            pass

        return users

    def getProgressBar(self, value: float, maxValue: float, length: int = 20) -> str:
        """Generates an ASCII progress bar."""

        fill: str = '█'
        empty: str = '░'

        percentage = int(value / maxValue * 100)
        progress = int(length * value / maxValue)
        return f'[{fill * progress}{empty * (length - progress)}] {percentage}%'

    def isUserBotAdmin(self, userID: str, dbManager: DatabaseManager) -> bool:
        """Checks if a user is a bot admin."""

        res = dbManager.executeOneshot(f'''
            SELECT * FROM botAdmins
            WHERE discordID = '{userID}'
            LIMIT 1
        ''')

        return (len(res) > 0)

    def getFromComplexList(self, complexList: list[Any], message: str) -> str | None:
        """Gets a list from a complex list."""

        for entry in complexList:
            prompts: list[str] | str = entry.get('input')
            strict = entry.get('strict') if ('strict' in entry) else False

            # single prompt
            if (isinstance(prompts, str)):
                if (prompts in message):
                    return entry.get('output')

            # multiple prompts
            else:
                if (entry.get('type') == 'AND'): # AND
                    flag = True
                    for prompt in prompts:
                        if (not self.isSubstring(message, prompt, strict=strict)):
                            flag = False
                    if (flag):
                        return entry.get('output')
                else: # OR
                    for prompt in prompts:
                        if (self.isSubstring(message, prompt, strict=strict)):
                            return entry.get('output')
        return None

    def isSubstring(self, string: str, substr: str, strict = False) -> bool:
        """Checks if a string is a substring of another string."""

        if (strict):
            return substr == string
        return substr in string
