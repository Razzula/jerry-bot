from typing import Any
from discord.ext import commands

class TestCog(commands.Cog):
    """TODO"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, context: Any):
        """Pings the bot."""

        await context.send('Pong!')

def setup(bot):
    """TODO"""

    bot.add_cog(TestCog(bot))
