# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ, import-not-found
"""Main (not core) cog for the bot."""
import datetime
import random
import re
import time
import asyncio
from typing import Final, Any, Sequence
import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer

from src.BotUtils import BotUtils, Emotes, Emote
from src.DatabaseManager import DatabaseManager
from src.cogs.CogTemplate import CustomCog
from src.logger import Logger

class MinecraftCog(CustomCog):
    """
    Minecraft status cog.
    """

    def __init__(self, bot: commands.Bot, logger: Logger, botUtils: BotUtils):

        self.LOGGER: Final[Logger] = logger

        super().__init__('MinecraftCog', logger, [])

        self.BOT: Final[commands.Bot] = bot
        self.BOT_UTILS: Final[BotUtils] = botUtils

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.minecraftPoll.is_running():
            self.minecraftPoll.start()

    async def cog_unload(self):
        if self.minecraftPoll.is_running():
            self.minecraftPoll.cancel()

    @tasks.loop(seconds=10)
    async def minecraftPoll(self):
        """Poll the Minecraft server for status and update bot presence."""
        try:
            server = JavaServer.lookup("dnbeancraft.exaroton.me")
            status = await asyncio.to_thread(server.status)

            # print(status.players)
            if status.players.online and status.players.online > 0:
                players = status.players.online

                await self.BOT.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.playing,
                        name=f'Minecraft ({players} online)'
                    )
                )
                return

        except Exception as e:
            # print(e)
            self.LOGGER.error(f'Minecraft status failed: {e}')

        # Restore normal activity
        activity, activityType, _ = self.BOT_UTILS.getActivity()

        await self.BOT.change_presence(
            activity=discord.Activity(
                type=activityType,
                name=activity
            )
        )

    @minecraftPoll.before_loop
    async def beforeMinecraftPoll(self):
        await self.BOT.wait_until_ready()

    @minecraftPoll.error
    async def minecraftPollError(self, error):
        print("Minecraft loop crashed:", repr(error))
