# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""Discord bot that responds to messages and commands."""
import os
import random
import json
from typing import Final, Any, Sequence
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands

from src.BotUtils import BotUtils, Emotes
from src.DatabaseManager import DatabaseManager
from src.apis.bibleAPI import BibleAPI

from src.cogs.CogTemplate import CustomCog
from src.cogs.JerryCog import JerryCog
from src.cogs.SteamCog import SteamCog
from src.cogs.TagCog import TagCog
from src.logger import Logger

load_dotenv('tokens.env')

DYNAMIC_DATA_PATH: Final[str] = 'data/dynamic/'
STATIC_DATA_PATH: Final[str] = 'data/static/'

class JerryBot:
    """Main class for the bot."""

    BOT_ALIASES = ['jerry', 'jezza', 'jeyry']

    def __init__(self):
        """Constructor for the bot."""

        with open(os.path.join(STATIC_DATA_PATH, 'gifs.json'), 'r', encoding='utf-8') as file:
            self.GIFS = json.load(file)

        self.LOGGER = Logger('BOT', level=logging.INFO)

        self.DB_MANAGER = DatabaseManager(os.path.join(DYNAMIC_DATA_PATH, 'global.db'))

        self.BOT_UTILS = BotUtils(self.LOGGER, STATIC_DATA_PATH, DYNAMIC_DATA_PATH)

        intents = discord.Intents.all()
        self.BOT = commands.Bot(intents=intents, command_prefix='!', help_command=None, case_insensitive=True, strip_after_prefix=True)

        # Cogs
        self.JerryCoreCog = JerryCoreCog(self.BOT, self.LOGGER, self.BOT_UTILS, self.DB_MANAGER, self.BOT_ALIASES, self.GIFS)
        self.cogs = [
            JerryCog(self.BOT, self.LOGGER, self.BOT_UTILS, self.DB_MANAGER, self.GIFS),
            SteamCog(self.BOT, self.LOGGER, self.BOT_UTILS, self.DB_MANAGER, os.environ.get('STEAM_API_KEY')),
            TagCog(self.BOT, self.LOGGER, self.BOT_UTILS, self.GIFS),
        ]

    @classmethod
    async def create(cls):
        """Asynchronously creates a bot instance (supports loading cogs)."""

        bot = cls()
        await bot.loadCogs()
        return bot

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

    def __init__(self, bot: commands.Bot, logger: Logger, botUtils: BotUtils, dbManager: DatabaseManager, botNames: list[str], gifs: dict[str, list[str]]):

        self.LOGGER: Final[Logger] = logger
        self.DB_MANAGER: Final[DatabaseManager] = dbManager

        super().__init__('JerryCoreCog', logger, [
            { 'aliases': ['help'], 'short': 'help', 'icon': '❓', 'description': '...literally the command you just used.' },
            { 'aliases': ['ping', 'pong'], 'short': 'ping, pong', 'icon': '🏓', 'description': 'Just like on the Atari.' },
        ])

        self.BOT: Final[commands.Bot] = bot

        self.BOT_UTILS: Final[BotUtils] = botUtils
        self.BIBLE_API = BibleAPI(STATIC_DATA_PATH)

        self.BOT_ALIASES: Final[list[str]] = botNames
        self.GIFS: Final[dict[str, list[str]]] = gifs

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

        if ((cog := self.loadedCogs.get(cogName)) is not None):
            await command(cog, context, args[0])

    @commands.Cog.listener()
    async def on_ready(self):
        """Initializes the bot when it is ready."""

        self.LOGGER.info(f'Logged in as {self.BOT.user}\n')
        await self.BOT.change_presence(status=discord.Status.invisible) # appear offline initially, whilst bot is setting up

        # ACTIVITY
        activity, avatar = self.BOT_UTILS.getActivity()

        # profile picture
        if (not os.environ.get('DEBUG')):  # disable avatar change in debug mode, as excessive calls will result in a timeout
            try:
                await self.BOT.user.edit(avatar=avatar)
            except discord.errors.HTTPException:
                self.LOGGER.warn('Avatar not changed: HTTPException')
        # presence
        await self.BOT.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=activity)
        )

        self.LOGGER.info('Ready.\n')

    @commands.Cog.listener()
    async def on_message(self, context: Any):
        """Reacts to messages sent to the bot."""

        message: str = context.content.lower()  # removes case sensitivity
        if (context.author == self.BOT.user):
            return
        if (message.startswith('http') or message.startswith('www.')):  # ignore links (GIFs)
            return

        # REACT
        for reaction in Emotes:
            for prompt in reaction.value.triggers:
                if (prompt in message):
                    await self.BOT_UTILS.reactWithEmote(context, reaction.value)
                    break

        # BIBLE REFERENCES
        references: list[list[str]] | None = self.BIBLE_API.getBibleReferences(message)
        if (references is not None):
            for reference in references:
                await context.channel.send(reference[0])
                for chunk in reference[1]:
                    await context.channel.send(f'> {chunk}')
            return

        # SOFT COMMANDS
        for keyword in ['remind', 'ask', 'tell']:
            if (keyword in message):
                await self.callCommand('JerryCog', JerryCog.setReminder, context, keyword)
                return

        for name in self.BOT_ALIASES: # jerry, ...
            if (name in message):

                ## REMINDERS

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

            # RESPOND
            ## DANCE
            if ('dance' in message):
                await self.BOT_UTILS.sendGIF(context.channel, random.choice(self.GIFS['dances']))
                return

            ## GIFS
            for response in self.GIFS['responses']:
                if (isinstance(response[0], str)): # single prompt
                    response[0] = [response[0]]

                for prompt in response[0]:
                    if (prompt in message):
                        await self.BOT_UTILS.sendGIF(context.channel, response[1])
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
                title='What can men do against such reckless hate?',
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
