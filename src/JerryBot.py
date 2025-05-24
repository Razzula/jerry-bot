# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""Discord bot that responds to messages and commands."""
import asyncio
from datetime import datetime, timedelta
import os
import random
import json
import subprocess
from typing import Final, Any, Sequence, Callable, Awaitable
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
import httpx
import re

from src.BotUtils import BotUtils, Emotes
from src.DatabaseManager import DatabaseManager
from src.apis.bibleAPI import BibleAPI

from src.cogs.CogTemplate import CustomCog
from src.cogs.JerryCog import JerryCog
from src.cogs.SteamCog import SteamCog
from src.cogs.TagCog import TagCog
from src.cogs.NerdBotCog import NerdBotCog
from src.logger import Logger

load_dotenv('tokens.env')

DYNAMIC_DATA_PATH: Final[str] = 'data/dynamic/'
STATIC_DATA_PATH: Final[str] = 'data/static/'

PUNCTUATION_STRIPPER = str.maketrans('', '', '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')

class JerryBot:
    """Main class for the bot."""

    BOT_ALIASES = ['jerry', 'jezza', 'jeyry']

    def __init__(self: Any):
        """Constructor for the bot."""

        with open(os.path.join(STATIC_DATA_PATH, 'gifs.json'), 'r', encoding='utf-8') as file:
            self.GIFS = json.load(file)
        with open(os.path.join(STATIC_DATA_PATH, 'responses.json'), 'r', encoding='utf-8') as file:
            self.RESPOSNES = json.load(file)

        self.LOGGER = Logger('BOT', level=logging.INFO)

        self.DB_MANAGER = DatabaseManager(os.path.join(DYNAMIC_DATA_PATH, 'global.sqlite'))

        self.BOT_UTILS = BotUtils(self.LOGGER, STATIC_DATA_PATH, DYNAMIC_DATA_PATH)

        intents = discord.Intents.all()
        self.BOT = commands.Bot(intents=intents, command_prefix='!', help_command=None, case_insensitive=True, strip_after_prefix=True)

        # Database
        self.setupDatabase()

        # Cogs
        self.JerryCoreCog = JerryCoreCog(self.BOT, self.LOGGER, self.BOT_UTILS, self.DB_MANAGER, self.BOT_ALIASES, self.GIFS, self.RESPOSNES)
        self.cogs = [
            JerryCog(self.BOT, self.LOGGER, self.BOT_UTILS, self.DB_MANAGER, self.GIFS),
            SteamCog(self.BOT, self.LOGGER, self.BOT_UTILS, self.DB_MANAGER, os.environ.get('STEAM_API_KEY')),
            TagCog(self.BOT, self.LOGGER, self.BOT_UTILS, self.GIFS),
            NerdBotCog(self.BOT, self.LOGGER, self.BOT_UTILS, self.GIFS),
        ]

    @classmethod
    async def create(cls: Any):
        """Asynchronously creates a bot instance (supports loading cogs)."""

        bot = cls()
        await bot.loadCogs()
        return bot

    def setupDatabase(self):
        """Sets up the database for the bot."""

        self.DB_MANAGER.executeOneshot('''
            CREATE TABLE IF NOT EXISTS botAdmins (
                discordID VARCHAR(18) PRIMARY KEY
            )
        ''')

        self.DB_MANAGER.executeOneshot('''
            CREATE TABLE IF NOT EXISTS emergencyContacts (
                webhookID VARCHAR(19) PRIMARY KEY,
                webhookToken VARCHAR(68),
                name VARCHAR(32)
            )
        ''')

    async def loadCogs(self):
        """Loads the cogs defined in the constructor."""
        helpList = self.JerryCoreCog.getHelpList()

        loadedCogs: dict[str, CustomCog] = {}

        if (self.cogs):
            for cog in self.cogs:
                helpList.extend(cog.getHelpList())
                await self.BOT.add_cog(cog)

                loadedCogs[cog.COG_NAME] = cog

        self.JerryCoreCog.setHelpList(helpList)
        self.JerryCoreCog.setLoadedCogs(loadedCogs)

        await self.BOT.add_cog(self.JerryCoreCog)

    async def run(self, TOKEN, verbosity: int = logging.INFO):
        """Asynchronously runs the bot."""

        try:
            await self.BOT.start(TOKEN, reconnect=True)
        except discord.errors.LoginFailure:
            self.LOGGER.error('Error: Invalid token.')

    async def close(self):
        """Closes the bot."""

        await self.BOT.close()


class JerryCoreCog(CustomCog):
    """
    Core cog for the bot.

    Provides basic functionality such as help, ping, and pong.
    """

    def __init__(self, bot: commands.Bot, logger: Logger, botUtils: BotUtils, dbManager: DatabaseManager, botNames: list[str], gifs: dict[str, list[Any]], responses: dict[str, list[Any]]):

        self.LOGGER: Final[Logger] = logger
        self.DB_MANAGER: Final[DatabaseManager] = dbManager

        super().__init__('JerryCoreCog', logger, [
            { 'aliases': ['help'], 'short': 'help', 'icon': '❓', 'description': '...literally the command you just used.' },
            { 'aliases': ['ping', 'pong'], 'short': 'ping, pong', 'icon': '🏓', 'description': 'Just like on the Atari.' },
            # { 'aliases': ['version'], 'short': 'version', 'icon': '⚙️', 'description': 'Display the current version of the bot.' }, # Disabled from help menu
        ])

        self.BOT: Final[commands.Bot] = bot

        self.BOT_UTILS: Final[BotUtils] = botUtils
        self.BIBLE_API = BibleAPI(STATIC_DATA_PATH)

        self.BOT_ALIASES: Final[list[str]] = botNames
        self.GIFS: Final[dict[str, Any]] = gifs
        self.RESPONSES: Final[dict[str, str]] = responses

        self.helpList: list[dict[str, str | Sequence[str]]] = []
        self.loadedCogs: dict[str, CustomCog] = {}

        with open(os.path.join(STATIC_DATA_PATH, 'fortune.txt'), 'r', encoding='utf-8') as file:
            wisdoms = []
            for line in file:
                line = line.rstrip() + ' '
                if (line != ' ') and (line[0] != '#'):
                    wisdoms.append(line)
            self.WISDOMS = wisdoms

    def setHelpList(self, helpList: list[dict[str, str | Sequence[str]]]):
        """HelpList setter."""

        self.helpList = helpList

    def setLoadedCogs(self, loadedCogs: dict[str, CustomCog]):
        """LoadedCogs setter."""

        self.loadedCogs = loadedCogs

    async def callCommand(self, cogName: str, command: Any, context: Any, *args):
        """Calls a command from a cog."""

        arg = args[0] if args else None

        if ((cog := self.loadedCogs.get(cogName)) is not None):
            await command(cog, context, arg)

    @commands.Cog.listener()
    async def on_ready(self):
        """Initializes the bot when it is ready."""

        self.LOGGER.info(f'Running JerryBot v{self.getBotVersion()}')
        self.LOGGER.info(f'Logged in as {self.BOT.user}\n')
        await self.BOT.change_presence(status=discord.Status.do_not_disturb) # appear DND initially, whilst bot is setting up

        await self.setupBot()

        self.LOGGER.info('Ready.\n')

    async def scheduleTaskForNextHour(self, method: Callable[..., Awaitable[None]]):
        """Schedules a task to run at the next hour."""

        currentTime = datetime.now()
        nextHour = (currentTime.replace(second=0, microsecond=0, minute=0) + timedelta(hours=1)).replace(tzinfo=currentTime.tzinfo)

        delay = (nextHour - currentTime).total_seconds()
        await asyncio.sleep(delay)

        await method()

    async def setupBot(self):
        """Sets up the bot."""

        # ACTIVITY
        activity, activityType, avatar = self.BOT_UTILS.getActivity()

        # profile picture
        if (not os.environ.get('DEBUG')):  # disable avatar change in debug mode, as excessive calls will result in a timeout
            try:
                await self.BOT.user.edit(avatar=avatar)
            except discord.errors.HTTPException:
                self.LOGGER.warn('Avatar not changed: HTTPException')
        # presence
        await self.BOT.change_presence(
            activity=discord.Activity(
                status=discord.Status.online,
                type=activityType,
                name=activity
            )
        )

        asyncio.create_task(self.scheduleTaskForNextHour(self.setupBot))

    @commands.Cog.listener()
    async def on_message(self, context: Any):
        """Reacts to messages sent to the bot."""

        if (context.author == self.BOT.user): # ignore self
            return
        message: str = context.content.lower()  # removes case sensitivity
        if (message.startswith('http') or message.startswith('www.')):  # ignore links (GIFs)
            return
        messageMin: str = message.translate(PUNCTUATION_STRIPPER) # removes punctuation

        # REACT
        for reaction in Emotes:
            for prompt in reaction.value.triggers:
                if (prompt in message):
                    await self.BOT_UTILS.reactWithEmote(context, reaction.value)
                    break

        # RESPOND
        response = self.BOT_UTILS.getFromComplexList(self.RESPONSES, messageMin)
        if (response is not None and len(response) > 0):
            await context.reply(response[0])
            for chunk in response[1:]:
                await context.channel.send(chunk)
            return

        # BIBLE REFERENCES
        references: list[list[str]] | None = self.BIBLE_API.getBibleReferences(message)
        if (references is not None):
            for reference in references:
                await context.channel.send(reference[0])
                for chunk in reference[1]:
                    await context.channel.send(f'> {chunk}')
            return

        # COLOURS
        hexhash = re.findall(r"#([0-9a-fA-F]{3,8})", message)
        if (hexhash):
            await context.reply(f'https://www.colorhexa.com/{hexhash[0]}.png')

        # SOFT COMMANDS

        # for name in [*self.BOT_ALIASES, 'someone', 'somebody', 'anyone', 'anybody']: # jerry, ..., someone, ...
        #     if (name in message):
        ## REMINDERS
        for keyword in ['remind', 'ask', 'tell']:
            if (keyword in message):
                await self.callCommand('JerryCog', JerryCog.setReminder, context, keyword)
                return

        for name in self.BOT_ALIASES: # jerry, ...
            if (name in message):

                ## BONK
                if ('bonk' in message):
                    await self.callCommand('JerryCog', JerryCog.bonk, context, message)
                    return

                ## SUMMON
                if ('summon' in message):
                    await self.callCommand('JerryCog', JerryCog.summon, context, message)
                    return

                ## DECIDE STEAM GAME
                if (any(keyword in message for keyword in ['choose', 'decide', 'pick', 'which', 'what'])):
                    if ('game' in message):
                        await self.callCommand('SteamCog', SteamCog.decideGame, context, message)
                        return

                ## WORDS OF WISDOM
                if ('wis' in message):
                    if (self.WISDOMS):
                        await context.channel.send(random.choice(self.WISDOMS).format('<@' + str(context.author.id) + '>'))
                    else:
                        self.LOGGER.error('Error: fortune.txt is blank')
                        await context.channel.send("Hmm. I can't think of anything... 🤔")
                    return

            ## DANCE
            for trigger in ['danc', 'party', 'boog', 'whoo', 'woo', 'celebr']:
                if (trigger in message):
                    await self.callCommand('JerryCog', JerryCog.dance, context)
                    return

            ## HIGH FIVES
            if ('high' in message and 'five' in message):
                if (self.GIFS):
                    delay = random.randint(0, 2)

                    self.DB_MANAGER.storeInCache('JerryBot', 'highfives', str(context.author.id), context.channel.id, timeUntilExpire=delay)
                    await asyncio.sleep(delay)

                    tooSlow = self.DB_MANAGER.getFromCache('JerryBot', 'tooslow', str(context.author.id))
                    if (tooSlow is not None and tooSlow[0] == context.channel.id):
                        return # cancel high-five, as user has 'too slowed' Jerry
                    await self.BOT_UTILS.sendGIF(context.channel, random.choice(self.GIFS['highfives']))
                    self.DB_MANAGER.storeInCache('JerryBot', 'toofast', str(context.author.id), context.channel.id, timeUntilExpire=3)
                else:
                    self.LOGGER.error('Error: gifs.json is blank')
                return
            elif ('too slow' in message):
                highFive = self.DB_MANAGER.getFromCache('JerryBot', 'highfives', str(context.author.id))
                if (highFive is not None and highFive[0] == context.channel.id):
                    self.DB_MANAGER.storeInCache('JerryBot', 'tooslow', str(context.author.id), context.channel.id, timeUntilExpire=3)
                    await self.BOT_UTILS.sendGIF(context.channel, 'TooSlow')
                    return

                tooFast = self.DB_MANAGER.getFromCache('JerryBot', 'toofast', str(context.author.id))
                if (tooFast is not None and tooFast[0] == context.channel.id):
                    await self.BOT_UTILS.sendGIF(context.channel, 'IKnowYouAre')
                    return

        ## GIFS
        gif = self.BOT_UTILS.getFromComplexList(self.GIFS['responses'], message)
        if (gif is not None and len(gif) > 0):
            for chunk in gif:
                await self.BOT_UTILS.sendGIF(context.channel, chunk)
            return

        ## HUGS
        if ('hug' in message):
            await self.callCommand('JerryCog', JerryCog.hug, context)
            return

    @commands.command(name='ping')
    async def ping(self, context: Any):
        """Pings the bot."""

        await context.send('Pong!')

    @commands.command(name='pong')
    async def pong(self, context: Any):
        """Pings the bot. (Alternate)."""

        await context.send('Ping!')

    @commands.command(name='help', pass_context=True)
    async def help(self, context: Any, arg: str | None = None):
        """Displays the help menu."""

        prefix = await self.BOT.get_prefix(context)
        if (isinstance(prefix, list)):
            prefix = prefix[0]

        if (arg is None): # list commands
            embed = discord.Embed(
                title=random.choice([
                    'What can men do against such reckless hate?',
                    'Legolas, what do your elf eyes see?',
                    'Do you know what you\'re doing, kid?',
                    'You think you know how the world works?',
                ]),
                color=discord.Color.red()
            )

            for field in self.helpList:
                embed.add_field(name=f'{prefix}{field.get("short")}', value=field.get('icon'))

            embed.set_footer(text=f'Use `{prefix}help <command>` for more details.')

        else: # show specific details for a command

            helpList = None
            for command in self.helpList:
                if (arg in command['aliases']):
                    helpList = command

            if (helpList is not None):

                embed = discord.Embed(
                    title=f'{prefix}{arg} {helpList.get("icon")}',
                    color=discord.Color.red(),
                )

                embed.add_field(name=f'{prefix}{helpList["short"]}', value=helpList['description'])

                if (aliases := helpList.get('aliases')):
                    if (len(aliases) > 1):
                        aliases.remove(arg)
                        aliases = ', '.join(aliases)
                        embed.set_footer(text=f'Aliases: {aliases}')

            else:
                await context.send(f'`{arg}` is not a valid command.')
                return

        await context.send(embed=embed)

    @commands.command(name='version')
    async def version(self, context: Any):
        """Displays the current version of the bot."""

        version = f'⚙️ JerryBot v{self.getBotVersion()}'

        res = subprocess.run('git fetch && git status', stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=True)
        if ('branch is up to date' not in res.stdout.decode('utf-8')):
            version += ' (outdated)'

        await context.send(version)

    def getBotVersion(self) -> str:
        """Gets the version of the bot."""

        with open('VERSION', 'r', encoding='utf-8') as file:
            return file.read().strip()

    @commands.command(name='update')
    async def update(self, context: Any):
        """Trigger the parent server to update the bot."""

        if (self.BOT_UTILS.isUserBotAdmin(str(context.author.id), self.DB_MANAGER)):
            await self.BOT_UTILS.reactWithEmoteStr(context, '👍🏿')
            # TODO maybe pinging the update endpoint would work on the RPi
            port = os.environ.get('SERVER_PORT') or '8000'
            headers = {}

            if ((auth := os.environ.get('SERVER_AUTH_TOKEN')) is not None):
                headers['Authorization'] = f'Bearer {auth}'

            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f'http://localhost:{port}/update', headers=headers)
                    if (response.status_code == 200):
                        return
                    else:
                        await self.BOT_UTILS.reactWithEmoteStr(context, '👎🏿')
                except httpx.RequestError:
                    await self.BOT_UTILS.reactWithEmoteStr(context, '👎🏿')
        else:
            await self.BOT_UTILS.reactWithEmote(context, Emotes.BONK.value)
