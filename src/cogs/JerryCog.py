# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ, import-not-found
"""Main (not core) cog for the bot."""
import datetime
import random
import re
import time
import asyncio
from typing import Final, Any, Sequence
import discord
from discord.ext import commands

from src.BotUtils import BotUtils, Emotes, Emote
from src.DatabaseManager import DatabaseManager
from src.cogs.CogTemplate import CustomCog
from src.logger import Logger

PERSPECTIVE_CONVERTOR = [ # (first, second, third)
    ('i', 'you', ['they', 'he', 'she']),
    ('my', 'your', ['their', 'his', 'her']),
    ('mine', 'yours', ['theirs', 'his', 'hers']),
    ('me', 'you', ['them', 'him', 'her']),
    ('myself', 'yourself', ['themself', 'himself', 'herself']),
    ("i'm", "you're", ["they're", "he's", "she's"]),
    ("i'll", "you'll", ["they'll", "he'll", "she'll"]),
    ('am', 'are', 'are'),
]

MESSAGE_SEPERATOR = r'\N'

class JerryCog(CustomCog):
    """
    Main (not core) cog for the bot.

    Provides all of the Jerry-isms that we know and love.
    """

    def __init__(self, bot: commands.Bot, logger: Logger, botUtils: BotUtils, dbManager: DatabaseManager, gifs: dict[str, list[str]]):

        self.LOGGER: Final[Logger] = logger
        self.DB_MANAGER: Final[DatabaseManager] = dbManager

        super().__init__('JerryCog', logger, [
            { 'aliases': ['party', 'boogie', 'celebrate', 'whoop'], 'short': 'party', 'icon': '🎉', 'description': 'I like to move it, move it 🦝' },
            { 'aliases': ['hug'], 'short': 'hug', 'icon': '🤗', 'description': 'Sometimes a hug is all you need to make you feel better.' },
            { 'aliases': ['highfive'], 'short': 'highfive', 'icon': '👏', 'description': 'Gimme five. (Don\'t be too slow!)' },
            { 'aliases': ['pick', 'choose', 'select'], 'short': 'pick `a`,`b`,...', 'icon': '❔', 'description': 'Randomly select a choice from a list of options (or does it just return the first one? I can never remember).' },
            { 'aliases': ['roll'], 'short': 'roll `n`', 'icon': '🎲', 'description': 'Roll a d`n` die.' },
            { 'aliases': ['bonk'], 'short': 'bonk `@`', 'icon': Emotes.BONK.value.emote, 'description': 'Punish a user with a bonk, and send them to bonk-jail.' },
            { 'aliases': ['summon'], 'short': 'summon `@`', 'icon': '🎺', 'description': 'Summon a user (to fulfil their oath!)' },
        ])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_UTILS: Final[BotUtils] = botUtils

        self.GIFS: Final[dict[str, list[str]]] = gifs

    def setupDatabase(self):
        """TODO"""

        cursor = self.DB_MANAGER.getCursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                guild_id VARCHAR(32),
                channel_id VARCHAR(32),
                message_id VARCHAR(32),
                message VARCHAR(2000),
                date_time FLOAT
            )
        ''')
        self.DB_MANAGER.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        """Initializes the bot when it is ready."""

        # enqueue all reminders # TODO optimise this to minimise active threads
        data = self.DB_MANAGER.executeOneshot('''
            SELECT message_id FROM reminders
        ''')

        for reminder in data:
            asyncio.create_task(self.queueReminder(reminder[0]))

    @commands.Cog.listener()
    async def on_message(self, context: Any):
        """Reacts to messages sent to the bot."""

        message: str = context.content.lower()  # removes case sensitivity
        if (context.author == self.BOT.user):
            return

        # extract mentions
        userMentions = self.BOT_UTILS.extractMentionsFromMessage(message).get('users')

        # PRESENCE WAITLIST
        for userID in userMentions:

            user = context.guild.get_member(int(userID))
            if (user is None):
                continue

            # enqueue to presence waitlist
            if (user.status.name in ('offline', 'idle')): # only queue if user is not online
                value = {
                    'guild': context.guild.id,
                    'channel': context.channel.id,
                    'message': context.id,
                }

                self.DB_MANAGER.storeInCache(self.COG_NAME, 'presenceWaitlist', userID, value, timeUntilExpire=3600) # 1 hour
                await self.BOT_UTILS.reactWithEmoteStr(context, '👀')

    @commands.Cog.listener()
    async def on_presence_update(self, _userBefore, userAfter):

        if (userAfter.status.name in ['online', 'dnd']): # user has come online
            temp = self.DB_MANAGER.getFromCache(self.COG_NAME, 'presenceWaitlist', str(userAfter.id))

            if (temp is not None): # user has a reminder queued
                for prompt in temp:
                    # TODO ensure this reminder is for the current guild
                    # if the bot and user are in multiple guilds, the bot could react to this oresence change multiple times
                    if (prompt['guild'] == userAfter.guild.id):

                        channel = self.BOT.get_guild(prompt['guild']).get_channel(prompt['channel'])
                        if (channel is not None):

                            message = await channel.fetch_message(prompt['message'])
                            if (message is not None):
                                timeTaken = (datetime.datetime.now(message.created_at.tzinfo) - message.created_at).total_seconds()

                                if (timeTaken < 120): # 2 minutes
                                    gifName = 'HeIsHere'
                                elif (timeTaken > 3600): # 1 hour
                                    gifName = "You'reLate"
                                else:
                                    self.DB_MANAGER.removeFromCache(self.COG_NAME, 'presenceWaitlist', str(userAfter.id))
                                    continue

                                try:
                                    await message.reply(self.BOT_UTILS.getGIF(gifName))
                                except discord.NotFound:
                                    await channel.send(self.BOT_UTILS.getGIF(gifName))

                        self.DB_MANAGER.removeFromCache(self.COG_NAME, 'presenceWaitlist', str(userAfter.id))

    @commands.command(name='party')
    async def dance(self, context: Any, *_args):
        """Sends a random dance GIF."""

        await self.BOT_UTILS.sendGIF(context.channel, random.choice(self.GIFS['dances']))

    @commands.command(name='hug')
    async def hug(self, context: Any, *_args):
        """Sends a random hug GIF."""

        await self.BOT_UTILS.sendGIF(context.channel, random.choice(self.GIFS['hugs']))

    @commands.command(name='pick', pass_context=True, aliases=['choose', 'select'])
    async def pick(self, context: Any, *, arg: str | None) -> None:
        """Picks a random choice from a list of comma-separated choices."""

        if (arg is None):
            await context.channel.send('Is this some kind of trick question..?')
            return

        choices = arg.split(',')
        if (len(choices) == 1):
            await context.channel.send("Hmm.. that's a _really_ tough one.")
            await context.channel.send(choices[0])
        else:
            await context.channel.send(random.choice(choices))

    @commands.command(name='roll', pass_context=True)
    async def roll(self, context: Any, arg: str | None) -> None:
        """Rolls a random number between 1 and the specified number."""

        if (arg is None):
            # if no number is specified, just do a forward roll, hehe
            await self.BOT_UTILS.sendGIF(context.channel, 'PandaRoll')

        else:
            try:
                result = random.randint(1, (int)(arg))
            except ValueError:
                await self.BOT_UTILS.reactWithEmote(context, Emotes.EKKY_DISAPPROVES.value)
                return

            await context.channel.send(result)

    @commands.command(name='bonk', pass_context=True)
    async def bonk(self, context: Any, *args):
        """Bonks a user."""

        if (not self.BOT_UTILS.isUserAdmin(context.author)):

            await self.BOT_UTILS.reactWithCustomEmote(context, Emotes.BONK.value)

            await self.BOT_UTILS.sendGIF(context.channel, 'YouHaveNoPowerHere')
            return

        targets = self.BOT_UTILS.getUsersFromMentions(self.BOT_UTILS.extractMentionsFromMessage(' '.join(args)))
        if (targets):

            # TODO: check bot is authorised

            bonkRole = discord.utils.get(context.guild.roles, name='Bonk Jail') # TODO: dynamic

            toBonk = []
            toUnbonk = []

            if (bonkRole):

                for target in targets:
                    user = context.guild.get_member(int(target))

                    if (bonkRole in user.roles):  # already bonked
                        toUnbonk.append(user)
                    else:
                        toBonk.append(user)

                if (not toBonk): # only unbonk if no new bonks
                    for user in toUnbonk:
                        await user.remove_roles(bonkRole)

                    # inform of unbonk
                    await context.channel.send(', '.join([u.mention for u in toUnbonk]))
                    await self.BOT_UTILS.sendGIF(context.channel, 'IReleaseYou')

                else: # bonk all
                    for user in toBonk:
                        await user.add_roles(bonkRole) # TODO ensure this role is not higher than the bot

                    # message channel
                    await self.BOT_UTILS.sendGIF(context.channel, random.choice(self.GIFS['bonks']))
                    if (random.randint(0, 5) <= 2):
                        await context.channel.send('https://www.youtube.com/watch?v=2D7P1khV40U') # The Lion King 2 Not One Of Us

                    # message bonk jail
                    bonkJail = discord.utils.get(context.guild.channels, name='bonk-jail')
                    if (bonkJail is not None):
                        await bonkJail.send(', '.join([u.mention for u in toBonk]))
                        await self.BOT_UTILS.sendGIF(bonkJail, random.choice(self.GIFS['shames']))
                    else:
                        self.LOGGER.warn('`#bonk-jail` channel does not exist')

            else:
                self.LOGGER.warn('Role `Bonk Jail` does not exist')
                await self.BOT_UTILS.sendGIF(context.channel, random.choice(self.GIFS['bonks']))

        else:  # no user specified
            await self.BOT_UTILS.reactWithEmoteStr(context, '❓')

    @commands.command(name='appear', pass_context=True)
    async def appear(self, context: Any, *args):
        """Comes back to you, at the turn of the tide..."""
        await self.BOT_UTILS.sendGIF(context.channel, 'GandalfReturns')
        await context.message.delete()

    @commands.command(name='summon', pass_context=True)
    async def summon(self, context: Any, *args):
        """Summons a user or role to the current channel."""

        targets = self.BOT_UTILS.extractSmallestMentionSubset(' '.join(args))
        if (targets):

            # TODO: subtle

            content = None
            try:
                content = context.content
            except:
                content = context.message.content

            await self.BOT_UTILS.reactWithEmoteStr(context, '👍🏿')
            await self.enqueueReminder(context, content, [
                targets,
                self.BOT_UTILS.getGIF(random.choice(self.GIFS['summons']))
            ])

        else:  # no user specified
            await self.BOT_UTILS.reactWithEmoteStr(context, '❓')

    async def setReminder(self, context: Any, *args):
        """TODO"""

        trigger = args[0] if (len(args) > 0) else 'remind'

        # get message
        content = context.content.lower() + ' '
        reg = re.search(rf'{trigger} (me|.*?)[ .]', content)

        if (reg is None):
            await context.channel.send(f'{trigger.title()} you of what?')
            return

        target = reg.group(1)
        perspective = 'B'
        if (target in ['me', None]):
            target = context.author.mention
            perspective = 'A'

        reg = re.search(rf'{trigger} (me|.*?) .*?(?:to|that|about|of|if) (.*)', content)
        if (reg is not None):
            temp = reg.group(2).split(' ')

            message = f'{target.capitalize()}, '
            for word in temp:

                def getConjugates(word: str) -> tuple[tuple[Sequence[str], str, Sequence[str]], int] | None:
                    for conjugates in PERSPECTIVE_CONVERTOR:
                        for index, tense in enumerate(conjugates):
                            if (isinstance(tense, list)):
                                if (word.lower() in tense):
                                    return conjugates, index + 1
                            else:
                                if (word.lower() == tense):
                                    return conjugates, index + 1
                    return None

                if (conjugates := getConjugates(word)):

                    match conjugates[1]:
                        case 1:
                            # FIRST
                            # [A] (1) I -> you  (2)
                            # [B] (1) I -> they (3)
                            targetPerspective = 2 if (perspective == 'A') else 3
                        case 2:
                            # SECOND
                            # [A] (2) you -> I (1)
                            # [B] (2) you -> I (1)
                            targetPerspective = 1
                        case 3:
                            # THIRD
                            # [A] (3) them -> them (3)
                            # [B] (3) them -> you (2)
                            targetPerspective = 3 if (perspective == 'A') else 2

                    newWord = conjugates[0][targetPerspective - 1]
                    if (isinstance(newWord, list)):
                        newWord = newWord[0]
                    message += f'{newWord} '

                else:
                    message += f'{word} '
                pass

        else:
            message = f'{target}'

        await self.enqueueReminder(context, content, [message.capitalize()])
        await self.BOT_UTILS.reactWithEmoteStr(context, '👍🏿')

    async def enqueueReminder(self, context: Any, message: str, messages: list[str]):
        """TODO"""

        # calculate delay
        delayToSend = self.extractDelay(message)

        if (delayToSend <= 0.9):
            for index, message in enumerate(messages):
                if (index == 0):
                    await context.reply(message)
                else:
                    await context.channel.send(message)

        else:
            # store to be resumable
            message = MESSAGE_SEPERATOR.join(messages)
            self.DB_MANAGER.executeOneshot(f'''
                INSERT INTO reminders (message_id, guild_id, channel_id, message, date_time)
                VALUES ('{context.id}', '{context.guild.id}', '{context.channel.id}', '{message}', {time.time() + delayToSend})
            ''')

            # trigger reminder
            asyncio.create_task(self.queueReminder(str(context.id)))

    async def queueReminder(self, messageID: str):
        """TODO"""

        data = self.DB_MANAGER.executeOneshot(f'''
            SELECT date_time
            FROM reminders
            WHERE message_id = '{messageID}'
        ''')

        if (len(data) == 1):
            delay = (float)(data[0][0]) - time.time()

            if (delay >= 0):
                await asyncio.sleep(delay) # wait until time to send
                asyncio.create_task(self.triggerReminder(messageID))
            else:
                await self.triggerReminder(messageID, late=True)

        else:
            self.LOGGER.error(f'Error fetching reminder {messageID} from database, when scheduling.')

    async def triggerReminder(self, messageID: str, late: bool = False):
        """TODO"""

        data = self.DB_MANAGER.executeOneshot(f'''
            SELECT message_id, guild_id, channel_id, message
            FROM reminders
            WHERE message_id = '{messageID}'
        ''')

        if (len(data) == 1):
            guild = self.BOT.get_guild(int(data[0][1]))
            if (guild is not None):
                channel: Any = guild.get_channel(int(data[0][2]))
                if (channel is not None):

                    messages = data[0][3].split(MESSAGE_SEPERATOR) # split into individual messages
                    for index, message in enumerate(messages):
                        if (index == 0):
                            # try to reply for the initial message
                            try:
                                initialMessage = await channel.fetch_message(int(data[0][0]))
                                await initialMessage.reply(message)
                            except discord.NotFound:
                                await channel.send(message)
                        else:
                            # send subsequent messages individually
                            await channel.send(message)

                    if (late):
                        await channel.send('(Sorry for the delay.)')

            # cleanup database
            self.DB_MANAGER.executeOneshot(f'''
                DELETE FROM reminders
                WHERE message_id = '{messageID}'
            ''')
        else:
            self.LOGGER.error(f'Error fetching reminder {messageID} from database, when sending.')


    def extractDelay(self, content: str) -> int:
        """Extracts the delay from a reminder command."""

        delay: float = 0

        content = f' {content} ' # add spaces for matching
        # CALCULATE TIME OF DAY DIRECTLY
        if (any(f' {word}' in content for word in ['at'])):

            currentTime = time.localtime() # TODO: use timezones
            targetTime = {}

            # TIME OF DAY
            temp = re.search(r'(\d{1,2}):(\d{2})', content)
            if (temp is not None):
                targetTime['hour'] = int(temp.group(1))
                targetTime['minute'] = int(temp.group(2))
            else:
                # assume now
                targetTime['hour'] = currentTime.tm_hour
                targetTime['minute'] =  currentTime.tm_min

            # DATE
            temp = re.search(r'(\d{1,2})[/\.](\d{1,2})', content)
            if (temp is not None):
                targetTime['day'] = int(temp.group(1))
                targetTime['month'] = int(temp.group(2))
            else:
                # DAY THIS WEEK
                temp = re.search(r'(mon|tue|wed|thu|fri|sat|sun)', content)
                if (temp is not None):
                    # TODO
                    pass
                else:
                    # assume today
                    targetTime['day'] = currentTime.tm_mday
                    targetTime['month'] = currentTime.tm_mon

            newTime = time.mktime((currentTime.tm_year, targetTime['month'], targetTime['day'], targetTime['hour'], targetTime['minute'], 0, 0, 0, 0))
            delay = newTime - time.time()

        # CALCULATE TIME OF MESSAGE AS A DELAY
        elif (any(f' {word}' in content for word in ['in', 'after'])):

            for unit in [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]:
                temp = re.search(rf'(\d+|an? )\s*{unit[0]}', content) # number of units, or 'a(n)' for 1

                if (temp is not None):
                    a = temp.group(1)

                    if (a[0] == 'a'):
                        delay += unit[1]
                    else:
                        delay += int(a) * unit[1]

        return delay
