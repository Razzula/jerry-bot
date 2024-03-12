# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ, import-not-found
"""TODO ..."""
import random
import asyncio
from typing import Final, Any
import discord
from discord.ext import commands

from BotUtils import BotUtils, Emotes, Emote
from cogs.CogTemplate import CustomCog

class TagCog(CustomCog):
    """TODO"""

    def __init__(self, bot: commands.Bot, botUtils: BotUtils, gifs: dict[str, list[str]]):

        # self.DB_MANAGER: Final[DatabaseManager] = dbManager

        super().__init__('TagCog', [])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_UTILS: Final[BotUtils] = botUtils

        self.GIFS: Final[dict[str, list[str]]] = gifs

    @commands.Cog.listener()
    async def on_message(self, context: Any):
        """Reacts to messages sent to the bot."""

        message: str = context.content.lower()  # removes case sensitivity
        if (context.author == self.BOT.user):
            return
        if (message.startswith('http') or message.startswith('www.')):  # ignore links (GIFs)
            return
        
        # ensure user is 'It'
        tagRole: Any = discord.utils.get(context.guild.roles, name='It')
        if (tagRole is None):
            # TODO create role
            tagRole = await context.guild.create_role(name='It', color=discord.Colour.blurple())
        
        if (tagRole in context.author.roles):
            playerRole: Any = discord.utils.get(context.guild.roles, name='PlayingTag')
        
            # find target
            users = self.BOT_UTILS.extractMentionsFromMessage(message).get('users')
            user = None
            while (user is None):
                if (len(users) == 0):
                    return
                
                userID = random.choice(users)
                user = context.guild.get_member(int(userID))

                users.remove(userID)

                if (user is not None):
                    if ((playerRole is not None) and (playerRole not in user.roles)): # user is not playing tag
                        user = None

            # tagger is no loner It
            await context.author.remove_roles(tagRole)

            # tag target
            if (user.id == self.BOT.user.id):
                # bot has been tagged
                await user.add_roles(tagRole)

                await asyncio.sleep(random.randint(2, 6))
                await user.remove_roles(tagRole)

                while ((playerRole not in user.roles) or (user.id == self.BOT.user.id)):
                    user = random.choice(context.guild.members)

                await context.channel.send(f'<@{user.id}>')
                if (random.randint(0, 100) < 40 ): # 40%
                    await self.BOT_UTILS.sendGIF(context.channel, self.GIFS.get('tag'))

            # another user has been tagged
            await user.add_roles(tagRole)

    @commands.command(name='leaderboard', aliases=['l'])
    async def leaderboard(self, context):
        await context.channel.send(
            'Sorry, I forgot to pack the leaderboard when I moved out of my place at Amazon.. so `!l` no longer functions.'
        )