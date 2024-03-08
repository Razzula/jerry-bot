# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ, import-not-found
"""TODO ..."""
import random
import re
import time
import asyncio
from typing import Final, Any
import discord
from discord.ext import commands

from BotUtils import BotUtils, Emotes, Emote
from DatabaseHandler import DatabaseHandler
from cogs.CogTemplate import CustomCog

PERSPECTIVE_CONVERTOR = {
    # first -> second
    'my': 'your',
    'myself': 'yourself',
    'me': 'you',
    'i': 'you',
    'mine': 'yours',
    'am': 'are',
    "i'm": "you're",
    "i'll": "you'll",
    # second -> third
    'you': 'they',
    'your': 'their',
    'yours': 'theirs',
    'yourself': 'themselves',
    "you're": "they're",
    "you'll": "they'll",
}

class JerryCog(CustomCog):
    """TODO"""

    def __init__(self, bot: commands.Bot, botUtils: BotUtils, dbHandler: DatabaseHandler, gifs: dict[str, list[str]]):

        self.DB_HANDLER: Final[DatabaseHandler] = dbHandler

        super().__init__('JerryCog', [
            ['party',               '🎉'],
            ['pick `a`,`b`,...',    '❔'],
            ['roll `n`',            '🎲'],
            ['bonk `@`',            Emotes.BONK.value.emote],
            ['summon `@`',          '🎺'],
        ])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_UTILS: Final[BotUtils] = botUtils

        self.GIFS: Final[dict[str, list[str]]] = gifs

    def setupDatabase(self):
        """TODO"""

        cursor = self.DB_HANDLER.getCursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                guild_id VARCHAR(32),
                channel_id VARCHAR(32),
                message_id VARCHAR(32),
                message VARCHAR(2000),
                date_time FLOAT
            )
        ''')
        self.DB_HANDLER.commit()

    @commands.command(name='party')
    async def dance(self, context: Any):
        """Sends a random dance GIF."""

        await self.BOT_UTILS.sendGIF(context.channel, random.choice(self.GIFS['dances']))

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
                        print("`#bonk-jail` channel does not exist")

            else:
                print("Role `Bonk Jail` does not exist")
                await self.BOT_UTILS.sendGIF(context.channel, random.choice(self.GIFS['bonks']))

        else:  # no user specified
            await self.BOT_UTILS.reactWithEmoteStr(context, '❓')

    @commands.command(name='summon', pass_context=True)
    async def summon(self, context: Any, *args):
        """Summons a user or role to the current channel."""

        targets = self.BOT_UTILS.extractSmallestMentionSubset(' '.join(args))
        if (targets):

            # TODO: subtle
            # TODO: reminders (reply, not just send message)

            await self.BOT_UTILS.reactWithEmoteStr(context, '👍🏿')
            await context.channel.send(targets)
            await self.BOT_UTILS.sendGIF(context.channel, random.choice(self.GIFS['summons']))

        else:  # no user specified
            await self.BOT_UTILS.reactWithEmoteStr(context, '❓')

    async def setReminder(self, context: Any, *args):
        """TODO"""

        # get message
        content = context.content + ' '
        needsName = re.search(r'remind (me|.*?)[ .]', content)

        if (needsName is None):
            await context.channel.send('Remind you of what?')
            return

        target = needsName.group(1)
        if (target in ['me', None]):
            target = context.author.mention

        needsName = re.search(r'remind (me|.*?) .*?(?:to|that|about|of) (.*)', content)
        if (needsName is not None):
            temp = needsName.group(2).split(' ')

            message = f'{target}, '
            for word in temp:
                newWord = PERSPECTIVE_CONVERTOR.get(word.lower())
                if (newWord is not None):
                    message += newWord + ' '
                    continue
                message += word + ' '

        else:
            message = f'{target}'


        # calculate delay
        delayToSend = self.extractDelay(context.content)

        if (delayToSend <= 999):
            await context.reply(message)

        else:
            # store to be resumable
            self.DB_HANDLER.executeOneshot(f'''
                INSERT INTO reminders (message_id, guild_id, channel_id, message, date_time)
                VALUES ('{context.id}', '{context.guild.id}', '{context.channel.id}', '{message}', {time.time() + delayToSend})
            ''')

            # triggrer reminder
            asyncio.create_task(self.queueReminder(str(context.id)))

    async def queueReminder(self, messageID: str):
        """TODO"""

        pass

    async def triggerReminder(self):
        """TODO"""

        pass

    def extractDelay(self, content: str) -> int:
        """Extracts the delay from a reminder command."""

        delay = 0

        for unit in [('day', 86400), ('hour', 3600), ('min', 60), ('sec', 1)]:
            temp = re.search(rf'(\d+|an?) {unit[0]}', content)

            if (temp is not None):
                a = temp.group(1)

                if (a[0] == 'a'):
                    delay += unit[1]
                else:
                    delay += int(a) * unit[1]

        return delay
