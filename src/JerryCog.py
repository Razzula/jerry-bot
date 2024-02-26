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

from BotHelper import BotUtils, Emotes, Emote
from CogTemplate import CustomCog

class JerryCog(CustomCog):
    """TODO"""

    def __init__(self, bot: commands.Bot, botUtils: BotUtils, gifs: dict[str, list[str]]):
        super().__init__('JerryCog', [
            ['bonk @', Emotes.BONK.value.emote],
            ['summon @', '🎺'],
        ])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_UTILS: Final[BotUtils] = botUtils

        self.GIFS: Final[dict[str, list[str]]] = gifs

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
