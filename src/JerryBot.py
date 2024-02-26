# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, unused-import, trailing-whitespace, arguments-differ
"""TODO ..."""
import os
import random
import time
from datetime import datetime, timedelta
import asyncio
import re
import json
from enum import Enum
from typing import Final, Any
from dotenv import load_dotenv
import logging
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import steamAPI
import bibleAPI

from BotHelper import BotUtils, Emotes, Emote
from CogTemplate import CustomCog
from JerryCog import JerryCog

load_dotenv('token.env')

DYNAMIC_DATA_PATH: Final[str] = 'data/dynamic/'
STATIC_DATA_PATH: Final[str] = 'data/static/'

class JerryBot:
    """TODO"""

    BOT_ALIASES = ['jerry', 'jezza', 'jeyry']

    def __init__(self):
        """TODO"""

        with open(os.path.join(STATIC_DATA_PATH, 'gifs.json'), 'r', encoding='utf-8') as file:
            self.GIFS = json.load(file)

        self.BOT_UTILS = BotUtils(STATIC_DATA_PATH, DYNAMIC_DATA_PATH)

        intents = discord.Intents.all()
        self.BOT = commands.Bot(intents=intents, command_prefix='!', help_command=None, case_insensitive=True, strip_after_prefix=True)

        # Cogs
        self.JerryCoreCog = JerryCoreCog(self.BOT, self.BOT_UTILS, self.BOT_ALIASES, self.GIFS)
        asyncio.run(self.loadCogs([
            JerryCog(self.BOT, self.BOT_UTILS, self.GIFS),
        ]))


    async def loadCogs(self, additionalCogs: list[Any] | None = None):
        """TODO"""
        helpList = self.JerryCoreCog.getHelpList()

        loadedCogs: dict[str, CustomCog] = {}

        if (additionalCogs):
            for cog in additionalCogs:
                helpList.extend(cog.getHelpList())
                await self.BOT.add_cog(cog)

                loadedCogs[cog.COG_NAME] = cog

        self.JerryCoreCog.setHelpList(helpList)
        self.JerryCoreCog.setLoadedCogs(loadedCogs)

        await self.BOT.add_cog(self.JerryCoreCog)

    def run(self, verbosity: int):
        """TODO"""

        self.BOT.run(TOKEN, log_level=verbosity)


class JerryCoreCog(CustomCog):
    """TODO"""

    def __init__(self, bot: commands.Bot, botUtils: BotUtils, botNames: list[str], gifs: dict[str, list[str]]):
        super().__init__('JerryCoreCog', [
            ['help', '❓'],
            ['ping, pong', '🏓'],
        ])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_HELPER: Final[BotUtils] = botUtils

        self.BOT_ALIASES: Final[list[str]] = botNames
        self.GIFS: Final[dict[str, list[str]]] = gifs

        self.helpList: list[list[str]] = []
        self.loadedCogs: dict[str, CustomCog] = {}

        with open(os.path.join(STATIC_DATA_PATH, 'fortune.txt'), 'r', encoding='utf-8') as file:
            wisdoms = []
            for line in file:
                line = line.rstrip() + ' '
                if (line != ' ') and (line[0] != '#'):
                    wisdoms.append(line)
            self.WISDOMS = wisdoms

    def setHelpList(self, helpList: list[list[str]]):
        """TODO"""

        self.helpList = helpList

    def setLoadedCogs(self, loadedCogs: dict[str, CustomCog]):
        """TODO"""

        self.loadedCogs = loadedCogs

    async def callCommand(self, cogName: str, command: Any, context: Any, arg: str):
        """Calls a command from a cog."""

        if ((cog := self.loadedCogs.get(cogName)) is not None):
            await command(cog, context, arg)

    @commands.Cog.listener()
    async def on_ready(self):
        """Initializes the bot when it is ready."""

        print(f'Logged in as {self.BOT.user}\n')
        await self.BOT.change_presence(status=discord.Status.invisible) # appear offline initially, whilst bot is setting up

        # ACTIVITY
        activity, avatar = self.BOT_HELPER.getActivity()

        # profile picture
        if (not os.environ.get('DEBUG')):  # disable avatar change in debug mode, as excessive calls will result in a timeout
            try:
                await self.BOT.user.edit(avatar=avatar)
            except discord.errors.HTTPException:
                print('Avatar not changed: HTTPException')
        # presence
        await self.BOT.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=activity)
        )

        # REMINDERS
        # TODO

        print('Ready.\n')

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
                    await self.BOT_HELPER.reactWithEmote(context, reaction.value)
                    break

        # TAG

        # BIBLE REFERENCES

        # SOFT COMMANDS
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

                ## WORDS OF WISDOM
                if ('wis' in message):
                    if (self.WISDOMS):
                        await context.channel.send(random.choice(self.WISDOMS).format('<@' + str(context.author.id) + '>'))
                    else:
                        print('Error: fortune.txt is blank')
                        await context.channel.send("Hmm. I can't think of anything... 🤔")
                    return

            # RESPOND
            ## DANCE
            if ('dance' in message):
                await self.BOT_HELPER.sendGIF(context.channel, random.choice(self.GIFS['dances']))
                return

            ## GIFS
            for response in self.GIFS['responses']:
                if (isinstance(response[0], str)): # single prompt
                    response[0] = [response[0]]

                for prompt in response[0]:
                    if (prompt in message):
                        await self.BOT_HELPER.sendGIF(context.channel, response[1])
                        return

        # REGURGITATE GITHUB WEBHOOKS

        # await self.BOT.process_commands(context)

    @commands.command(name='ping')
    async def ping(self, context: Any):
        """Pings the bot."""

        await context.send('Pong!')

    @commands.command(name='pong')
    async def pong(self, context: Any):
        """Pings the bot. (Alternate)"""

        await context.send('Ping!')

    @commands.command(name='help', pass_context=True)
    async def help(self, context: Any):
        """Displays the help menu."""

        embed = discord.Embed(
            title='What can men do against such reckless hate?', color=discord.Color.red()
        )

        prefix = await self.BOT.get_prefix(context)
        if (isinstance(prefix, list)):
            prefix = prefix[0]

        for field in self.helpList:
            embed.add_field(name=f'{prefix}{field[0]}', value=field[1])

        await context.send(embed=embed)


if ((TOKEN := os.environ.get('DISCORD_BOT_TOKEN')) is not None):
    BOT = JerryBot()
    BOT.run(logging.INFO)
else:
    print('Error: No token found')
