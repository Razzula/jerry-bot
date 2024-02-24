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
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import steamAPI
import bibleAPI

load_dotenv('token.env')

DYNAMIC_DATA_PATH: Final[str] = 'data/dynamic/'
STATIC_DATA_PATH: Final[str] = 'data/static/'

class Emote:
    """TODO ..."""

    def __init__(self, name: str, value: str, triggers: list[str] | None = None):
        self.name = name
        self.value = value
        self.triggers = triggers if (triggers is not None) else []

class Emotes(Enum):
    """Enum of custom emotes"""

    JERRY = Emote('jerry', '❤️', ["jerry", "good bot", "attab"])

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
    ALLIANCE = Emote('theAlliance', '<:theAlliance:899087916251353118>', ['alliance'])
    DOUBT = Emote('doubt', '<:doubt:1084980452537937940>', ['doubt'])
    BEANS = Emote('beans', '<:beans:796047923711836210>', ['beans'])


class JerryBot(commands.Bot):
    """TODO ..."""

    active = False

    def __init__(self):

        with open(os.path.join(STATIC_DATA_PATH, 'gifs.json'), 'r', encoding='utf-8') as file:
            self.GIFS = json.load(file)

        with open(os.path.join(STATIC_DATA_PATH, 'emotes.json'), 'r', encoding='utf-8') as file:
            self.EMOTES = json.load(file)

        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        intents.message_content = True
        commands.Bot.__init__(self, intents=intents, command_prefix='!', help_command=None, case_insensitive=True, description='JerryBot')

    async def on_ready(self):
        """Initializes the bot when it is ready."""

        print(f'Logged in as {self.user}\n')
        await self.change_presence(status=discord.Status.invisible) # appear offline initially, whilst bot is setting up

        # CONFIGURE BOT
        activity, avatar = self.getActivity()

        # profile picture
        if (not os.environ.get('DEBUG')):  # disable avatar change in debug mode, as excessive calls will result in a timeout
            try:
                await self.user.edit(avatar=avatar)
            except discord.errors.HTTPException:
                print('Avatar not changed: HTTPException')
        # presence
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=activity)
        )

        # reminders
        # TODO

        self.active = True
        print('Ready.\n')


    async def on_message(self, context: Any):
        """Reacts to messages sent to the bot."""

        message: str = context.content.lower()  # removes case sensitivity
        if ((not self.active) or (context.author == self.user)):
            return
        if (message.startswith('http') or message.startswith('www.')):  # ignore links (GIFs)
            return

        # REACT
        for reaction in Emotes:
            for prompt in reaction.value.triggers:
                if (prompt in message):
                    try:
                        await context.add_reaction(reaction.value.value)
                    except discord.errors.HTTPException:
                        print(f'Error: Unknown Emoji: {reaction.value.name} ({reaction.value.value})')
                    break

        # SOFT COMMANDS
        ## TAG

        ## BIBLE REFERENCES

        ## REMINDERS

        ## BONK

        ## SUMMON

        ## DANCE

        ## DECIDE STEAM GAME

        ## WORDS OF WISDOM

        # RESPOND
        for response in self.GIFS['responses']:
            if (isinstance(response[0], str)): # single prompt
                response[0] = [response[0]]

            for prompt in response[0]:
                if (prompt in message):
                    await context.channel.send(f'https://github.com/Razzula/jerry-bot/blob/v2.0/data/static/gifs/{response[1]}.gif') # TODO: switch to master branch
                    return

        # REGURGITATE GITHUB WEBHOOKS


    def getActivity(self):
        """Determine the bot's activity and profile picture based on the current date."""

        activity = 'Baba Yetu'

        today = datetime.now()
        if (today.month == 12):  # DECEMBER (CHRISTMAS)
            with open(os.path.join(STATIC_DATA_PATH ,'pfp/jerry-festag.png'), 'rb') as image:
                avatar = image.read()

            if (today.day <= 14):  # JINGLE JAM
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
            with open(os.path.join(STATIC_DATA_PATH ,'pfp/jerry.png'), 'rb') as image:
                avatar = image.read()

            if (today.month == 5 and today.day == 4):  # MAY THE 4TH
                activity = 'Duel of the Fates'
            elif (today.month == 2 and today.day == 14):  # VALENTIE'S DAY
                activity = 'Careless Whisper'

        return activity, avatar

if ((TOKEN := os.environ.get('DISCORD_BOT_TOKEN')) is not None):
    bot = JerryBot()
    bot.run(TOKEN)
else:
    print('Error: No token found')
