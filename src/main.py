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

class JerryBot(commands.Bot):
    """TODO ..."""

    def __init__(self):

        with open(os.path.join(STATIC_DATA_PATH, 'gifs.json'), 'r', encoding='utf-8') as file:
            self.GIFS = json.load(file)

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

        print('Ready.\n')


    async def on_message(self, context: Any):
        """Reacts to messages sent to the bot."""

        if (context.author == self.user):
            return

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

        return activity, avatar

if ((TOKEN := os.environ.get('DISCORD_BOT_TOKEN')) is not None):
    bot = JerryBot()
    bot.run(TOKEN)
else:
    print('Error: No token found')
