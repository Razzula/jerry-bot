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

    def __init__(self, name: str, emote: str, triggers: list[str] | None = None, fallback: str | None = None):
        self.name = name
        self.emote = emote
        self.triggers = triggers if (triggers is not None) else []
        self.fallback = fallback if (fallback is not None) else None

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
    ALLIANCE = Emote('theAlliance', '<:theAlliance:899087916251353118>', ['alliance'], '�')
    DOUBT = Emote('doubt', '<:doubt:1084980452537937940>', ['doubt'], '🇽')
    BEANS = Emote('beans', '<:beans:796047923711836210>', ['beans'], '🫘')
    BONK = Emote('bonk', '<:bonk:798539206901235773>', [], '👎🏿')


class JerryBot(commands.Bot):
    """TODO ..."""

    active = False

    def __init__(self):

        with open(os.path.join(STATIC_DATA_PATH, 'gifs.json'), 'r', encoding='utf-8') as file:
            self.GIFS = json.load(file)

        with open(os.path.join(STATIC_DATA_PATH, 'fortune.txt'), 'r', encoding='utf-8') as file:
            wisdoms = []
            for line in file:
                line = line.rstrip() + ' '
                if (line != ' ') and (line[0] != '#'):
                    wisdoms.append(line)
            self.WISDOMS = wisdoms

        intents = discord.Intents.all()
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
                        await context.add_reaction(reaction.value.emote)
                    except discord.errors.HTTPException:
                        print(f'Error: Unknown Emoji: {reaction.value.name} ({reaction.value.emote})')
                        if (reaction.value.fallback is not None):
                            await context.add_reaction(reaction.value.fallback)
                    break

        # TAG

        # BIBLE REFERENCES

        # SOFT COMMANDS
        if ('jerry' in message or 'jezza' in message or 'jeyry' in message):

            ## REMINDERS

            ## BONK
            if ('bonk' in message):
                await self.bonk(context, message)

            ## SUMMON
            if ('summon' in message):
                await self.summon(context)

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
            await context.channel.send(random.choice(self.GIFS['dances']))
            return

        ## GIFS
        for response in self.GIFS['responses']:
            if (isinstance(response[0], str)): # single prompt
                response[0] = [response[0]]

            for prompt in response[0]:
                if (prompt in message):
                    await self.sendGIF(context.channel, response[1])
                    return

        # REGURGITATE GITHUB WEBHOOKS

    # COMMANDS
    async def bonk(self, context: Any, target: str):
        """Bonks a user."""

        if (not self.isUserAdmin(context.author)):

            await self.reactWithCustomEmote(context, Emotes.BONK.value)

            await self.sendGIF(context.channel, 'YouHaveNoPowerHere')
            return

        targets = self.getUsersFromMentions(self.extractMentionsFromMessage(context.content))
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
                    await self.sendGIF(context.channel, 'IReleaseYou')

                else: # bonk all
                    for user in toBonk:
                        await user.add_roles(bonkRole) # TODO ensure this role is not higher than the bot

                    # message channel
                    await self.sendGIF(context.channel, random.choice(self.GIFS['bonks']))
                    if (random.randint(0, 5) <= 2):
                        await context.channel.send('https://www.youtube.com/watch?v=2D7P1khV40U') # The Lion King 2 Not One Of Us

                    # message bonk jail
                    bonkJail = discord.utils.get(context.guild.channels, name='bonk-jail')
                    if (bonkJail is not None):
                        await bonkJail.send(', '.join([u.mention for u in toBonk]))
                        await self.sendGIF(bonkJail, self.GIFS['shames'])
                    else:
                        print("`#bonk-jail` channel does not exist")

            else:
                print("Role `Bonk Jail` does not exist")
                await self.sendGIF(context.channel, random.choice(self.GIFS['bonks']))

        else:  # no user specified
            await context.add_reaction('❓')

    async def summon(self, context: Any):
        """Summons a user or role to the current channel."""

        target = self.extractSmallestMentionSubset(context.content)
        if (target):

            # TODO: subtle
            # TODO: reminders (reply, not just send message)

            await context.add_reaction('👍🏿')
            await context.channel.send(target)
            await self.sendGIF(context.channel, random.choice(self.GIFS['summons']))

        else:  # no user specified
            await context.add_reaction('❓')

    # HELPER FUNCTIONS
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

    async def sendGIF(self, channel: Any, gifName: str):
        """Sends a GIF to the current channel."""

        await channel.send(f'https://raw.githubusercontent.com/Razzula/jerry-bot/v2.0/data/static/gifs/{gifName}.gif') # TODO: switch to master branch

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

if ((TOKEN := os.environ.get('DISCORD_BOT_TOKEN')) is not None):
    bot = JerryBot()
    bot.run(TOKEN)
else:
    print('Error: No token found')
